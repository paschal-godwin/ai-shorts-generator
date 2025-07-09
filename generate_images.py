import os
import openai
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import requests
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_scene_description(text_on_screen, voiceover):
    prompt = f"""You are a creative assistant for AI visuals.

Based on the following YouTube Shorts scene elements, write a single-sentence visual description of what should be shown:

Text on Screen: "{text_on_screen}"
Voiceover: "{voiceover}"

Rules:
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

# 3. Function to generate image from scene description using DALL·E
def generate_image_from_prompt(prompt, output_path):
    response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1792",  # Vertical for Shorts
        quality="standard",
        response_format="b64_json",
    )
    image_data = response.data[0].b64_json
    image = Image.open(
        io.BytesIO(base64.b64decode(image_data))
    )
    image.save(output_path)

