#!/usr/bin/env python3
"""
Orbital Telemetry Pulse
Updates the subtle signal heartbeat in README.md to maintain daily telemetry and contribution activity.
"""

import re
import socket
import time
from datetime import datetime, timezone

TARGETS = [
    ("Cloudflare DNS", "1.1.1.1", 53),
    ("Google DNS", "8.8.8.8", 53),
]


def probe_latency(host, port, timeout=2.0):
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        return None


def generate_pulse():
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    latencies = [probe_latency(h, p) for _, h, p in TARGETS]
    valid = [l for l in latencies if l is not None]
    ping_str = f"{min(valid)}ms" if valid else "nominal"
    return f"<!-- PULSE:START -->\n<sub><code>signal: nominal</code> • <code>ping: {ping_str}</code> • <code>pulse: {now_utc}</code></sub>\n<!-- PULSE:END -->"


def main():
    readme_path = "README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    pulse = generate_pulse()
    pattern = r"<!-- PULSE:START -->.*?<!-- PULSE:END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        updated_content = re.sub(pattern, pulse, content, flags=re.DOTALL)
    else:
        updated_content = content.rstrip() + f"\n\n{pulse}\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("Profile pulse updated successfully.")


if __name__ == "__main__":
    main()
