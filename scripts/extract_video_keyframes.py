#!/usr/bin/env python3
"""extract_video_keyframes.py — video keyframe extraction for cold retrieval.

First-version video strategy (方案 §4.4): 视频关键帧 + 一句说明 + 来源时间点,
NOT embedded video. Given a source video and target timecodes, extract one
high-quality frame per timecode plus a JSON manifest with provenance.

Requires ffmpeg: install it and make sure `ffmpeg` is on PATH, or set the
FFMPEG environment variable to the executable path.

Usage:
  python3 extract_video_keyframes.py demo.mp4 --timecodes 12.5,47 --out-dir ./frames
  python3 extract_video_keyframes.py demo.mp4 --scene-detect --max-frames 8 --out-dir ./frames
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _ffmpeg() -> str | None:
    import os
    env = os.environ.get("FFMPEG")
    if env and Path(env).is_file():
        return env
    return shutil.which("ffmpeg")


def _probe_duration(ffmpeg: str, video: Path) -> float | None:
    ffprobe = str(Path(ffmpeg).with_name("ffprobe")) if Path(ffmpeg).exists() else "ffprobe"
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video)],
            capture_output=True, text=True, timeout=60)
        return float(out.stdout.strip())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def _timecode_label(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(int(m), 60)
    return f"{h:02d}-{m:02d}-{s:05.2f}".replace(".", "p")


def extract_at(ffmpeg: str, video: Path, seconds: float, target: Path) -> bool:
    cmd = [ffmpeg, "-y", "-ss", f"{seconds:.3f}", "-i", str(video),
           "-frames:v", "1", "-q:v", "2", str(target)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return proc.returncode == 0 and target.is_file() and target.stat().st_size > 0


def scene_detect(ffmpeg: str, video: Path, threshold: float) -> list[float]:
    cmd = [ffmpeg, "-i", str(video), "-filter:v",
           f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    times = []
    for line in proc.stderr.splitlines():
        if "pts_time:" in line:
            try:
                frag = line.split("pts_time:", 1)[1]
                times.append(float(frag.split()[0]))
            except (ValueError, IndexError):
                continue
    return times


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", help="源视频文件")
    parser.add_argument("--timecodes", help="目标时间点（秒），逗号分隔，如 12.5,47")
    parser.add_argument("--scene-detect", action="store_true", help="按镜头切换自动抽帧")
    parser.add_argument("--scene-threshold", type=float, default=0.4)
    parser.add_argument("--max-frames", type=int, default=10)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--manifest", help="清单 JSON 路径（默认 <out-dir>/keyframes_manifest.json）")
    args = parser.parse_args()

    video = Path(args.video).resolve()
    if not video.is_file():
        print(f"video not found: {video}", file=sys.stderr)
        return 2
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        print("ffmpeg not found — install ffmpeg and put it on PATH, or set FFMPEG=<path-to-ffmpeg>",
              file=sys.stderr)
        return 3

    timecodes: list[float] = []
    if args.timecodes:
        try:
            timecodes = sorted({float(t) for t in args.timecodes.split(",") if t.strip()})
        except ValueError:
            print(f"invalid --timecodes: {args.timecodes}", file=sys.stderr)
            return 2
    if args.scene_detect:
        detected = scene_detect(ffmpeg, video, args.scene_threshold)
        timecodes = sorted(set(timecodes + detected))
    if not timecodes:
        print("no timecodes — pass --timecodes and/or --scene-detect", file=sys.stderr)
        return 2
    timecodes = timecodes[: args.max_frames]

    duration = _probe_duration(ffmpeg, video)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items, failed = [], []
    for tc in timecodes:
        if duration is not None and tc > duration:
            failed.append({"timecode": tc, "reason": f"beyond duration {duration:.1f}s"})
            continue
        name = f"frame_{_timecode_label(tc)}.jpg"
        if extract_at(ffmpeg, video, tc, out_dir / name):
            items.append({
                "file": name,
                "kind": "视频关键帧",
                "source_timecode": tc,
                "suggested_properties": {
                    "来源文件": video.name,
                    "来源位置": f"视频 {_timecode_label(tc).replace('-', ':').replace('p', '.')}",
                },
            })
        else:
            failed.append({"timecode": tc, "reason": "ffmpeg extraction failed"})

    result = {
        "version": 1,
        "source_file": str(video),
        "duration_seconds": duration,
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "items": items,
        "failed": failed,
    }
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "keyframes_manifest.json"
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"kept": len(items), "failed": len(failed),
                      "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0 if items else 1


if __name__ == "__main__":
    sys.exit(main())
