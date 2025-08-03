import os
import re
import json
import openai
import random
from moviepy.editor import *
from moviepy.audio.fx.all import volumex
from moviepy.video.VideoClip import TextClip, ColorClip
from config import OPENAI_API_KEY
from moviepy.config import change_settings  # <- ADD THIS

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# Hardcode the path to ImageMagick if needed
change_settings({
    "IMAGEMAGICK_BINARY": "C:/Program Files/ImageMagick-7.1.2-Q16-HDRI/magick.exe"
})

def get_video_music_category(title, tone, full_script):
    prompt = f"""
You're helping assign background music for a short video.

Title: {title}
Tone: {tone}

Script:
{full_script}

Pick the best background music category that enhances the viewer's emotional experience.

Return only one category from:
- motivational
- calm
- educational
- dramatic
- inspirational
- mysterious
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().lower()


def select_music(category):
    print(f"{category} category chosen")
    music_dir = os.path.join("music", category)
    music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
    return os.path.join(music_dir, random.choice(music_files)) if music_files else None


def create_video_from_assets(title):
# === Load metadata ===
    with open("metadata.json", "r") as f:
        metadata = json.load(f)

    title = metadata["title"]
    tone = metadata["tone"]
    scenes = metadata["scenes"]
    scene_folder = f"assets/{title}"
    audio_folder = f"audio/{title}"
    output_path = f"output/{title}.mp4"
    background_music_enabled = metadata.get("music", "yes").lower() == "yes"

    os.makedirs("output", exist_ok=True)

    # === Sort helpers ===
    def extract_number(filename):
        match = re.search(r"(\d+)", filename)
        return int(match.group(1)) if match else -1

    image_files = sorted([f for f in os.listdir(scene_folder) if f.endswith(".png")], key=extract_number)
    audio_files = sorted([f for f in os.listdir(audio_folder) if f.endswith(".mp3")], key=extract_number)


    # === Combine full script and get music track
    full_script = "\n".join(scene["voiceover"] for scene in scenes)
    music_category = None
    music_path = None

    if background_music_enabled:
        music_category = get_video_music_category(title, tone, full_script)
        music_path = select_music(music_category)


    clips = []
    

    for i, (scene_data, img_file, aud_file) in enumerate(zip(scenes, image_files, audio_files), start=1):
        image_path = os.path.join(scene_folder, img_file)
        audio_path = os.path.join(audio_folder, aud_file)

        voiceover = AudioFileClip(audio_path)
        duration = voiceover.duration

        # Load voiceover and on-screen text from metadata
        
        voiceover_text = scene_data["voiceover"]
        text_on_screen = scene_data["text_on_screen"]

        # Use text_on_screen for caption (unless intro or closing)
        if i == 0 or "CLOSING" in text_on_screen.upper():
            caption_text = voiceover_text
        else:
            caption_text = text_on_screen

        image = ImageClip(image_path).set_duration(duration)

        caption_txt= TextClip(
        caption_text,
        fontsize=50,
        font="Arial-Bold",
        color="white",
        size=(image.w * 0.9, None),
        method="caption",
        align="center"
    ).set_duration(duration)  # lift slightly above bottom
        # Create a semi-transparent background box
        bg_height = caption_txt.h + 20
        bg = ColorClip(
            size=(caption_txt.w + 40, bg_height),
            color=(0, 0, 0)
        ).set_opacity(0.6).set_duration(duration)

        # Position the text and background together
        bg = bg.set_position(("center", "bottom"))
        caption_txt = caption_txt.set_position(("center", "bottom"))

        # Combine both
        caption = CompositeVideoClip([bg, caption_txt], size=image.size).set_duration(duration)


        scene = CompositeVideoClip([image, caption]).set_audio(voiceover)
        clips.append(scene.crossfadein(0.5))

    # === Add intro to fix playback bug
    first_audio = os.path.join(audio_folder, audio_files[0])
    intro = ColorClip(size=clips[0].size, color=(0, 0, 0), duration=1)
    intro = intro.set_audio(AudioFileClip(first_audio).fx(volumex, 0))  # silent

    # === Combine and export
    final = concatenate_videoclips([intro] + clips, method="compose")

    # === Add full-length background music once under the full video
    if music_path:
        bg_music_full = AudioFileClip(music_path).volumex(0.07)
        bg_music = (
            bg_music_full.set_duration(final.duration)
            .audio_fadein(1.5)     # 1.5 sec fade-in
            .audio_fadeout(2.0)    # 2 sec fade-out
        )
        full_audio = CompositeAudioClip([bg_music, final.audio])
        final = final.set_audio(full_audio)


    final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=30, preset="medium")


