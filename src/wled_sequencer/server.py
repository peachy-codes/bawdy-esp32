"""HTTP server for Pattern Sequencer web application and sequence storage."""

from __future__ import annotations
import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from wled_sequencer.models import SequenceData, SequenceRepository


class SequencerHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler serving static UI assets and sequence storage API."""

    server: SequencerServer

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default stderr HTTP request logging for quiet operation."""
        pass

    def _send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, data: Any) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, msg: str) -> None:
        self._send_json(status, {"status": "error", "message": msg})

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path.rstrip("/"))

        # 1. API: List sequences
        if path == "/api/sequences":
            seqs = self.server.repo.list_sequences()
            self._send_json(200, seqs)
            return

        # 2. API: Load specific sequence
        if path.startswith("/api/sequences/"):
            parts = path.split("/")
            if len(parts) == 4:
                filename = parts[3]
                seq = self.server.repo.load_sequence(filename)
                if seq is None:
                    self._send_error(404, f"Sequence '{filename}' not found")
                    return
                self._send_json(200, seq.to_dict())
                return

        # 3. Static files
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path.rstrip("/"))

        if path == "/api/sequences":
            try:
                body = self._read_body()
                seq = SequenceData.from_dict(body)
                fname = self.server.repo.save_sequence(seq)
                self._send_json(200, {"status": "ok", "filename": fname, "name": seq.name})
            except Exception as e:
                self._send_error(400, f"Failed to save sequence: {e}")
            return

        self._send_error(404, f"Unknown endpoint: {path}")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path.rstrip("/"))

        if path.startswith("/api/sequences/"):
            parts = path.split("/")
            if len(parts) == 4:
                filename = parts[3]
                deleted = self.server.repo.delete_sequence(filename)
                if deleted:
                    self._send_json(200, {"status": "ok", "deleted": filename})
                else:
                    self._send_error(404, f"Sequence '{filename}' not found")
                return

        self._send_error(404, f"Unknown endpoint: {path}")

    def _serve_static(self, path: str) -> None:
        static_dir = self.server.static_dir
        if path == "" or path == "/":
            target = static_dir / "index.html"
        else:
            rel = path.lstrip("/")
            target = static_dir / rel

        # Security check against directory traversal
        try:
            target = target.resolve()
            static_dir = static_dir.resolve()
            if not str(target).startswith(str(static_dir)):
                self._send_error(403, "Access denied")
                return
        except Exception:
            self._send_error(404, "File not found")
            return

        if not target.is_file():
            self._send_error(404, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(str(target))
        mime_type = mime_type or "application/octet-stream"

        with open(target, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(content)


class SequencerServer(ThreadingHTTPServer):
    """Threading HTTP server with sequence repository and static asset directory."""

    def __init__(
        self,
        server_address: tuple[str, int],
        repo: SequenceRepository,
        static_dir: Path,
    ) -> None:
        self.repo = repo
        self.static_dir = static_dir
        super().__init__(server_address, SequencerHandler)


class SequencerAppServer:
    """Lifecycle manager for the Pattern Sequencer web application server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8081,
        sequences_dir: Path | str | None = None,
        static_dir: Path | str | None = None,
    ) -> None:
        self.host = host
        self.port = port

        # Resolve directories
        base_dir = Path(__file__).resolve().parent
        self.static_dir = Path(static_dir) if static_dir else base_dir / "static"

        root_dir = base_dir.parent.parent
        self.sequences_dir = Path(sequences_dir) if sequences_dir else root_dir / "sequences"
        self.repo = SequenceRepository(self.sequences_dir)

        self.server: SequencerServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self.server is not None and self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self.server = SequencerServer((self.host, self.port), self.repo, self.static_dir)
        self.port = self.server.server_port
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="WledSequencerServer")
        self._thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None


def main() -> None:
    import argparse
    import time
    from rich.console import Console

    parser = argparse.ArgumentParser(description="WLED Pattern Sequencer Studio Server")
    parser.add_argument("--port", type=int, default=8081, help="Web port (default: 8081)")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    console = Console()
    app = SequencerAppServer(host=args.host, port=args.port)
    app.start()
    console.print(f"[bold green]⚡ WLED Pattern Sequencer running on http://{args.host}:{app.port}[/bold green]")
    console.print("Press [bold yellow]Ctrl+C[/bold yellow] to stop.")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop()


if __name__ == "__main__":
    main()

