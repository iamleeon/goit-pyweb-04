import json
import logging
import mimetypes
import socket
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread


BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = 'localhost'
SOCKET_PORT = 5000
DATA_FILE = 'storage/data.json'


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html_file('index.html')
            case '/message.html':
                self.send_html_file('message.html')
            case '/':
                self.send_html_file('index.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/message.html')
        self.end_headers()

    def send_html_file(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-type', mime_type)
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def send_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        if Path(DATA_FILE).exists():
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        else:
            existing_data = {}
        data_received_at = str(datetime.now())
        existing_data[data_received_at] = parse_dict
        with open(DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
    except ValueError as e:
        logging.error(e)
    except OSError as e:
        logging.error(e)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting UDP socket server")
    try:
        while True:
            message, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {message} ")
            send_data_from_form(message)
    except KeyboardInterrupt:
        server_socket.close()
    finally:
        server_socket.close()


def run_http_server(host, port):
    server_address = (host, port)
    http_server = HTTPServer(server_address, HttpHandler)
    try:
        logging.info("Starting HTTP socket server")
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')
    server_http = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server_http.start()
    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
