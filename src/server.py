import argparse
import html
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from src.shortener import UrlShortener


PAGE_STYLES = """
:root{font-family:Arial,sans-serif;color:#202124;background:#f4f6fb}
*{box-sizing:border-box}
body{margin:0;min-height:100vh}
a{color:#174ea6}
.site-header{background:#fff;border-bottom:1px solid #e0e3eb}
.header-content{width:min(1120px,calc(100% - 32px));min-height:68px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:24px}
.brand{font-size:20px;font-weight:800;text-decoration:none;color:#202124}
.site-nav,.actions{display:flex;align-items:center;flex-wrap:wrap;gap:10px}
.nav-link{padding:9px 12px;border-radius:8px;text-decoration:none;color:#3c4043;font-weight:600}
.nav-link:hover{background:#f1f3f4}
.page-shell{width:min(1120px,calc(100% - 32px));margin:36px auto 64px}
.hero{display:flex;align-items:center;justify-content:space-between;gap:24px;margin-bottom:24px}
.eyebrow{margin:0 0 8px;color:#1967d2;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
h1{margin:0 0 8px;font-size:clamp(28px,4vw,40px)}
h2{margin:0 0 8px;font-size:20px}
.muted,.intro{color:#5f6368;line-height:1.55}
.content-grid{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(240px,.8fr);gap:20px}
.panel,.table-section{padding:24px;border:1px solid #e0e3eb;border-radius:14px;background:#fff;box-shadow:0 2px 8px #2021240a}
.form-field{display:block;margin:20px 0 16px;font-weight:700}
.form-field input{display:block;width:100%;margin-top:8px;padding:13px 14px;border:1px solid #c7cbd4;border-radius:8px;font:inherit}
.form-field input:focus{outline:2px solid #8ab4f8;border-color:#1a73e8}
.button{display:inline-flex;min-height:40px;align-items:center;justify-content:center;padding:9px 15px;border:1px solid transparent;border-radius:8px;font:inherit;font-weight:700;text-decoration:none;cursor:pointer}
.button-primary{background:#1967d2;color:#fff}
.button-primary:hover{background:#1558b0}
.button-secondary{background:#fff;border-color:#c7cbd4;color:#3c4043}
.button-secondary:hover{background:#f8f9fa}
.helper-panel{background:linear-gradient(145deg,#eaf2ff,#f7faff)}
.helper-panel ol{padding-left:20px;color:#3c4043;line-height:1.8}
.metrics-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0 28px}
.metric-card{min-width:0;padding:16px;border:1px solid #e0e3eb;border-radius:10px;background:#fff}
.metric-card span{display:block;color:#5f6368;font-size:13px}
.metric-card strong{display:block;margin-top:8px;font-size:24px}
.table-toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:28px 0 16px}
.table-section{margin:20px 0;padding:20px}
.section-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.table-meta{margin:0;color:#5f6368;font-size:14px}
.bucket-list{margin-top:16px}
.bucket-row{display:grid;grid-template-columns:150px minmax(0,1fr);margin:8px 0;border:1px solid #dfe1e5;border-radius:9px;background:#fff;overflow:hidden}
.bucket-label{display:flex;flex-direction:column;justify-content:center;gap:8px;padding:12px;background:#f1f4f9}
.collision-row .bucket-label{background:#fff1df}
.collision-badge{align-self:flex-start;border-radius:12px;padding:4px 9px;background:#f9ab00;color:#202124;font-size:12px;font-weight:800}
.chain-view{display:flex;align-items:center;gap:10px;padding:12px;overflow-x:auto}
.head-pointer,.chain-end{flex:0 0 auto;padding:7px 10px;border:1px dashed #9aa0a6;border-radius:6px;color:#5f6368;font-size:13px;font-weight:700}
.chain-arrow{flex:0 0 auto;color:#5f6368;font-size:22px}
.chain-node{display:flex;flex:0 0 230px;flex-direction:column;gap:8px;padding:12px;border:2px solid #8ab4f8;border-radius:9px;background:#f8fbff}
.chain-node code{overflow-wrap:anywhere;color:#174ea6}
.chain-node small{color:#5f6368}
.result-card{padding:22px;border:1px solid #d5e2f7;border-radius:12px;background:#f8fbff}
.result-url{display:block;margin:8px 0 20px;overflow-wrap:anywhere;font-size:20px;font-weight:700}
.original-url{overflow-wrap:anywhere}
.result-actions{margin-top:18px}
@media(max-width:760px){.hero,.table-toolbar{align-items:flex-start;flex-direction:column}.content-grid{grid-template-columns:1fr}.metrics-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:520px){.header-content{align-items:flex-start;flex-direction:column;padding:14px 0}.page-shell{margin-top:24px}.panel,.table-section{padding:16px}.metrics-grid{gap:8px}.bucket-row{grid-template-columns:1fr}.bucket-label{align-items:center;flex-direction:row;justify-content:space-between}}
"""


class UrlShortenerServer:
    def __init__(self, host, port):
        shortener = UrlShortener()

        class Handler(BaseHTTPRequestHandler):
            def send_html(handler, body, status=200):
                encoded = body.encode("utf-8")
                handler.send_response(status)
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(encoded)))
                handler.end_headers()
                handler.wfile.write(encoded)

            def send_page(handler, title, body):
                document = (
                    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">'
                    f"<title>{html.escape(title)}</title><style>{PAGE_STYLES}</style></head><body>"
                    '<header class="site-header"><div class="header-content">'
                    '<a class="brand" href="/">Link Shortener</a>'
                    '<nav class="site-nav" aria-label="Main navigation">'
                    '<a class="nav-link" href="/">Shortener</a>'
                    '<a class="nav-link" href="/table">Hash Table</a>'
                    "</nav></div></header>"
                    f"{body}</body></html>"
                )
                handler.send_html(document)

            def do_GET(handler):
                path = handler.path.split("?", 1)[0]
                if path == "/":
                    url_table = shortener._url_to_code
                    buckets = url_table.snapshot()
                    collision_count = sum(1 for _, chain in buckets if len(chain) > 1)
                    load_factor = len(url_table) / url_table.capacity
                    body = f"""
<main class="page-shell">
  <section class="hero">
    <div><p class="eyebrow">Simple URL management</p><h1>Make long links short</h1>
    <p class="intro">Create a compact link and see how the hash table stores it.</p></div>
    <a class="button button-secondary" href="/table">Explore hash table</a>
  </section>
  <div class="content-grid">
    <section class="panel">
      <h2>Create a short link</h2>
      <p class="muted">Enter a valid HTTP or HTTPS address.</p>
      <form method="POST" action="/shorten">
        <label class="form-field" for="url">Original URL
          <input id="url" name="url" type="url" placeholder="https://example.com" required>
        </label>
        <div class="actions">
          <button class="button button-primary" type="submit">Shorten URL</button>
          <button class="button button-secondary" type="reset">Clear</button>
        </div>
      </form>
    </section>
    <aside class="panel helper-panel">
      <h2>How it works</h2>
      <ol><li>Submit a URL to create a short code.</li>
      <li>URLs are stored in a hash table.</li>
      <li>Colliding keys are connected in a linked list.</li></ol>
    </aside>
  </div>
  <section aria-label="Hash table summary">
    <div class="metrics-grid">
      <div class="metric-card"><span>Links created</span><strong>{len(url_table)}</strong></div>
      <div class="metric-card"><span>Bucket capacity</span><strong>{url_table.capacity}</strong></div>
      <div class="metric-card"><span>Load factor</span><strong>{load_factor:.0%}</strong></div>
      <div class="metric-card"><span>Collision buckets</span><strong>{collision_count}</strong></div>
    </div>
  </section>
</main>"""
                    handler.send_page("URL Shortener", body)
                    return

                if path == "/table":
                    sections = []
                    for title, table in (("URL to short code", shortener._url_to_code), ("Short code to URL", shortener._code_to_url)):
                        snapshot = table.snapshot()
                        occupied_count = sum(1 for _, chain in snapshot if chain)
                        collision_count = sum(1 for _, chain in snapshot if len(chain) > 1)
                        load_factor = len(table) / table.capacity
                        rows = [
                            f'<div class="section-heading"><div><h2>{html.escape(title)}</h2>'
                            f'<p class="table-meta">Hash index = Horner hash % {table.capacity}</p></div></div>',
                            '<div class="metrics-grid">'
                            f'<div class="metric-card"><span>Entries</span><strong>{len(table)}</strong></div>'
                            f'<div class="metric-card"><span>capacity</span><strong>{table.capacity}</strong></div>'
                            f'<div class="metric-card"><span>Load factor</span><strong>{load_factor:.0%}</strong></div>'
                            f'<div class="metric-card"><span>Occupied buckets</span><strong>{occupied_count}</strong></div>'
                            f'<div class="metric-card"><span>Collision buckets</span><strong>{collision_count}</strong></div>'
                            "</div><div class=\"bucket-list\">",
                        ]
                        for bucket_index, chain in snapshot:
                            nodes = ['<span class="head-pointer">head</span>']
                            for node_index, (key, value, hash_value) in enumerate(chain, start=1):
                                nodes.extend(
                                    (
                                        '<span class="chain-arrow" aria-hidden="true">&rarr;</span>',
                                        f'<article class="chain-node">'
                                        f"<strong>Node {node_index}</strong>"
                                        f"<code>{html.escape(str(key))}</code>"
                                        f'<span><b>value:</b> {html.escape(str(value))}</span>'
                                        f"<small>hash {hash_value} % {table.capacity} = {bucket_index}</small>"
                                        "</article>",
                                    )
                                )
                            nodes.extend(
                                (
                                    '<span class="chain-arrow" aria-hidden="true">&rarr;</span>',
                                    '<span class="chain-end">NULL</span>',
                                )
                            )
                            collision = (
                                f'<span class="collision-badge">Collision: {len(chain)} nodes</span>'
                                if len(chain) > 1
                                else ""
                            )
                            row_class = "bucket-row collision-row" if len(chain) > 1 else "bucket-row"
                            rows.append(
                                f'<div class="{row_class}" aria-label="Bucket {bucket_index} linked list">'
                                f'<div class="bucket-label"><strong>bucket {bucket_index}</strong>{collision}</div>'
                                f'<div class="chain-view">{"".join(nodes)}</div></div>'
                            )
                        rows.append("</div>")
                        sections.append(f'<section class="table-section">{"".join(rows)}</section>')

                    body = f"""
<main class="page-shell">
  <section class="hero">
    <div><p class="eyebrow">Live data structure</p><h1>Hash table visualization</h1>
    <p class="intro">Follow each bucket head through its linked list. Shared buckets are highlighted as collisions.</p></div>
  </section>
  <div class="table-toolbar">
    <p class="muted">This view updates from the current in-memory tables.</p>
    <div class="actions">
      <a class="button button-secondary" href="/table">Refresh</a>
      <a class="button button-primary" href="/">Create short link</a>
    </div>
  </div>
  {"".join(sections)}
</main>"""
                    handler.send_page("Hash Table", body)
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

                short_url = f"http://{handler.headers.get('Host', 'localhost')}/{code}"
                escaped_short_url = html.escape(short_url, quote=True)
                escaped_code = html.escape(code, quote=True)
                body = f"""
<main class="page-shell">
  <section class="hero">
    <div><p class="eyebrow">Link created</p><h1>Your short URL is ready</h1>
    <p class="intro">Use the short link below or inspect how it was stored.</p></div>
  </section>
  <section class="panel">
    <h2>Short URL</h2>
    <div class="result-card">
      <a class="result-url" data-code="{escaped_code}" href="{escaped_short_url}">{escaped_short_url}</a>
      <p class="muted original-url"><strong>Original:</strong> {html.escape(url)}</p>
    </div>
    <div class="actions result-actions">
      <a class="button button-primary" href="{escaped_short_url}">Open short URL</a>
      <a class="button button-secondary" href="/">Shorten another</a>
      <a class="button button-secondary" href="/table">View hash table</a>
    </div>
  </section>
</main>"""
                handler.send_page("Short URL created", body)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the URL shortener server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args()

    server = create_server(arguments.host, arguments.port)
    server.start()
    print(f"URL shortener running at http://{arguments.host}:{server.port}", flush=True)
    try:
        server._thread.join()
    except KeyboardInterrupt:
        server.stop()
