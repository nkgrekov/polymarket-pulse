#!/usr/bin/env python3
import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import psycopg
from psycopg.rows import dict_row

SQL_TOP_MOVERS = """
select market_id, question, delta_yes, yes_mid_prev, yes_mid_now, prev_bucket, last_bucket
from public.top_movers_latest
where delta_yes is not null
order by abs(delta_yes) desc nulls last
limit 3;
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


def q_escape_for_filter(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a 5s branded cursed short from live movers")
    parser.add_argument("--output", default="assets/social/out/shitpost-live-5s.mp4")
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
            cur.execute(SQL_TOP_MOVERS)
            movers = cur.fetchall()
    if not movers:
        raise SystemExit("No movers found in public.top_movers_latest")

    while len(movers) < 3:
        movers.append(movers[-1])

    m1, m2, m3 = movers[:3]
    title = "POLYMARKET PULSE // LIVE GLITCH"
    subtitle = f"SCOPE {fmt_window(m1.get('prev_bucket'), m1.get('last_bucket'))} // SIGNAL > NOISE"
    line1 = truncate(
        f"1) {m1.get('question') or 'n/a'} | {fmt_pct(m1.get('yes_mid_prev'))}->{fmt_pct(m1.get('yes_mid_now'))} | {fmt_delta(m1.get('delta_yes'))}",
        84,
    )
    line2 = truncate(
        f"2) {m2.get('question') or 'n/a'} | {fmt_pct(m2.get('yes_mid_prev'))}->{fmt_pct(m2.get('yes_mid_now'))} | {fmt_delta(m2.get('delta_yes'))}",
        84,
    )
    line3 = truncate(
        f"3) {m3.get('question') or 'n/a'} | {fmt_pct(m3.get('yes_mid_prev'))}->{fmt_pct(m3.get('yes_mid_now'))} | {fmt_delta(m3.get('delta_yes'))}",
        84,
    )
    cta = "TRACK FULL FEED -> @POLYMARKET_PULSE_BOT"
    pulse_stamp = f"UTC {datetime.now(timezone.utc).strftime('%H:%M:%S')} | LIVE DB"

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(prefix="ppmeme_") as tmp:
        tmp_path = Path(tmp)
        files = {
            "title": tmp_path / "title.txt",
            "subtitle": tmp_path / "subtitle.txt",
            "line1": tmp_path / "line1.txt",
            "line2": tmp_path / "line2.txt",
            "line3": tmp_path / "line3.txt",
            "cta": tmp_path / "cta.txt",
            "stamp": tmp_path / "stamp.txt",
        }
        files["title"].write_text(title, encoding="utf-8")
        files["subtitle"].write_text(subtitle, encoding="utf-8")
        files["line1"].write_text(line1, encoding="utf-8")
        files["line2"].write_text(line2, encoding="utf-8")
        files["line3"].write_text(line3, encoding="utf-8")
        files["cta"].write_text(cta, encoding="utf-8")
        files["stamp"].write_text(pulse_stamp, encoding="utf-8")

        mono = "/System/Library/Fonts/SFNSMono.ttf"
        sans = "/System/Library/Fonts/HelveticaNeue.ttc"

        vf = (
            f"[0:v]format=rgba,"
            "eq=contrast=1.10:saturation=1.08:brightness=-0.04,"
            "noise=alls=8:allf=t+u,"
            "drawbox=x='mod(t*280,1500)-280':y=0:w=260:h=ih:color=0x00ff88@0.09:t=fill,"
            "drawbox=x=40:y=120:w=1000:h=1680:color=0x131714@0.94:t=fill,"
            "drawbox=x=40:y=120:w=1000:h=1680:color=0x1e2520@1.0:t=2,"
            "drawbox=x=40:y=1540:w=1000:h=140:color=0x101511@0.95:t=fill,"
            f"drawtext=fontfile={mono}:textfile='{q_escape_for_filter(files['title'])}':expansion=none:fontsize=48:fontcolor=0xe8ede9:x=70:y=170:enable='between(t,0,1.2)',"
            f"drawtext=fontfile={mono}:textfile='{q_escape_for_filter(files['subtitle'])}':expansion=none:fontsize=24:fontcolor=0x8fa88f:x=70:y=236:enable='between(t,0,1.8)',"
            f"drawtext=fontfile={sans}:textfile='{q_escape_for_filter(files['line1'])}':expansion=none:fontsize=34:fontcolor=0x00ff88:x=70:y=420:enable='between(t,0.7,2.0)',"
            f"drawtext=fontfile={sans}:textfile='{q_escape_for_filter(files['line2'])}':expansion=none:fontsize=34:fontcolor=0xe8ede9:x=70:y=640:enable='between(t,1.8,3.3)',"
            f"drawtext=fontfile={sans}:textfile='{q_escape_for_filter(files['line3'])}':expansion=none:fontsize=34:fontcolor=0xff5d73:x=70:y=860:enable='between(t,3.0,4.4)',"
            f"drawtext=fontfile={mono}:textfile='{q_escape_for_filter(files['cta'])}':expansion=none:fontsize=32:fontcolor=0x00ff88:x=70:y=1600:enable='between(t,4.1,5.0)',"
            f"drawtext=fontfile={mono}:textfile='{q_escape_for_filter(files['stamp'])}':expansion=none:fontsize=20:fontcolor=0x8fa88f:x=70:y=1660:enable='between(t,0,5.0)',"
            "hue='H=2*sin(2*PI*t*3)':s=1.03,"
            "vignette=PI/5"
            "[v]"
        )

        af = (
            "highpass=f=120,"
            "lowpass=f=2600,"
            "tremolo=f=8:d=0.65,"
            "volume=0.07,"
            "afade=t=out:st=4.6:d=0.4,"
            "loudnorm=I=-18:TP=-1.5:LRA=7"
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
            f"sine=frequency=160:sample_rate=44100:duration={args.duration}",
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
            "20",
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

    print(str(out_path))


if __name__ == "__main__":
    main()
