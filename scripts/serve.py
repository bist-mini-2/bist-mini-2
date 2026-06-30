import http.server
import os
import sys

PORT = 3000
DIRECTORY = "frontend/dist"

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def translate_path(self, path):
        translated = super().translate_path(path)
        
        # 디렉토리가 있더라도 동일 이름의 .html 파일이 루트에 있으면 해당 파일을 우선 서비스합니다.
        # 예: /bist-mini-2/join 또는 /bist-mini-2/join/ -> /bist-mini-2/join.html
        normalized_path = translated.rstrip('/')
        if not normalized_path.endswith('.html'):
            html_path = normalized_path + '.html'
            if os.path.exists(html_path) and os.path.isfile(html_path):
                return html_path
                
        return translated

if __name__ == '__main__':
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, CleanURLHandler)
    print(f"Serving Clean URLs on port {PORT}...")
    httpd.serve_forever()
