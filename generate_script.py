import os
import json
import openai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from utils.scene_parser import parse_script
from utils.generate_images import (
    generate_scene_description,
    generate_image_from_prompt,
    save_image_from_base64,
    sanitize_prompt,
    sanitize_title
)
from utils.scene_sanitizer import sanitize_scene_description
from config import (
    HEADERS, SPREADSHEET_ID, RANGE_NAME,
    OPENAI_API_KEY, ELEVENLABS_API_KEY,
    VOICE_ID, MODEL_ID, MAX_RETRIES
)

def generate_script_and_assets():
    # === SETUP CLIENTS ===
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    tts_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    # === GOOGLE SHEETS AUTH ===
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # === READ FROM SHEET ===
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values or not values[0]:
        print("No data found in the specified range.")
        exit()

    data = {k.strip().lower(): v for k, v in zip(HEADERS, values[0])}

    video_title = data.get("topic", "")
    tone = data.get("tone", "neutral")
    style = data.get("style", "")
    audience = data.get("audience", "")
    voiceover = data.get("voiceover", "")
    music = data.get("background_music", "yes")

    # Use sanitized title for folder/file naming
    title = sanitize_title(video_title)


    # === BUILD PROMPT ===
    prompt = f"""
    You are an expert YouTube Shorts scriptwriter.

    Write a script for a short video that lasts **exactly 60 seconds or close (no less than 50s)**.

    - Topic: {title}
    - Tone: {tone}
    - Audience: {audience}
    - Voiceover?: {voiceover}
    - Style: {style}

    Use this structure:

    [INTRO: Brief sound or visual cue]

    [TEXT ON SCREEN:]
    [Voiceover] Strong hook to grab attention (1 sentence, ~8-12 words)

    Then write 5–7 scenes like this:

    [TEXT ON SCREEN: "1. TIP TITLE"]
    [Voiceover] Give a punchy but **slightly longer explanation or insight** (2–3 sentences, around 30 words max)

    Finally:

    [TEXT ON SCREEN: "CLOSING MESSAGE"]
    [Voiceover] Wrap up with a motivating, surprising, or reflective message (1–2 sentences, ~20 words)

    The entire voiceover should **add up to 120–140 words**, enough to fill 55–60 seconds.

    Only return the formatted script. No extra commentary.
    """

    # === GET SCRIPT FROM OPENAI ===
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a scriptwriter for YouTube Shorts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=700
    )

    script_text = response.choices[0].message.content.strip()
    scenes = parse_script(script_text)

    # === DEBUG PRINT ===
    print("\n🎬 Generated YouTube Short Script:\n")
    

    # === PREPARE FOLDERS ===
    audio_folder_path = os.path.join("audio", title)
    os.makedirs(audio_folder_path, exist_ok=True)

    # === GENERATE AUDIO + IMAGES PER SCENE ===
    for scene in scenes:
        scene_number = scene["scene_number"]
        text = scene["text_on_screen"]
        if "CLOSING" in scene["text_on_screen"].upper() or "OUTRO" in scene["text_on_screen"].upper() or "INTRO" in scene["text_on_screen"].upper():
            voiceover = scene["voiceover"]
        else:
            voiceover = f"{scene['text_on_screen']}: {scene['voiceover']}"


        # Audio
        audio = tts_client.text_to_speech.convert(
            text=voiceover,
            voice_id=VOICE_ID,
            model_id=MODEL_ID,
        )
        audio_filename = f"scene_{scene_number:02d}.mp3"
        audio_path = os.path.join(audio_folder_path, audio_filename)
        save(audio, audio_path)
        print(f"🎧 Scene {scene_number} audio saved to {audio_path}")

        text_filename = f"scene_{scene_number:02d}.txt"
        text_file_path = os.path.join(audio_folder_path, text_filename)

        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(voiceover)

        # Retry-safe Image Generation
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                desc = generate_scene_description(text, voiceover)
                sanitized = sanitize_scene_description(desc)
                print(f"🟢 Attempt {attempt}: Description sanitized.")

                image_data = generate_image_from_prompt(sanitized)
                save_image_from_base64(image_data, scene_number, video_title)
                print(f"🖼️ Scene {scene_number} image saved.")
                break

            except Exception as e:
                print(f"❌ Attempt {attempt} failed: {e}")
                if attempt == MAX_RETRIES:
                    print(f"🚫 Giving up on scene {scene_number} after {MAX_RETRIES} attempts.")


    metadata = {
        "title": title,
        "scenes": scenes,
        "music": music,
        "tone": tone,
        "video_title": video_title,
        "scene_count": len(scenes),
        "audio_folder": os.path.join("audio", title),
        "image_folder": os.path.join("assets", video_title),
        "output_path": os.path.join("output", "final_video.mp4")
    }

    with open("metadata.json", "w") as f:
        json.dump(metadata, f)

    print("✅ Metadata saved to metadata.json")
    return title



