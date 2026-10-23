from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def get_json(url: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
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
            "searchgrid.api:app",
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
                status, health = get_json(f"{base_url}/health")
                if status == 200:
                    break
            except urllib.error.URLError:
                time.sleep(0.1)
        else:
            raise RuntimeError("SearchGrid did not become healthy")

        query = urllib.parse.urlencode({"q": "PostgreSQL vector", "k": 2})
        status, results = get_json(f"{base_url}/v1/search?{query}")
        assert status == 200
        assert isinstance(results, list) and results
        assert results[0]["id"] == "4"
        assert results[0]["lexical_rank"] == 1
        assert results[0]["vector_rank"] == 1

        invalid_status, invalid = get_json(f"{base_url}/v1/search?q=%21%21%21")
        assert invalid_status == 422
        assert invalid == {"detail": "q must contain a word or number"}

        print(json.dumps({"health": health, "top_result": results[0]}, indent=2))
        print("SearchGrid HTTP demo passed")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
