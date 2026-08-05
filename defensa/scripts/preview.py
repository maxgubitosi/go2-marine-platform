"""Servidor local para previsualizar el deck, sin cache y con subida.

El no-cache es lo importante: sin el, el navegador se queda con el CSS y el HTML
viejos entre iteracion e iteracion, y uno termina revisando una version que ya no
existe. Pasa seguido y es dificil de notar.

El POST existe por un caso puntual, que es rasterizar las escenas de oleaje
animadas para la version PowerPoint. En esta maquina no hay ningun rasterizador
de SVG (ni rsvg-convert, ni qlmanage, ni LibreOffice sirven), asi que la unica
forma es dibujarlas en un canvas del navegador. Este endpoint deja que la pagina
escriba el resultado a disco directamente.

Uso:
    python3 defensa/scripts/preview.py [puerto]     # desde la raiz del repo

Despues abrir http://localhost:8771

POST /__save?path=img/escenas/foo.jpg con el binario en el cuerpo. Solo escribe
dentro de assets/, para que tener el servidor levantado no habilite escribir en
cualquier lado del disco.
"""

import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8771

# Se sirve defensa/web/ sin importar desde donde se invoque el script.
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")
WEB = os.path.realpath(WEB)
ASSETS = os.path.join(WEB, "assets")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/__save":
            self.send_error(404)
            return
        rel = (parse_qs(url.query).get("path") or [""])[0]
        destino = os.path.realpath(os.path.join(ASSETS, rel))
        if not destino.startswith(ASSETS + os.sep):
            self.send_error(403, "fuera de assets/")
            return
        datos = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "wb") as f:
            f.write(datos)
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"{rel} {len(datos)}".encode())

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Sirviendo {WEB} en http://localhost:{PUERTO}")
    ThreadingHTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
