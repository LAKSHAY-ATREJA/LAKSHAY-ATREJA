"""Run PlatformKit's credential-free local HTTP demonstration."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import urlopen


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def main() -> None:
    port = available_port()
    environment = os.environ.copy()
    environment.update({"HOST": "127.0.0.1", "PORT": str(port)})
    server = subprocess.Popen(
        [sys.executable, "demo/app.py"],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base_url = f"http://127.0.0.1:{port}"

    try:
        for _ in range(50):
            try:
                with urlopen(f"{base_url}/health", timeout=1) as response:
                    health = json.load(response)
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        else:
            raise RuntimeError("PlatformKit demo did not become healthy")

        assert health == {"status": "ok", "service": "PlatformKit"}
        with urlopen(f"{base_url}/metrics", timeout=2) as response:
            metrics = response.read().decode()
        assert 'platformkit_demo_info{version="1.0.0"} 1' in metrics

        try:
            urlopen(f"{base_url}/missing", timeout=2)
        except HTTPError as error:
            assert error.code == 404
            missing_status = error.code
        else:
            raise AssertionError("unknown paths must return 404")

        print(
            json.dumps(
                {
                    "health": health,
                    "metric": 'platformkit_demo_info{version="1.0.0"} 1',
                    "missing_path_status": missing_status,
                },
                indent=2,
            )
        )
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()
