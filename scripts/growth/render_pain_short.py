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


def write_preview_frames(video_path: Path, out_dir: Path, slug: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamps = [0.9, 2.4, 4.2]
    for idx, ts in enumerate(stamps, start=1):
        out_path = out_dir / f"{slug}-preview-{idx:02d}.png"
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


def build_alert_fatigue_filter(texts: dict[str, Path], width: int, height: int) -> str:
    mono = "/System/Library/Fonts/SFNSMono.ttf"
    sans = "/System/Library/Fonts/HelveticaNeue.ttc"
    alert_boxes = []
    alert_y = 260
    for idx in range(5):
        y = alert_y + idx * 92
        alpha = 0.92 if idx < 4 else 0.98
        color = "0x131714" if idx < 4 else "0x0f1410"
        alert_boxes.append(
            f"drawbox=x=88:y={y}:w=904:h=70:color={color}@{alpha}:t=fill:enable='between(t,0.35,2.15)'"
        )
        alert_boxes.append(
            f"drawbox=x=88:y={y}:w=904:h=70:color=0x1e2520@1.0:t=1:enable='between(t,0.35,2.15)'"
        )
    noisy_lines = []
    noisy_copy = [
        ("ALERT // BTC SPIKE", 280),
        ("ALERT // FED MARKET", 372),
        ("ALERT // BREAKING MOVE", 464),
        ("ALERT // SAME THING AGAIN", 556),
    ]
    for label, y in noisy_copy:
        noisy_lines.append(
            f"drawtext=fontfile={mono}:text='{label}':fontsize=24:fontcolor=0x8fa88f:x=118:y={y}:enable='between(t,0.4,1.9)'"
        )

    parts = [
        "[0:v]format=rgba",
        "eq=contrast=1.04:brightness=-0.02:saturation=0.95",
        "noise=alls=7:allf=t+u",
        "drawbox=x='mod(t*260,1600)-420':y=0:w=220:h=ih:color=0x00ff88@0.05:t=fill",
        f"drawbox=x=40:y=88:w={width-80}:h={height-176}:color=0x131714@0.97:t=fill",
        f"drawbox=x=40:y=88:w={width-80}:h={height-176}:color=0x1e2520@1.0:t=2",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['title'])}':expansion=none:fontsize=22:fontcolor=0x8fa88f:x=82:y=148:enable='between(t,0,5)'",
        *alert_boxes,
        *noisy_lines,
        f"drawtext=fontfile={mono}:text='TOO MANY ALERTS = NO TRUST':fontsize=34:fontcolor=0xe8ede9:x=118:y=740:enable='between(t,1.6,2.7)'",
        f"drawbox=x=88:y=900:w=904:h=260:color=0x0f1410@0.99:t=fill:enable='between(t,2.55,4.2)'",
        f"drawbox=x=88:y=900:w=904:h=260:color=0x00ff88@0.24:t=2:enable='between(t,2.55,4.2)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['threshold'])}':expansion=none:fontsize=38:fontcolor=0x00ff88:x=124:y=972:enable='between(t,2.7,3.6)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['dedup'])}':expansion=none:fontsize=28:fontcolor=0xe8ede9:x=124:y=1036:enable='between(t,2.8,3.8)'",
        f"drawtext=fontfile={sans}:textfile='{esc(texts['question'])}':expansion=none:fontsize=32:fontcolor=0xe8ede9:x=124:y=1102:enable='between(t,2.9,4.0)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['delta'])}':expansion=none:fontsize=25:fontcolor=0x8fa88f:x=124:y=1150:enable='between(t,3.0,4.0)'",
        f"drawbox=x=88:y=1330:w=904:h=180:color=0x101511@0.98:t=fill:enable='between(t,4.05,5.0)'",
        f"drawbox=x=88:y=1330:w=904:h=180:color=0x1e2520@1.0:t=2:enable='between(t,4.05,5.0)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['cta'])}':expansion=none:fontsize=40:fontcolor=0x00ff88:x=(w-text_w)/2:y=1390:enable='between(t,4.12,5.0)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['stamp'])}':expansion=none:fontsize=20:fontcolor=0x8fa88f:x=(w-text_w)/2:y=1452:enable='between(t,4.12,5.0)'",
        "drawbox=x=40:y='if(between(t,1.45,1.53)+between(t,2.42,2.48), 0, -200)':w=1000:h=18:color=0xffffff@0.07:t=fill",
        "vignette=PI/6",
    ]
    return ",".join(parts) + "[v]"


def build_dashboard_overload_filter(texts: dict[str, Path], width: int, height: int) -> str:
    mono = "/System/Library/Fonts/SFNSMono.ttf"
    sans = "/System/Library/Fonts/HelveticaNeue.ttc"
    panels = []
    positions = [
        (92, 270, 280, 180),
        (404, 270, 280, 180),
        (716, 270, 276, 180),
        (92, 486, 280, 180),
        (404, 486, 280, 180),
        (716, 486, 276, 180),
    ]
    for x, y, w, h in positions:
        panels.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0x101511@0.95:t=fill:enable='between(t,0.25,1.7)'")
        panels.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0x1e2520@1.0:t=1:enable='between(t,0.25,1.7)'")
    panel_copy = [
        ("WIDGET 01", 120, 320),
        ("WIDGET 02", 432, 320),
        ("WIDGET 03", 744, 320),
        ("CHARTS", 120, 536),
        ("FILTERS", 432, 536),
        ("NOISE", 744, 536),
    ]
    panel_labels = [
        f"drawtext=fontfile={mono}:text='{label}':fontsize=22:fontcolor=0x6b7a6e:x={x}:y={y}:enable='between(t,0.35,1.55)'"
        for label, x, y in panel_copy
    ]

    parts = [
        "[0:v]format=rgba",
        "eq=contrast=1.05:brightness=-0.02:saturation=0.94",
        "noise=alls=5:allf=t+u",
        "drawbox=x='mod(t*200,1500)-320':y=0:w=240:h=ih:color=0x00ff88@0.05:t=fill",
        f"drawbox=x=40:y=88:w={width-80}:h={height-176}:color=0x131714@0.97:t=fill",
        f"drawbox=x=40:y=88:w={width-80}:h={height-176}:color=0x1e2520@1.0:t=2",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['title'])}':expansion=none:fontsize=22:fontcolor=0x8fa88f:x=82:y=148:enable='between(t,0,5)'",
        *panels,
        *panel_labels,
        f"drawtext=fontfile={mono}:textfile='{esc(texts['what'])}':expansion=none:fontsize=44:fontcolor=0xe8ede9:x=120:y=800:enable='between(t,1.25,2.1)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['how'])}':expansion=none:fontsize=44:fontcolor=0x00ff88:x=120:y=864:enable='between(t,2.0,2.85)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['matter'])}':expansion=none:fontsize=44:fontcolor=0xe8ede9:x=120:y=928:enable='between(t,2.7,3.6)'",
        f"drawbox=x=88:y=1080:w=904:h=300:color=0x0f1410@0.99:t=fill:enable='between(t,3.2,4.4)'",
        f"drawbox=x=88:y=1080:w=904:h=300:color=0x00ff88@0.24:t=2:enable='between(t,3.2,4.4)'",
        f"drawtext=fontfile={sans}:textfile='{esc(texts['question'])}':expansion=none:fontsize=32:fontcolor=0xe8ede9:x=124:y=1150:enable='between(t,3.3,4.3)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['price'])}':expansion=none:fontsize=32:fontcolor=0xe8ede9:x=124:y=1216:enable='between(t,3.35,4.35)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['delta'])}':expansion=none:fontsize=25:fontcolor=0x00ff88:x=124:y=1266:enable='between(t,3.4,4.35)'",
        f"drawbox=x=88:y=1450:w=904:h=144:color=0x101511@0.98:t=fill:enable='between(t,4.15,5.0)'",
        f"drawbox=x=88:y=1450:w=904:h=144:color=0x1e2520@1.0:t=2:enable='between(t,4.15,5.0)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['cta'])}':expansion=none:fontsize=38:fontcolor=0x00ff88:x=(w-text_w)/2:y=1496:enable='between(t,4.2,5.0)'",
        f"drawtext=fontfile={mono}:textfile='{esc(texts['stamp'])}':expansion=none:fontsize=20:fontcolor=0x8fa88f:x=(w-text_w)/2:y=1548:enable='between(t,4.2,5.0)'",
        "drawbox=x=40:y='if(between(t,1.05,1.10)+between(t,2.95,3.00), 0, -200)':w=1000:h=20:color=0xffffff@0.07:t=fill",
        "vignette=PI/6",
    ]
    return ",".join(parts) + "[v]"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render branded 5s pain-first shorts from live movers")
    parser.add_argument("--theme", required=True, choices=["alert-fatigue", "dashboard-overload"])
    parser.add_argument("--output")
    parser.add_argument("--preview-dir", default="assets/social/out")
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=5.0)
    args = parser.parse_args()

    default_outputs = {
        "alert-fatigue": "assets/social/out/alert-fatigue-5s.mp4",
        "dashboard-overload": "assets/social/out/dashboard-overload-5s.mp4",
    }
    output = args.output or default_outputs[args.theme]

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
    delta_line = f"{fmt_delta(mover.get('delta_yes'))}  //  {fmt_window(mover.get('prev_bucket'), mover.get('last_bucket'))}"
    live_stamp = f"LIVE DB // UTC {datetime.now(timezone.utc).strftime('%H:%M:%S')}"

    out_path = Path(output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="painshort_") as tmp:
        tmp_path = Path(tmp)
        texts = {
            "title": tmp_path / "title.txt",
            "question": tmp_path / "question.txt",
            "price": tmp_path / "price.txt",
            "delta": tmp_path / "delta.txt",
            "cta": tmp_path / "cta.txt",
            "stamp": tmp_path / "stamp.txt",
            "threshold": tmp_path / "threshold.txt",
            "dedup": tmp_path / "dedup.txt",
            "what": tmp_path / "what.txt",
            "how": tmp_path / "how.txt",
            "matter": tmp_path / "matter.txt",
        }
        texts["question"].write_text(question, encoding="utf-8")
        texts["price"].write_text(price_line, encoding="utf-8")
        texts["delta"].write_text(delta_line, encoding="utf-8")
        texts["cta"].write_text("@POLYMARKET_PULSE_BOT", encoding="utf-8")
        texts["stamp"].write_text(live_stamp, encoding="utf-8")

        if args.theme == "alert-fatigue":
            texts["title"].write_text("POLYMARKET PULSE // ALERT FATIGUE", encoding="utf-8")
            texts["threshold"].write_text("THRESHOLD + DEDUP", encoding="utf-8")
            texts["dedup"].write_text("FEWER PINGS. CLEARER DELTAS. MORE TRUST.", encoding="utf-8")
            vf = build_alert_fatigue_filter(texts, args.width, args.height)
            slug = "alert-fatigue"
        else:
            texts["title"].write_text("POLYMARKET PULSE // DASHBOARD OVERLOAD", encoding="utf-8")
            texts["what"].write_text("WHAT MOVED?", encoding="utf-8")
            texts["how"].write_text("BY HOW MUCH?", encoding="utf-8")
            texts["matter"].write_text("DOES IT MATTER NOW?", encoding="utf-8")
            vf = build_dashboard_overload_filter(texts, args.width, args.height)
            slug = "dashboard-overload"

        af = (
            "highpass=f=110,"
            "lowpass=f=2200,"
            "volume=0.062,"
            "tremolo=f=6.5:d=0.52,"
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
            f"sine=frequency=132:sample_rate=44100:duration={args.duration}",
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

    write_preview_frames(out_path, Path(args.preview_dir).resolve(), slug)
    print(str(out_path))


if __name__ == "__main__":
    main()
