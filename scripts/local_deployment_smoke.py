"""Start the actual Streamlit HTTP server and check its loopback health.

This is a local process/network check, *never* proof of public deployment.
It performs no Gemini request and terminates only its own subprocess.

Run: python scripts/local_deployment_smoke.py
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "true", "--server.address", "127.0.0.1",
            "--server.port", str(port), "--browser.gatherUsageStats", "false",
        ],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://127.0.0.1:{port}/_stcore/health"
    try:
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            if process.poll() is not None:
                print("LOCAL STREAMLIT SMOKE FAILED: server exited before becoming healthy.")
                return 1
            try:
                with opener.open(url, timeout=1.5) as response:
                    if response.status == 200 and response.read().strip() == b"ok":
                        print("LOCAL STREAMLIT HTTP SMOKE PASSED: health endpoint returned 200 OK.")
                        print("This is loopback-only, not a public deployment URL.")
                        return 0
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
                pass
            time.sleep(0.25)
        print("LOCAL STREAMLIT SMOKE FAILED: no healthy response within 20 seconds.")
        return 1
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
