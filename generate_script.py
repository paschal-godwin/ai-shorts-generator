import os
import openai
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from utils.scene_parser import parse_script
from create_video import create_final_video
from generate_images import generate_scene_description, generate_image_from_prompt
from dotenv import load_dotenv

load_dotenv()


# === CONFIG ===
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID') 
RANGE_NAME = 'Prompts!A2:E2'
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tts_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY")) 


# === SETUP GOOGLE SHEETS AUTH ===
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

# === READ FROM GOOGLE SHEET ===
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                            range=RANGE_NAME).execute()
values = result.get('values', [])

if not values or not values[0]:
    print("No data found in the specified range.")
    exit()

# === FORMAT PROMPT ===
headers = ['Topic', 'Tone', 'Audience', 'Voiceover?', 'Style']
data = dict(zip(headers, values[0]))


prompt = f"""
You are an expert YouTube Shorts scriptwriter.

Write a 60-second video script based on the following:
- Topic: {data['Topic']}
- Tone: {data['Tone']}
- Audience: {data['Audience']}
- Voiceover?: {data['Voiceover?']}
- Style: {data['Style']}

Use this exact structure — no deviation:

[INTRO: Brief intro music or effect]

[TEXT ON SCREEN: "MAIN TITLE OR HOOK"]
[Voiceover] Intro hook that grabs attention and speaks directly to the audience.

[TEXT ON SCREEN: "1. TIP TITLE"]
[Voiceover] Tip 1 in a short, energetic sentence.

[TEXT ON SCREEN: "2. TIP TITLE"]
[Voiceover] Tip 2 in a short, energetic sentence.

[TEXT ON SCREEN: "3. TIP TITLE"]
[Voiceover] Tip 3 in a short, energetic sentence.

[TEXT ON SCREEN: "4. TIP TITLE"]
[Voiceover] Tip 4 in a short, energetic sentence.

[TEXT ON SCREEN: "5. TIP TITLE"]
[Voiceover] Tip 5 in a short, energetic sentence.

[TEXT ON SCREEN: "6. TIP TITLE"]
[Voiceover] Tip 6 in a short, energetic sentence.

[OUTRO: Music fades out]

[TEXT ON SCREEN: "YOU'VE GOT THIS!"]
[Voiceover] A motivational outro to end the video.

Keep each voiceover punchy, conversational, and under 10 seconds. Respond with only the script and no extra commentary. Format matters — follow it exactly.
"""

# === CALL OPENAI ===
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a scriptwriter for YouTube Shorts."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.8,
    max_tokens=300
)

script_text = response.choices[0].message.content.strip().strip()

scenes = parse_script(script_text)
 

# === OUTPUT ===
print("\n🎬 Generated YouTube Short Script:\n")
print(script_text)

voices = tts_client.voices.get_all()  # unpack the list

script_text = "\n".join(
    f"{scene['text_on_screen']}\n{scene['voiceover']}"
    for scene in scenes
)


audio = tts_client.text_to_speech.convert(
    text=script_text,
    voice_id = "pNInz6obpgDQGcFmaJgB", # Changeable: "Adam", "Antoni", "Elli", "Josh", etc.
    model_id="eleven_monolingual_v1",
)

# Save as voiceover.mp3
save(audio, "voiceover.mp3")
print("🎧 Voiceover saved as voiceover.mp3")

#Making Images

print("Generating Images Now......")

SCENES_FOLDER = "assets/scenes"

# Ensure assets/scenes folder exists
os.makedirs(SCENES_FOLDER, exist_ok=True)

# 4. Loop through scenes
for scene in scenes:
    scene_number = scene["scene_number"]
    text = scene["text_on_screen"]
    voice = scene["voiceover"]

    print(f"Generating scene {scene_number}...")

    # a. Get scene description
    description = generate_scene_description(text, voice)
    print(f"Scene {scene_number} description: {description}")

    # b. Generate and save image
    output_path = f"scene_images/scene_{scene_number}.png"
    generate_image_from_prompt(description, output_path)

    print(f"Saved image: {output_path}")


"""create_final_video(
    audio_path="audio/voiceover.mp3",
    background_image_path="assets/background.png",
    output_path="output/final_video.mp4"
)"""


