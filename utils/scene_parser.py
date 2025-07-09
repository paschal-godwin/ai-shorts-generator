import re

def parse_script(script_text):
    pattern = r'\[TEXT ON SCREEN:\s*"(.*?)"\]\s*\[Voiceover\]\s*(.*?)(?=\[TEXT ON SCREEN:|\[OUTRO:|\Z)'
    matches = re.findall(pattern, script_text, re.DOTALL)

    scenes = []
    for i, (text, voiceover) in enumerate(matches):
        scenes.append({
            "scene_number": i + 1,
            "text_on_screen": text.strip(),
            "voiceover": voiceover.strip()
        })

    return scenes