"""Run StreamForge's credential-free end-to-end HTTP demonstration."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time

import httpx


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def main() -> None:
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "streamforge.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        with httpx.Client(base_url=base_url, timeout=2, trust_env=False) as client:
            for _ in range(50):
                try:
                    health = client.get("/health")
                    if health.status_code == 200 and health.json() == {"status": "ok"}:
                        break
                except (httpx.HTTPError, ValueError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("StreamForge did not become healthy")

            baseline = []
            for index in range(5):
                response = client.post(
                    "/v1/events",
                    json={
                        "id": f"baseline-{index}",
                        "key": "checkout-latency",
                        "value": 10 + index % 2,
                        "ts": 100 + index,
                    },
                )
                response.raise_for_status()
                baseline.append(response.json())

            spike_payload = {
                "id": "spike-1",
                "key": "checkout-latency",
                "value": 100,
                "ts": 106,
            }
            spike_response = client.post("/v1/events", json=spike_payload)
            spike_response.raise_for_status()
            spike = spike_response.json()
            assert spike["status"] == "accepted" and spike["anomaly"] is True

            duplicate_response = client.post("/v1/events", json=spike_payload)
            duplicate_response.raise_for_status()
            duplicate = duplicate_response.json()
            assert duplicate == {"status": "duplicate"}

            advance_response = client.post(
                "/v1/events",
                json={
                    "id": "advance",
                    "key": "checkout-latency",
                    "value": 12,
                    "ts": 200,
                },
            )
            advance_response.raise_for_status()

            late_response = client.post(
                "/v1/events",
                json={"id": "late", "key": "checkout-latency", "value": 9, "ts": 100},
            )
            late_response.raise_for_status()
            late = late_response.json()
            assert late["status"] == "too_late"

            print(
                json.dumps(
                    {
                        "health": "ok",
                        "baseline_events": len(baseline),
                        "spike_anomaly": spike["anomaly"],
                        "duplicate_status": duplicate["status"],
                        "late_status": late["status"],
                        "watermark": late["watermark"],
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
