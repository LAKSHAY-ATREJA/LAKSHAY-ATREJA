from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def request_json(
    url: str, payload: dict[str, object] | None = None
) -> tuple[int, object]:
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def main() -> None:
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "sloforge.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ]
    )
    try:
        for _ in range(50):
            try:
                status, health = request_json(f"{base_url}/health")
                if status == 200:
                    break
            except urllib.error.URLError:
                time.sleep(0.1)
        else:
            raise RuntimeError("SLOForge did not become healthy")

        incident = {
            "target": 0.99,
            "fast_short": {"good": 80, "total": 100},
            "fast_long": {"good": 800, "total": 1000},
            "slow_short": {"good": 99, "total": 100},
            "slow_long": {"good": 990, "total": 1000},
        }
        status, decision = request_json(f"{base_url}/v1/evaluate", incident)
        assert status == 200
        assert decision["page"] is True
        assert decision["reasons"] == ["fast_burn"]
        assert decision["windows"]["fast_short"]["burn_rate"] == 20

        invalid = incident | {"fast_short": {"good": 101, "total": 100}}
        invalid_status, _ = request_json(f"{base_url}/v1/evaluate", invalid)
        assert invalid_status == 422

        print(json.dumps({"health": health, "decision": decision}, indent=2))
        print("SLOForge HTTP demo passed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
