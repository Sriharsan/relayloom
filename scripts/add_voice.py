"""Put your own voice on the demo video.

Usage:
    python scripts/add_voice.py VOICE_FILE [--video docs/video/relayloom-demo-captioned.mp4] [--out docs/video/relayloom-demo-final.mp4]

VOICE_FILE is your recording of the narration in docs/VIDEO_SCRIPT.md (m4a, mp3, wav, any format). The picture keeps its captions. If your
voice runs longer than the picture, the last frame is held so nothing is cut off. If it is shorter, the picture ends with your voice.
The result must stay at or under three minutes, and the script tells you if it does not.
"""
import glob
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def tool(name):
    found = shutil.which(name) or (glob.glob(str(Path.home() / f"AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin/{name}.exe")) or [None])[0]
    if not found:
        sys.exit(f"{name} was not found. Install ffmpeg (winget install Gyan.FFmpeg) and run this again.")
    return found


def seconds(path, ffprobe):
    out = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        print(__doc__)
        sys.exit(2)
    voice = Path(args[0])
    video = Path(args[args.index("--video") + 1]) if "--video" in args else ROOT / "docs" / "video" / "relayloom-demo-captioned.mp4"
    out = Path(args[args.index("--out") + 1]) if "--out" in args else video.with_name("relayloom-demo-final.mp4")
    ffmpeg, ffprobe = tool("ffmpeg"), tool("ffprobe")
    v, a = seconds(video, ffprobe), seconds(voice, ffprobe)
    extra = max(0.0, a - v)
    graph = f"[0:v]tpad=stop_mode=clone:stop_duration={extra + 0.5:.2f}[v]" if extra else "[0:v]null[v]"
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(video), "-i", str(voice), "-filter_complex", graph, "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    total = seconds(out, ffprobe)
    print(f"wrote {out} ({total:.1f} s, picture {v:.1f} s, voice {a:.1f} s)")
    if total > 180:
        print("WARNING: longer than three minutes. Tighten the narration or speak a little faster, then run this again.")


if __name__ == "__main__":
    main()
