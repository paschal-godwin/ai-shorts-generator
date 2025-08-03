import os
import io
import re
import base64
import openai
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import requests
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def sanitize_title(title):
    # Remove illegal filename characters
    return re.sub(r'[\\/*?:"<>|]', "", title)

def generate_scene_description(text_on_screen, voiceover):
    prompt = f"""You are a creative assistant for AI visuals.

Based on the following YouTube Shorts scene elements, write a single-sentence visual description of what should be shown:

Text on Screen: "{text_on_screen}"
Voiceover: "{voiceover}"

Rules:
- Don't make it too long. 1 or 2 sentences at most
- Don't repeat the text
- Don't mention "text" or "voice"
- Describe a vivid, vertical image that fits the scene
- Avoid logos, brands, watermarks
- Use cinematic, clean style

Only respond with the image description."""

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    return response.choices[0].message.content.strip()


def sanitize_prompt(prompt: str) -> str:
    """
    Replaces keywords that could trigger OpenAI's content filter with safer alternatives.
    """
    blocked_keywords = {
        "bedroom": "living room",
        "person": "someone",
        "people": "a group",
        "yoga mat": "exercise mat",
        "bed": "sofa",
        "bathroom": "home interior",
        "nude": "outfit",
        "underwear": "clothes",
        "sleeping": "resting",
    }

    for bad, good in blocked_keywords.items():
        prompt = prompt.replace(bad, good)

    return prompt



# 3. Function to generate image from scene description using DALL·E
def generate_image_from_prompt(prompt):
    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1792",  # Vertical for Shorts
        quality="standard",
        response_format="b64_json",
    )
    image_data = response.data[0].b64_json
    return image_data

def save_image_from_base64(image_data, scene_number, video_title):
    # Sanitize folder name from title
    clean_title = sanitize_title(video_title)

    # Build folder path
    folder_path = os.path.join("assets", clean_title)
    os.makedirs(folder_path, exist_ok=True)

    # Decode and save image
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))
    filename = f"scene_{scene_number:02d}.png"
    image_path = os.path.join(folder_path, filename)
    image.save(image_path)
    print(f"✅ Saved {filename} to {folder_path}")

