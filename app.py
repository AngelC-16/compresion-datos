"""
INTERFAZ VISUAL — «¿Cómo cabe todo? Compresión de datos»

    python app.py

Levanta un pequeño servidor web LOCAL (solo en este computador) y abre el
navegador. La página (carpeta web/) dibuja paso a paso lo que hace cada
algoritmo; los cálculos los hace el MISMO código Python de la carpeta
compresion/ (a través de compresion/api.py).

No necesita internet ni instalar nada: usa solo la librería estándar.
Para detenerlo: Ctrl + C en la terminal.
"""

import json
import os
import sys
import threading
import traceback
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from compresion.api import RUTAS

CARPETA_WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PUERTO = int(os.environ.get("PUERTO", "8000"))


class Manejador(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CARPETA_WEB, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        """POST /api/<seccion> con un JSON de parámetros -> JSON de resultados."""
        nombre = self.path.rstrip("/").split("/")[-1]
        funcion = RUTAS.get(nombre)
        if not self.path.startswith("/api/") or funcion is None:
            return self._json({"error": "ruta desconocida"}, 404)
        try:
            largo = int(self.headers.get("Content-Length", 0))
            parametros = json.loads(self.rfile.read(largo) or b"{}")
            return self._json(funcion(parametros))
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        except Exception as e:                       # mostrar el error en la página
            traceback.print_exc()
            return self._json({"error": "%s: %s" % (type(e).__name__, e)}, 500)

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *args):
        pass                                          # consola limpia


class Servidor(ThreadingHTTPServer):
    # En Windows, "reutilizar dirección" deja que DOS programas usen el mismo
    # puerto a la vez (y el navegador termina hablando con el equivocado).
    # Lo desactivamos para que, si el puerto está ocupado, se use el siguiente.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def abrir_navegador(url):
    """Abre el navegador; si `webbrowser` falla, usa el método de Windows."""
    try:
        if webbrowser.open(url):
            return
    except Exception:
        pass
    if os.name == "nt":
        try:
            os.startfile(url)
        except OSError:
            pass


def main():
    try:                                              # tildes bien en la consola de Windows
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    servidor = None
    for puerto in range(PUERTO, PUERTO + 20):        # si el puerto está ocupado, prueba el siguiente
        try:
            servidor = Servidor(("127.0.0.1", puerto), Manejador)
            break
        except OSError:
            continue
    if servidor is None:
        print("No se encontró un puerto libre.")
        return 1
    url = "http://127.0.0.1:%d/" % servidor.server_address[1]
    print("=" * 64)
    print("  INTERFAZ VISUAL LISTA")
    print("  Abra en el navegador:  %s" % url)
    print("  (Se abre sola; si no, copie esa dirección en Chrome o Edge.)")
    print("  NO cierre esta ventana mientras la usa. Para salir: Ctrl + C")
    print("=" * 64, flush=True)
    if "--sin-navegador" not in sys.argv:
        threading.Timer(0.6, abrir_navegador, args=(url,)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
