import argparse
import html
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from src.hash_table import HashTable
from src.linear_probing_hash_table import LinearProbingHashTable


PAGE_STYLES = """
:root{font-family:Arial,sans-serif;color:#202124;background:#f4f6fb}
*{box-sizing:border-box}
body{margin:0;min-height:100vh}
a{color:#174ea6}
header{background:#fff;border-bottom:1px solid #e0e3eb}
nav,.actions{display:flex;flex-wrap:wrap;gap:12px}
nav{width:min(1120px,calc(100% - 32px));margin:auto;padding:20px 0}
nav a{font-weight:700}
main{width:min(1120px,calc(100% - 32px));margin:32px auto 64px}
.panel,.table-panel{padding:22px;border:1px solid #e0e3eb;border-radius:12px;background:#fff;margin:16px 0}
.hint,small{color:#5f6368}
textarea{display:block;width:100%;min-height:120px;padding:12px;font:inherit}
button{padding:10px 16px;margin-top:12px;font:inherit;font-weight:700;cursor:pointer}
.comparison{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.bucket{display:grid;grid-template-columns:110px minmax(0,1fr);gap:12px;padding:14px;border:1px solid #dfe1e5;border-radius:8px;margin:8px 0;overflow-wrap:anywhere}
.bucket strong{color:#174ea6}
.entry{padding:10px;border-left:3px solid #8ab4f8;background:#f8fbff;margin:8px 0}
.entry code{font-weight:700}
.collision{border-color:#f9ab00;background:#fffaf0}
.probe-path{line-height:1.6}
@media(max-width:700px){.comparison{grid-template-columns:1fr}.bucket{grid-template-columns:1fr}}
"""


def _render_chaining(table):
    rows = []
    for bucket_index, chain in table.snapshot():
        if chain:
            entries = []
            for key, value, hash_value in chain:
                entries.append(
                    '<div class="entry">'
                    f"<code>{html.escape(key)}</code> = {html.escape(value)}"
                    f"<br><small>hash {hash_value} % {table.capacity} = bucket {bucket_index}; "
                    f"stored at bucket {bucket_index}</small></div>"
                )
            content = "".join(entries)
            row_class = "bucket collision" if len(chain) > 1 else "bucket"
        else:
            content = "<span class=\"hint\">empty</span>"
            row_class = "bucket"
        rows.append(
            f'<div class="{row_class}"><strong>Bucket {bucket_index}</strong>{content}</div>'
        )
    return (
        '<section class="table-panel"><h2>Separate Chaining</h2>'
        f"<p>Capacity: {table.capacity} · Entries: {len(table)}</p>{''.join(rows)}</section>"
    )


def _render_linear_probing(table):
    rows = []
    for bucket_index, state, key, value, hash_value in table.snapshot():
        if state == "occupied":
            home_bucket = hash_value % table.capacity
            steps = table.probe_trace(key)
            path = " &rarr; ".join(
                f"bucket {index} ({'stored' if status == 'found' else status})"
                for index, status in steps
            )
            row_class = "bucket collision" if len(steps) > 1 else "bucket"
            content = (
                '<div class="entry">'
                f"<code>{html.escape(key)}</code> = {html.escape(value)}"
                f"<br><small>hash {hash_value}; home bucket {home_bucket}; "
                f"stored at bucket {bucket_index}</small>"
                f'<div class="probe-path"><strong>Probe path:</strong> {path}</div></div>'
            )
        elif state == "deleted":
            row_class = "bucket"
            content = '<span class="hint">deleted (tombstone)</span>'
        else:
            row_class = "bucket"
            content = '<span class="hint">empty</span>'
        rows.append(
            f'<div class="{row_class}"><strong>Bucket {bucket_index}</strong>{content}</div>'
        )
    return (
        '<section class="table-panel"><h2>Linear Probing</h2>'
        f"<p>Capacity: {table.capacity} · Entries: {len(table)}</p>{''.join(rows)}</section>"
    )


class ProbingComparisonServer:
    def __init__(self, host, port):
        self.chaining_table = HashTable()
        self.linear_probing_table = LinearProbingHashTable()
        comparison_server = self

        class Handler(BaseHTTPRequestHandler):
            def send_page(handler, title, body, status=200):
                document = (
                    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">'
                    f"<title>{html.escape(title)}</title><style>{PAGE_STYLES}</style></head><body>"
                    '<header><nav><a href="/">Input data</a><a href="/chaining">Separate Chaining</a>'
                    '<a href="/linear-probing">Linear Probing</a><a href="/compare">Compare</a></nav></header>'
                    f"{body}</body></html>"
                ).encode("utf-8")
                handler.send_response(status)
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(document)))
                handler.end_headers()
                handler.wfile.write(document)

            def do_GET(handler):
                path = handler.path.split("?", 1)[0]
                if path == "/":
                    handler.send_page(
                        "Hash table comparison",
                        """
<main><section class="panel">
  <h1>Compare collision strategies</h1>
  <p>Enter one key-value pair per line using <code>key=value</code>.
  The same records are inserted into both hash tables.</p>
  <form method="POST" action="/insert">
    <label for="data">Test data</label>
    <textarea id="data" name="data" required>a=first
q=second
b=third</textarea>
    <button type="submit">Insert into both tables</button>
  </form>
  <p class="hint">The example keys <code>a</code> and <code>q</code> collide at capacity 16.</p>
</section></main>""",
                    )
                    return

                if path == "/chaining":
                    handler.send_page(
                        "Separate Chaining",
                        f"<main><h1>Separate Chaining</h1>{_render_chaining(comparison_server.chaining_table)}</main>",
                    )
                    return

                if path == "/linear-probing":
                    handler.send_page(
                        "Linear Probing",
                        f"<main><h1>Linear Probing</h1>{_render_linear_probing(comparison_server.linear_probing_table)}</main>",
                    )
                    return

                if path == "/compare":
                    handler.send_page(
                        "Compare hash tables",
                        "<main><h1>Same data, different collision handling</h1>"
                        '<div class="comparison">'
                        f"{_render_chaining(comparison_server.chaining_table)}"
                        f"{_render_linear_probing(comparison_server.linear_probing_table)}"
                        "</div></main>",
                    )
                    return

                handler.send_error(404)

            def do_POST(handler):
                if handler.path != "/insert":
                    handler.send_error(404)
                    return

                try:
                    content_length = int(handler.headers.get("Content-Length", "0"))
                    if content_length <= 0 or content_length > 65536:
                        raise ValueError("invalid request size")
                    form_data = handler.rfile.read(content_length).decode("utf-8")
                except (ValueError, UnicodeDecodeError):
                    handler.send_error(400, "Invalid form data")
                    return

                values = parse_qs(form_data, keep_blank_values=True).get("data", [])
                if not values:
                    handler.send_error(400, "Missing test data")
                    return

                records = []
                try:
                    for line in values[0].splitlines():
                        if not line.strip():
                            continue
                        if "=" not in line:
                            raise ValueError("Each row must use key=value")
                        key, value = line.split("=", 1)
                        if not key.strip():
                            raise ValueError("Keys must not be empty")
                        if comparison_server.chaining_table.contains(key):
                            raise ValueError(f"Key already exists: {key}")
                        if any(existing_key == key for existing_key, _ in records):
                            raise ValueError(f"Duplicate key in input: {key}")
                        records.append((key, value))
                    if not records:
                        raise ValueError("Enter at least one key-value pair")
                except (TypeError, ValueError) as error:
                    handler.send_error(400, str(error))
                    return

                for key, value in records:
                    comparison_server.chaining_table.put(key, value)
                    comparison_server.linear_probing_table.put(key, value)

                handler.send_response(303)
                handler.send_header("Location", "/compare")
                handler.send_header("Content-Length", "0")
                handler.end_headers()

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


def create_server(host="127.0.0.1", port=8001):
    return ProbingComparisonServer(host, port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare chaining and linear probing")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    arguments = parser.parse_args()

    server = create_server(arguments.host, arguments.port)
    server.start()
    print(f"Hash table comparison running at http://{arguments.host}:{server.port}", flush=True)
    try:
        server._thread.join()
    except KeyboardInterrupt:
        server.stop()
