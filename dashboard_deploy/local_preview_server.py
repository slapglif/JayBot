from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit

UPSTREAM = 'https://kitty-litter-live.cryptsmith.workers.dev/api/live'

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/live') or self.path.startswith('/api/weekend'):
            qs = urlsplit(self.path).query
            if self.path.startswith('/api/weekend'):
                qs = ('weekend=1&' + qs) if qs else 'weekend=1'
            target = UPSTREAM + (('?' + qs) if qs else '')
            try:
                req = Request(target, headers={'accept': 'application/json', 'user-agent': 'jaybot-local-preview/1.0'})
                with urlopen(req, timeout=15) as r:
                    body = r.read()
                    self.send_response(r.status)
                    self.send_header('content-type', r.headers.get('content-type') or 'application/json; charset=utf-8')
                    self.send_header('cache-control', 'no-store, no-cache, must-revalidate')
                    self.end_headers()
                    self.wfile.write(body)
            except HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header('content-type', e.headers.get('content-type') or 'text/plain')
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                body = (repr(e) + '\n').encode()
                self.send_response(502)
                self.send_header('content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(body)
            return
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

if __name__ == '__main__':
    httpd = ThreadingHTTPServer(('127.0.0.1', 8810), Handler)
    print('ready http://127.0.0.1:8810', flush=True)
    httpd.serve_forever()
