import json
from generate_script import generate_script_and_assets
from create_video import create_video_from_assets




if __name__ == "__main__":
    title = generate_script_and_assets()
    create_video_from_assets(title)
