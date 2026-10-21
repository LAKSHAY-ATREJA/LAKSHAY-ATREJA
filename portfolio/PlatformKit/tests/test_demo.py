import importlib.util
import json
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

spec = importlib.util.spec_from_file_location(
    "platformkit_app", Path(__file__).parents[1] / "demo/app.py"
)
demo = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(demo)


class DemoTest(unittest.TestCase):
    def test_health_metrics_and_missing_path(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), demo.Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(f"{base}/health") as response:
                self.assertEqual(
                    json.load(response),
                    {"status": "ok", "service": "PlatformKit"},
                )
            with urlopen(f"{base}/metrics") as response:
                self.assertIn("platformkit_demo_info", response.read().decode())
            with self.assertRaises(HTTPError) as error:
                urlopen(f"{base}/missing")
            self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
