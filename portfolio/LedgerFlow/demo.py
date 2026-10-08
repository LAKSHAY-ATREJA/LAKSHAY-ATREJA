"""Run a real HTTP demonstration against a temporary local LedgerFlow server."""

import json
import socket
import threading
import time
from decimal import Decimal
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn


def run_demo():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        server = uvicorn.Server(uvicorn.Config("ledgerflow.api:app", log_level="error"))
        thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
        origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
        thread.start()

        def request(path, body=None):
            headers = {"Content-Type": "application/json", "Idempotency-Key": "demo-transfer"}
            data = json.dumps(body).encode() if body is not None else None
            req = Request(origin + path, data=data, headers=headers)
            try:
                with urlopen(req, timeout=5) as response:
                    return response.status, json.load(response)
            except HTTPError as exc:
                return exc.code, json.load(exc)

        try:
            deadline = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > deadline:
                    raise RuntimeError("The demo server did not start")
                time.sleep(0.02)
            assert request("/health") == (200, {"status": "ok"})
            payload = {"source": "cash", "destination": "merchant", "amount": "12.50"}
            status, first = request("/v1/transfers", payload)
            assert status == 201, (status, first)
            print("PASS  Transfer accepted: cash -> merchant, 12.50")
            assert request("/v1/transfers", payload) == (201, first)
            print("PASS  Retry returned the same journal entry")
            assert request("/v1/transfers", {**payload, "amount": "20"})[0] == 400
            print("PASS  Reusing the key with a different amount was rejected")
            cash = Decimal(request("/v1/accounts/cash/balance")[1]["balance"])
            merchant = Decimal(request("/v1/accounts/merchant/balance")[1]["balance"])
            assert (cash, merchant, cash + merchant) == (
                Decimal("-12.50"),
                Decimal("12.50"),
                Decimal("0"),
            )
            assert len(request("/v1/audit")[1]) == 1
            print(f"PASS  Balances: cash={cash}, merchant={merchant}; one audit entry")
            print("Demo complete. Start uvicorn ledgerflow.api:app to explore /docs.")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            if thread.is_alive():
                raise RuntimeError("The demo server did not shut down")


if __name__ == "__main__":
    run_demo()
