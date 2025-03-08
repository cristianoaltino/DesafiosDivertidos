import http.server
import socketserver
import os
import urllib.parse
import subprocess
import argparse

class WebserverHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        action = next((func for key, func in {
            "file=": self.handle_file_leak,
            "cmd=": self.execute_command
        }.items() if key in self.path), super().do_GET)
        action()

    def handle_file_leak(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        file_path = params.get("file", [None])[0]
        if not file_path:
            return self.send_error(400, "Parâmetro 'file' ausente")
        try:
            with open(file_path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404, f"Arquivo não encontrado: {file_path}")
        except Exception as e:
            self.send_error(500, f"Erro interno: {str(e)}")

    def execute_command(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        command = params.get("cmd", [None])[0]
        if not command:
            return self.send_error(400, "Parâmetro 'cmd' ausente")
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(output)
        except subprocess.CalledProcessError as e:
            self.send_error(500, f"Erro ao executar comando: {e}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Servidor HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor (padrão: 8000)")
    parser.add_argument("--directory", type=str, default='./', help="Diretório raiz do servidor (padrão: ./)")
    args = parser.parse_args()
    if not os.path.isdir(args.directory):
        parser.error(f"O diretório especificado '{args.directory}' não existe ou não é um diretório válido.")
    return args

args = parse_arguments()

with socketserver.TCPServer(("", args.port), WebserverHandler) as httpd:
    print(f"Servidor rodando em http://localhost:{args.port}")
    print("Encontre a(s) vulnerabilidade(s)!")
    httpd.serve_forever()

