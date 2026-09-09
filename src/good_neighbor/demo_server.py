from __future__ import annotations

import argparse
import copy
import json
import logging
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .agentcore_app import run_incident_payload


log = logging.getLogger(__name__)
WEB_ROOT = Path(__file__).with_name("web")


class DemoController:
    """Idempotent judge-demo boundary around the frozen incident."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._stage = "ready"
        self._report: dict[str, Any] | None = None
        self._sequence = 0
        self._results: dict[tuple[str, str], dict[str, Any]] = {}

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._snapshot_unlocked())

    def apply(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action not in {"start", "approve", "reset"}:
            raise ValueError("unsupported demo action")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        idempotency_key = payload.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("idempotency_key must be a non-empty string")
        if len(idempotency_key) > 128:
            raise ValueError("idempotency_key must be at most 128 characters")

        result_key = (action, idempotency_key)
        with self._lock:
            if result_key in self._results:
                return copy.deepcopy(self._results[result_key])

            if action == "start":
                result = self._start_unlocked()
            elif action == "approve":
                result = self._approve_unlocked(payload)
            else:
                result = self._reset_unlocked()
            self._results[result_key] = copy.deepcopy(result)
            return result

    def _start_unlocked(self) -> dict[str, Any]:
        if self._stage not in {"ready", "completed"}:
            raise ValueError("incident is already awaiting a decision")
        self._report = run_incident_payload(
            {
                "action": "run_incident",
                "approve": False,
                "task": "Recover the capacity-drop incident within deterministic safety boundaries.",
            }
        )
        self._stage = "awaiting_decision"
        self._sequence += 1
        return copy.deepcopy(self._snapshot_unlocked())

    def _approve_unlocked(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._stage != "awaiting_decision" or self._report is None:
            raise ValueError("there is no pending decision to approve")
        expected = self._report["human_decision"]["decision_id"]
        if payload.get("decision_id") != expected:
            raise ValueError("decision_id does not match the pending decision")
        self._report = run_incident_payload(
            {
                "action": "run_incident",
                "approve": True,
                "task": "Resume the persisted recovery decision and commit the approved patch.",
            }
        )
        self._stage = "completed"
        self._sequence += 1
        return copy.deepcopy(self._snapshot_unlocked())

    def _reset_unlocked(self) -> dict[str, Any]:
        self._stage = "ready"
        self._report = None
        self._sequence += 1
        return copy.deepcopy(self._snapshot_unlocked())

    def _snapshot_unlocked(self) -> dict[str, Any]:
        return {
            "schema_version": "good-neighbor.demo.v1",
            "stage": self._stage,
            "sequence": self._sequence,
            "report": self._report,
        }


def build_handler(controller: DemoController) -> type[BaseHTTPRequestHandler]:
    class DemoRequestHandler(BaseHTTPRequestHandler):
        server_version = "GoodNeighborDemo/1.0"

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/state":
                self._send_json(controller.snapshot())
                return
            asset = "index.html" if path == "/" else path.removeprefix("/")
            if asset not in {"index.html", "evidence.html", "app.css", "app.js"}:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
            }[Path(asset).suffix]
            self._send_bytes((WEB_ROOT / asset).read_bytes(), content_type)

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            prefix = "/api/actions/"
            if not path.startswith(prefix):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 16_384:
                    raise ValueError("request body must be between 1 and 16384 bytes")
                payload = json.loads(self.rfile.read(length))
                result = controller.apply(path.removeprefix(prefix), payload)
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._send_json(result)

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8", status=status)

        def _send_bytes(
            self,
            body: bytes,
            content_type: str,
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            log.info("demo_http " + format, *args)

    return DemoRequestHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Good Neighbor judge demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    args = parser.parse_args()

    server = ThreadingHTTPServer(
        (args.host, args.port),
        build_handler(DemoController()),
    )
    url = f"http://{args.host}:{args.port}"
    print(f"Good Neighbor judge demo: {url}", flush=True)
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
