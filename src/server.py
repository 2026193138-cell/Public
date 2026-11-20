import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from src.shortener import UrlShortener


class UrlShortenerServer:
    def __init__(self, host, port):
        shortener = UrlShortener()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(handler):
                path = handler.path.split("?", 1)[0]
                if path == "/":
                    body = b"<form method=\"POST\" action=\"/shorten\"><input name=\"url\"><button>Shorten</button></form>"
                    handler.send_response(200)
                    handler.send_header("Content-Type", "text/html; charset=utf-8")
                    handler.send_header("Content-Length", str(len(body)))
                    handler.end_headers()
                    handler.wfile.write(body)
                    return

                code = path.removeprefix("/")
                if not code or "/" in code:
                    handler.send_error(404)
                    return
                try:
                    url = shortener.expand(code)
                except KeyError:
                    handler.send_error(404)
                    return

                handler.send_response(302)
                handler.send_header("Location", url)
                handler.end_headers()

            def do_POST(handler):
                if handler.path != "/shorten":
                    handler.send_error(404)
                    return

                length_header = handler.headers.get("Content-Length")
                try:
                    length = int(length_header or 0)
                except ValueError:
                    handler.send_error(400)
                    return

                data = handler.rfile.read(length).decode("utf-8")
                url = parse_qs(data).get("url", [""])[0]
                try:
                    code = shortener.shorten(url)
                except ValueError:
                    handler.send_error(400)
                    return

                body = code.encode("utf-8")
                handler.send_response(200)
                handler.send_header("Content-Type", "text/plain; charset=utf-8")
                handler.send_header("Content-Length", str(len(body)))
                handler.end_headers()
                handler.wfile.write(body)

            def log_message(self, format, *args):
                return

        self._server = ThreadingHTTPServer((host, port), Handler)
        self.host = host
        self.port = self._server.server_address[1]
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)


def create_server(host="127.0.0.1", port=8000):
    return UrlShortenerServer(host, port)
