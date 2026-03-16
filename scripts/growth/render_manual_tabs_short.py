#!/usr/bin/env python3
import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg.rows import dict_row

SQL_TOP_MOVER = """
select market_id, question, delta_yes, yes_mid_prev, yes_mid_now, prev_bucket, last_bucket
from public.top_movers_latest
where delta_yes is not null
order by abs(delta_yes) desc nulls last
limit 1;
"""


def fmt_pct(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:.1f}%"


def fmt_delta(v: object) -> str:
    if v is None:
        return "n/a"
    return f"{float(v) * 100:+.1f}pp"


def fmt_window(prev_bucket, last_bucket) -> str:
    if prev_bucket is None or last_bucket is None:
        return "live"
    minutes = int((last_bucket - prev_bucket).total_seconds() // 60)
    return f"{max(minutes, 1)}m"


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def esc(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


def write_preview_frames(video_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamps = [0.8, 2.4, 4.2]
    for idx, ts in enumerate(stamps, start=1):
        out_path = out_dir / f"manual-tabs-preview-{idx:02d}.png"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(ts),
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                str(out_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a 5s branded short for the manual tabs pain post")
    parser.add_argument("--output", default="assets/social/out/manual-tabs-pain-5s.mp4")
    parser.add_argument("--preview-dir", default="assets/social/out")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()

    pg_conn = os.environ.get("PG_CONN", "")
    if not pg_conn:
        raise SystemExit("PG_CONN is required")

    with psycopg.connect(pg_conn, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(SQL_TOP_MOVER)
            mover = cur.fetchone()
    if not mover:
        raise SystemExit("No mover found in public.top_movers_latest")

    question = truncate((mover.get("question") or "n/a").upper(), 44)
    price_line = f"{fmt_pct(mover.get('yes_mid_prev'))} -> {fmt_pct(mover.get('yes_mid_now'))}"
    delta_line = f"DELTA {fmt_delta(mover.get('delta_yes'))}  //  {fmt_window(mover.get('prev_bucket'), mover.get('last_bucket'))}"
    live_stamp = f"LIVE DB // UTC {datetime.now(timezone.utc).strftime('%H:%M:%S')}"

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="manualtabs_") as tmp:
        tmp_path = Path(tmp)
        texts = {
            "title": tmp_path / "title.txt",
            "tabs": tmp_path / "tabs.txt",
            "move": tmp_path / "move.txt",
            "question": tmp_path / "question.txt",
            "price": tmp_path / "price.txt",
            "delta": tmp_path / "delta.txt",
            "manual": tmp_path / "manual.txt",
            "cta": tmp_path / "cta.txt",
            "stamp": tmp_path / "stamp.txt",
            "lag": tmp_path / "lag.txt",
        }
        texts["title"].write_text("POLYMARKET PULSE", encoding="utf-8")
        texts["tabs"].write_text("12 TABS OPEN", encoding="utf-8")
        texts["move"].write_text("MOVE ALREADY HAPPENED", encoding="utf-8")
        texts["question"].write_text(question, encoding="utf-8")
        texts["price"].write_text(price_line, encoding="utf-8")
        texts["delta"].write_text(delta_line, encoding="utf-8")
        texts["manual"].write_text("WORKFLOW TOO MANUAL", encoding="utf-8")
        texts["cta"].write_text("@POLYMARKET_PULSE_BOT", encoding="utf-8")
        texts["stamp"].write_text(live_stamp, encoding="utf-8")
        texts["lag"].write_text("SCANNING TABS IS WHERE YOU LOSE THE MOVE", encoding="utf-8")

        mono = "/System/Library/Fonts/SFNSMono.ttf"
        sans = "/System/Library/Fonts/HelveticaNeue.ttc"

        # 12 fake browser tabs in the top strip.
        tab_boxes = []
        start_x = 48
        tab_w = 79
        gap = 6
        for i in range(12):
            x = start_x + i * (tab_w + gap)
            color = "0x1e2520@0.96"
            if i == 7:
                color = "0x00ff88@0.20"
            tab_boxes.append(f"drawbox=x={x}:y=90:w={tab_w}:h=38:color={color}:t=fill")
            tab_boxes.append(f"drawbox=x={x}:y=90:w={tab_w}:h=38:color=0x2a332b@1.0:t=1")

        vf_parts = [
            "[0:v]format=rgba",
            "eq=contrast=1.05:brightness=-0.02:saturation=0.98",
            "noise=alls=6:allf=t+u",
            "drawbox=x='mod(t*220,1500)-360':y=0:w=300:h=ih:color=0x00ff88@0.06:t=fill",
            "drawbox=x=34:y=74:w=1012:h=1740:color=0x131714@0.96:t=fill",
            "drawbox=x=34:y=74:w=1012:h=1740:color=0x1e2520@1.0:t=2",
            "drawbox=x=34:y=74:w=1012:h=66:color=0x0f1410@1.0:t=fill",
            *tab_boxes,
            f"drawtext=fontfile={mono}:textfile='{esc(texts['title'])}':expansion=none:fontsize=20:fontcolor=0x8fa88f:x=72:y=160:enable='between(t,0,5)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['tabs'])}':expansion=none:fontsize=44:fontcolor=0xe8ede9:x=72:y=240:enable='between(t,0,1.2)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['lag'])}':expansion=none:fontsize=20:fontcolor=0x6b7a6e:x=72:y=308:enable='between(t,0.1,1.4)'",
            "drawbox=x=72:y=404:w=936:h=364:color=0x101511@0.96:t=fill:enable='between(t,1.0,3.0)'",
            "drawbox=x=72:y=404:w=936:h=364:color=0x1e2520@1.0:t=2:enable='between(t,1.0,3.0)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['move'])}':expansion=none:fontsize=36:fontcolor=0xff6b73:x=106:y=454:enable='between(t,1.1,2.4)'",
            f"drawtext=fontfile={sans}:textfile='{esc(texts['question'])}':expansion=none:fontsize=38:fontcolor=0xe8ede9:x=106:y=540:enable='between(t,1.2,2.8)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['price'])}':expansion=none:fontsize=34:fontcolor=0xe8ede9:x=106:y=624:enable='between(t,1.3,2.9)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['delta'])}':expansion=none:fontsize=26:fontcolor=0x00ff88:x=106:y=680:enable='between(t,1.4,2.9)'",
            "drawbox=x=72:y=862:w=936:h=280:color=0x0f1410@0.98:t=fill:enable='between(t,2.7,4.0)'",
            "drawbox=x=72:y=862:w=936:h=280:color=0x00ff88@0.28:t=2:enable='between(t,2.7,4.0)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['manual'])}':expansion=none:fontsize=44:fontcolor=0x00ff88:x=104:y=954:enable='between(t,2.8,4.0)'",
            "drawbox=x=72:y=1278:w=936:h=212:color=0x101511@0.98:t=fill:enable='between(t,4.0,5.0)'",
            "drawbox=x=72:y=1278:w=936:h=212:color=0x1e2520@1.0:t=2:enable='between(t,4.0,5.0)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['cta'])}':expansion=none:fontsize=42:fontcolor=0x00ff88:x=(w-text_w)/2:y=1352:enable='between(t,4.05,5.0)'",
            f"drawtext=fontfile={mono}:textfile='{esc(texts['stamp'])}':expansion=none:fontsize=20:fontcolor=0x8fa88f:x=(w-text_w)/2:y=1422:enable='between(t,4.05,5.0)'",
            "drawbox=x='mod(t*600,1800)-500':y=0:w=140:h=ih:color=0xffffff@0.035:t=fill",
            "drawbox=x=34:y='if(between(t,1.05,1.15)+between(t,2.9,3.02), 0, -200)':w=1012:h=24:color=0xffffff@0.08:t=fill",
            "vignette=PI/6",
        ]
        vf = ",".join(vf_parts) + "[v]"

        af = (
            "highpass=f=110,"
            "lowpass=f=2200,"
            "volume=0.065,"
            "tremolo=f=7:d=0.55,"
            "afade=t=out:st=4.65:d=0.25,"
            "loudnorm=I=-17:TP=-1.5:LRA=7"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#0d0f0e:s={args.width}x{args.height}:r={args.fps}:d={args.duration}",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency=120:sample_rate=44100:duration={args.duration}",
            "-filter_complex",
            f"{vf};[1:a]{af}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-r",
            str(args.fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "19",
            "-preset",
            "medium",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(out_path),
        ]
        subprocess.run(cmd, check=True)

    write_preview_frames(out_path, Path(args.preview_dir).resolve())
    print(str(out_path))


if __name__ == "__main__":
    main()
