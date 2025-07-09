import subprocess
import os

def create_final_video(
    audio_path="audio/voiceover.mp3",
    background_image_path="assets/background.png",
    output_path="output/final_video.mp4",
    resolution="1080x1920",
    duration=None  # Optional: force a video length in seconds
):
    # Make sure output folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Base FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg",
        "-loop", "1",                      # Loop the background image
        "-i", background_image_path,      # Input image
        "-i", audio_path,                 # Input audio
        "-c:v", "libx264",                # Video codec
        "-tune", "stillimage",            # Tune for still images
        "-c:a", "aac",                    # Audio codec
        "-b:a", "192k",                   # Audio bitrate
        "-pix_fmt", "yuv420p",            # Pixel format for compatibility
        "-shortest",                      # Ends video when audio ends
        "-y",                             # Overwrite output file
        "-vf", f"scale={resolution}"      # Set resolution
    ]

    # Optional: force a fixed video duration (e.g. 30s)
    if duration:
        ffmpeg_cmd += ["-t", str(duration)]

    ffmpeg_cmd.append(output_path)

    print(f"Running FFmpeg:\n{' '.join(ffmpeg_cmd)}")

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"✅ Video created successfully at: {output_path}")
    except subprocess.CalledProcessError as e:
        print("❌ Error creating video:", e)
