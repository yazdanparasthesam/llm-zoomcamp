#!/usr/bin/env python3
"""
Regenerates the multimodal audio briefings with gTTS (Google TTS).
Requires network access.  Usage:

    pip install gtts
    python3 data/generate_audio.py

If gTTS / network is unavailable, the app gracefully hides the audio
players and still shows the transcripts (data/transcripts.txt).
"""
import os
import re

OUT_DIR = os.path.join(os.path.dirname(__file__), "audio")
FILES = {
    "paris_vs_lyon_briefing.mp3": "Paris versus Lyon for a food-focused city break",
    "barcelona_beach_city_break.mp3": "Barcelona beach and city break",
    "eastern_europe_value_briefing.mp3": "Best-value Eastern Europe",
}


def extract_blocks(transcript_path):
    text = open(transcript_path, encoding="utf-8").read()
    blocks = {}
    for m in re.finditer(r"\d\) data/audio/([\w.]+)\n-+\n\"(.*?)\"", text, re.S):
        fname, body = m.group(1), m.group(2).replace("\n", " ").strip()
        blocks[fname] = body
    return blocks


def main():
    try:
        from gtts import gTTS
    except ImportError:
        print("gTTS not installed: pip install gtts")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    src = os.path.join(os.path.dirname(__file__), "transcripts.txt")
    blocks = extract_blocks(src)
    for fname in FILES:
        if fname not in blocks:
            print(f"!! no transcript section for {fname}, skipping")
            continue
        out = os.path.join(OUT_DIR, fname)
        gTTS(blocks[fname], lang="en").save(out)
        print(f"written {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
