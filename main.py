import mimetypes
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler


BASE_DIR = Path()


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html_file("index.html")
            case "/message.html":
                self.send_html_file("message.html")
            case "/":
                self.send_html_file("index.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file("error.html", 404)

    def do_POST(self):
        pass

    def send_html_file(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())


def run_server():
    server_address = ('localhost', 3000)
    http_server = HTTPServer(server_address, HttpHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == '__main__':
    run_server()
