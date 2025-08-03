# config.py

import os
from dotenv import load_dotenv
load_dotenv()

# === GOOGLE SHEETS ===
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RANGE_NAME = "Prompts!A2:E2"

# === OPENAI & ELEVENLABS ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# === HEADERS USED FOR SHEET TO DICT MAPPING ===
HEADERS = ["Topic", "Tone", "Audience", "Voiceover?", "Style", "Background_music"]

# === VOICE CONFIGURATION ===
VOICE_ID = "pNInz6obpgDQGcFmaJgB"
MODEL_ID = "eleven_monolingual_v1"

# === SCENE GENERATION ===
MAX_RETRIES = 2
