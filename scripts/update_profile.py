#!/usr/bin/env python3
"""
Orbital Telemetry Profile Updater
Fetches NASA Astronomy Picture of the Day (APOD) and probes global internet backbones,
then updates the live telemetry section in README.md.
"""

import json
import re
import socket
import time
import urllib.request
from datetime import datetime, timezone

NASA_APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"

TARGETS = [
    ("Cloudflare DNS", "1.1.1.1", 53),
    ("Google DNS", "8.8.8.8", 53),
    ("Quad9 DNS", "9.9.9.9", 53),
    ("GitHub Core", "github.com", 443),
    ("AWS Cloud", "aws.amazon.com", 443),
]


def fetch_nasa_apod():
    req = urllib.request.Request(NASA_APOD_URL, headers={"User-Agent": "OrbitalCanary/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: NASA APOD fetch error: {e}")
        return {
            "title": "Cosmic Observation Offline",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "url": "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1200",
            "media_type": "image",
            "explanation": "NASA APOD API was temporarily unreachable during probe execution.",
            "copyright": "Deep Space Archive",
        }


def probe_latency(host, port, timeout=3.0):
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.perf_counter() - t0) * 1000, 2)
    except Exception:
        return None


def render_ascii_bar(ms, max_ms=150.0):
    if ms is None:
        return "[TIMEOUT]"
    filled = min(10, max(1, int((ms / max_ms) * 10)))
    return "█" * filled + "░" * (10 - filled)


def generate_section(apod, probes):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    date_str = apod.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    title = apod.get("title", "Deep Space Capture")
    media_url = apod.get("hdurl") or apod.get("url", "")
    media_type = apod.get("media_type", "image")
    explanation = apod.get("explanation", "").strip()
    copyright_info = apod.get("copyright", "NASA / Public Domain").replace("\n", " ").strip()

    valid_latencies = [lat for _, _, _, lat in probes if lat is not None]
    avg_latency = round(sum(valid_latencies) / len(valid_latencies), 2) if valid_latencies else 0.0

    lines = ["<!-- ORBITAL_TELEMETRY:START -->\n"]
    lines.append('<div align="center">\n')
    lines.append(f"  <p><b>Today\'s Cosmic Observation: {title} ({date_str})</b></p>\n")
    if media_type == "image":
        lines.append(f'  <img src="{media_url}" width="100%" alt="{title}" style="border-radius: 8px; max-height: 420px; object-fit: cover;" />\n')
    else:
        lines.append(f'  <p><a href="{media_url}" target="_blank">▶️ Watch Cosmic Video ({title})</a></p>\n')
    lines.append(f"  <p><sub><i>Credits: {copyright_info}</i></sub></p>\n")
    lines.append("</div>\n\n")

    lines.append("<details>\n")
    lines.append(f"<summary>📡 <b>Live Global Backbone Latency Canary</b> (Avg RTT: <code>{avg_latency} ms</code>)</summary>\n\n")
    lines.append("```text\n")
    lines.append(f"{'ENDPOINT TARGET':<22} | {'HOST':<16} | {'LATENCY':<10} | {'TELEMETRY':<10} | STATUS\n")
    lines.append("─" * 75 + "\n")

    for name, host, port, lat in probes:
        if lat is not None:
            bar = render_ascii_bar(lat)
            lines.append(f"{name:<22} | {host:<16} | {lat:>6.2f} ms | {bar} | ONLINE\n")
        else:
            lines.append(f"{name:<22} | {host:<16} |    TIMEOUT | ░░░░░░░░░░ | UNREACHABLE\n")

    lines.append("─" * 75 + "\n")
    lines.append(f"Last probe: {now_utc} • Runner: GitHub Actions (Ubuntu) • Avg: {avg_latency} ms\n")
    lines.append("```\n")
    lines.append("</details>\n")
    lines.append("<!-- ORBITAL_TELEMETRY:END -->")

    return "".join(lines)


def main():
    print("Fetching NASA observation and probing network latency...")
    apod = fetch_nasa_apod()
    probes = []
    for name, host, port in TARGETS:
        probes.append((name, host, port, probe_latency(host, port)))

    new_section = generate_section(apod, probes)

    readme_path = "README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"<!-- ORBITAL_TELEMETRY:START -->.*?<!-- ORBITAL_TELEMETRY:END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        updated_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        marker = "<!-- GitHub Statistics"
        if marker in content:
            updated_content = content.replace(marker, f'<h2 align="center">🛰️ <em>Live Orbital Telemetry & Deep Space Feed</em></h2>\n\n{new_section}\n\n<br/>\n\n{marker}')
        else:
            updated_content = content + f"\n\n{new_section}\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Profile README updated successfully with live orbital telemetry!")


if __name__ == "__main__":
    main()
