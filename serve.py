import http.server
import socketserver
import os

PORT = 8000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/app.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def run_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server() 