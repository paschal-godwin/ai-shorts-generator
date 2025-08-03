import os
import openai
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def is_potentially_unsafe(text: str) -> bool:
    """
    Use OpenAI moderation API to check if content is unsafe.
    Returns True if flagged (unsafe), False if safe.
    If moderation fails, assume unsafe.
    """
    try:
        response = client.moderations.create(input=text)
        flagged = response.results[0].flagged
        print("🛡️ Moderation check:", "⚠️ Unsafe" if flagged else "✅ Safe")
        return flagged
    except Exception as e:
        print(f"❌ Moderation check failed: {e}. Assuming unsafe.")
        return True  # Better to rewrite than to risk content block

def rewrite_scene_description(scene_description: str) -> str:
    """
    Rewrite scene description to be safe and DALL·E-friendly using GPT-4o.
    """
    system_prompt = (
        "You are a helpful assistant that rewrites scene descriptions to be safe "
        "for AI image generation. Avoid any mention or implication of violence, nudity, politics, "
        "or other sensitive topics. Keep the rewrite highly visual, creative, and aligned with the original intent."
    )
    
    user_prompt = f"""Original scene description:
{scene_description}

Rewrite it to be safe and suitable for image generation:"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Rewriting failed: {e}")
        return scene_description  # fallback: return original if rewriting fails

def sanitize_scene_description(description: str) -> str:
    print("🔍 Checking and rewriting description...")

    try:
        flagged = is_potentially_unsafe(description)
    except Exception as e:
        print(f"⚠️ Moderation failed: {e}. Assuming unsafe.")
        flagged = True

    if flagged:
        print("⚠️ Unsafe or unverified. Rewriting...")
    else:
        print("✅ Moderation passed. Rewriting anyway for extra safety...")

    safe_version = rewrite_scene_description(description)
    return safe_version