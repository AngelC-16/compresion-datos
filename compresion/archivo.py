"""
5 · APLICACIONES — Compresor REAL de archivos (el «ejemplo práctico»)
======================================================================

Comprime y descomprime cualquier archivo con dos métodos implementados aquí:

  huffman   Huffman canónico sobre los bytes del archivo.
  deflate   «Mini-DEFLATE»: LZ77 (ventana deslizante + tabla hash) y luego
            Huffman canónico sobre los tokens. Es la MISMA idea que ZIP, gzip
            y PNG (LZ77 + Huffman = DEFLATE), simplificada.

y compara el resultado con los compresores profesionales que trae Python:
    zlib (DEFLATE real) · bz2 (BWT, como bzip2) · lzma (LZ77 avanzado + aritmética, .xz/.7z)

Uso desde la terminal:
    python -m compresion.archivo comprimir   entrada.txt  salida.edd [huffman|deflate]
    python -m compresion.archivo descomprimir salida.edd   recuperado.txt
    python -m compresion.archivo comparar    entrada.txt

FORMATO DEL ARCHIVO .edd (todo lo necesario para descomprimir):
    4 bytes  "EDD2"                  firma ("número mágico")
    1 byte   método (1 = huffman, 2 = deflate)
    4 bytes  tamaño original (entero sin signo, little-endian)
    k bytes  longitudes de los códigos canónicos (1 byte por símbolo del
             alfabeto: 256 en huffman, 513 en deflate). Gracias a los
             códigos CANÓNICOS no hay que guardar el árbol: basta esto.
    resto    los bits de datos, empaquetados en bytes
"""

import bz2
import lzma
import os
import struct
import sys
import time
import zlib
from collections import Counter

from . import huffman, lz77, rle

FIRMA = b"EDD2"
METODO_HUFFMAN = 1
METODO_DEFLATE = 2

# Alfabeto del mini-DEFLATE:
#   0..255   -> literal (un byte tal cual)
#   256..511 -> referencia LZ77 con longitud = símbolo − 256 + 3  (3..258)
#   512      -> (sin usar; reservado para "fin de bloque")
# La distancia de cada referencia se escribe aparte con 15 bits fijos (1..32768).
TAM_ALFABETO_DEFLATE = 513
BITS_DISTANCIA = 15


# ---------------------------------------------------------------------------
# Escritura y lectura de BITS (los archivos se guardan en bytes de 8 bits)
# ---------------------------------------------------------------------------
class EscritorBits:
    def __init__(self):
        self.bytes = bytearray()
        self._acum = 0          # bits pendientes (como entero)
        self._n = 0             # cuántos bits pendientes hay

    def escribir(self, valor, cantidad_bits):
        """Agrega los `cantidad_bits` bits menos significativos de `valor`."""
        self._acum = (self._acum << cantidad_bits) | valor
        self._n += cantidad_bits
        while self._n >= 8:
            self._n -= 8
            self.bytes.append((self._acum >> self._n) & 0xFF)
        self._acum &= (1 << self._n) - 1

    def terminar(self):
        """Rellena con ceros el último byte incompleto."""
        if self._n:
            self.bytes.append((self._acum << (8 - self._n)) & 0xFF)
            self._acum = self._n = 0
        return bytes(self.bytes)


class LectorBits:
    def __init__(self, datos):
        self.datos = datos
        self.pos = 0            # posición en bits

    def leer_bit(self):
        byte = self.datos[self.pos >> 3]
        bit = (byte >> (7 - (self.pos & 7))) & 1
        self.pos += 1
        return bit

    def leer(self, cantidad_bits):
        valor = 0
        for _ in range(cantidad_bits):
            valor = (valor << 1) | self.leer_bit()
        return valor


# ---------------------------------------------------------------------------
# Huffman canónico con enteros (más rápido que con strings)
# ---------------------------------------------------------------------------
def _longitudes(frecuencias, tam_alfabeto):
    """Longitud del código de cada símbolo (0 = el símbolo no aparece)."""
    longitudes = [0] * tam_alfabeto
    if not frecuencias:
        return longitudes
    raiz = huffman.construir_arbol(frecuencias)
    for simbolo, codigo in huffman.generar_codigos(raiz).items():
        longitudes[simbolo] = len(codigo)
    return longitudes


def _tabla_codificacion(longitudes):
    """{símbolo: (código_entero, longitud)} usando la regla canónica."""
    presentes = {s: l for s, l in enumerate(longitudes) if l > 0}
    if not presentes:
        return {}
    canon = huffman.codigos_canonicos(presentes)
    return {s: (int(c, 2), len(c)) for s, c in canon.items()}


def _tabla_decodificacion(longitudes):
    """{(longitud, código_entero): símbolo}: al leer bits, vamos armando
    (longitud, valor) y consultamos esta TABLA HASH en O(1)."""
    return {(l, c): s for s, (c, l) in _tabla_codificacion(longitudes).items()}


def _leer_simbolo(lector, tabla_dec):
    codigo = longitud = 0
    while True:
        codigo = (codigo << 1) | lector.leer_bit()
        longitud += 1
        if (longitud, codigo) in tabla_dec:
            return tabla_dec[(longitud, codigo)]
        if longitud > 600:
            raise ValueError("archivo corrupto")


# ---------------------------------------------------------------------------
# Método 1: Huffman sobre bytes
# ---------------------------------------------------------------------------
def comprimir_huffman(datos: bytes) -> bytes:
    longitudes = _longitudes(Counter(datos), 256)
    tabla = _tabla_codificacion(longitudes)
    w = EscritorBits()
    for b in datos:
        codigo, l = tabla[b]
        w.escribir(codigo, l)
    cabecera = FIRMA + struct.pack("<BI", METODO_HUFFMAN, len(datos)) + bytes(longitudes)
    return cabecera + w.terminar()


def _descomprimir_huffman(cuerpo, tamano):
    longitudes = list(cuerpo[:256])
    tabla_dec = _tabla_decodificacion(longitudes)
    lector = LectorBits(cuerpo[256:])
    return bytes(_leer_simbolo(lector, tabla_dec) for _ in range(tamano))


# ---------------------------------------------------------------------------
# Método 2: mini-DEFLATE = LZ77 + Huffman
# ---------------------------------------------------------------------------
def comprimir_deflate(datos: bytes) -> bytes:
    tokens = lz77.codificar(datos)
    simbolos = [t[1] if t[0] == "L" else 256 + t[2] - 3 for t in tokens]
    longitudes = _longitudes(Counter(simbolos), TAM_ALFABETO_DEFLATE)
    tabla = _tabla_codificacion(longitudes)
    w = EscritorBits()
    for t, s in zip(tokens, simbolos):
        codigo, l = tabla[s]
        w.escribir(codigo, l)
        if t[0] == "R":
            w.escribir(t[1] - 1, BITS_DISTANCIA)
    cabecera = FIRMA + struct.pack("<BI", METODO_DEFLATE, len(datos)) + bytes(longitudes)
    return cabecera + w.terminar()


def _descomprimir_deflate(cuerpo, tamano):
    longitudes = list(cuerpo[:TAM_ALFABETO_DEFLATE])
    tabla_dec = _tabla_decodificacion(longitudes)
    lector = LectorBits(cuerpo[TAM_ALFABETO_DEFLATE:])
    salida = bytearray()
    while len(salida) < tamano:
        s = _leer_simbolo(lector, tabla_dec)
        if s < 256:
            salida.append(s)
        else:
            longitud = s - 256 + 3
            distancia = lector.leer(BITS_DISTANCIA) + 1
            inicio = len(salida) - distancia
            for k in range(longitud):
                salida.append(salida[inicio + k])
    return bytes(salida)


# ---------------------------------------------------------------------------
# API general
# ---------------------------------------------------------------------------
def comprimir(datos: bytes, metodo="deflate") -> bytes:
    if metodo == "huffman":
        return comprimir_huffman(datos)
    if metodo == "deflate":
        return comprimir_deflate(datos)
    raise ValueError("método desconocido: %s" % metodo)


def descomprimir(comprimido: bytes) -> bytes:
    if comprimido[:4] != FIRMA:
        raise ValueError("no es un archivo .edd (firma incorrecta)")
    metodo, tamano = struct.unpack("<BI", comprimido[4:9])
    cuerpo = comprimido[9:]
    if metodo == METODO_HUFFMAN:
        return _descomprimir_huffman(cuerpo, tamano)
    if metodo == METODO_DEFLATE:
        return _descomprimir_deflate(cuerpo, tamano)
    raise ValueError("método desconocido en la cabecera: %d" % metodo)


def comparar(datos: bytes, nombre="datos"):
    """Tabla comparativa: nuestros métodos vs. los profesionales."""
    from .entropia import entropia
    print("\nArchivo: %s  (%d bytes)" % (nombre, len(datos)))
    if datos:
        h = entropia(datos)
        print("Entropía (orden 0): %.3f bits/byte -> límite para un compresor que solo"
              " mira frecuencias de bytes: %d bytes" % (h, int(len(datos) * h / 8)))
    print("\n  %-34s %10s %9s %9s  %s" % ("método", "bytes", "% orig.", "tiempo", "¿idéntico?"))
    filas = [
        ("RLE por bytes (nuestro)", rle.codificar_bytes, rle.decodificar_bytes),
        ("Huffman (nuestro)", comprimir_huffman, descomprimir),
        ("mini-DEFLATE LZ77+Huffman (nuestro)", comprimir_deflate, descomprimir),
        ("zlib nivel 9 (DEFLATE real)", lambda d: zlib.compress(d, 9), zlib.decompress),
        ("bz2 (BWT + Huffman)", lambda d: bz2.compress(d, 9), bz2.decompress),
        ("lzma / xz (LZ77 + aritmética)", lambda d: lzma.compress(d, preset=9), lzma.decompress),
    ]
    resultados = []
    for etiqueta, comp, desc in filas:
        t0 = time.perf_counter()
        c = comp(datos)
        t = time.perf_counter() - t0
        ok = desc(c) == datos
        pct = 100 * len(c) / len(datos) if datos else 0
        resultados.append((etiqueta, len(c), pct, t, ok))
        print("  %-34s %10d %8.1f%% %8.3fs  %s" % (etiqueta, len(c), pct, t, "sí" if ok else "NO"))
    return resultados


def demo(ruta=None):
    print("=" * 70)
    print("5 · APLICACIONES — Compresor real de archivos y comparación")
    print("=" * 70)
    if ruta is None:
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ejemplos", "guion.txt")
    with open(ruta, "rb") as f:
        datos = f.read()
    comparar(datos, os.path.basename(ruta))
    print("\nLectura de la tabla:")
    print("  * RLE casi siempre AGRANDA un texto normal (no hay rachas): «la trampa».")
    print("  * Huffman solo aprovecha que unas letras son más comunes que otras.")
    print("  * LZ77 + Huffman además aprovecha palabras y frases repetidas.")
    print("  * Los profesionales ganan con mejores búsquedas, códigos de distancia,")
    print("    bloques y (en lzma) codificación aritmética con contexto.")


def _main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    orden = argv[1]
    if orden == "comprimir" and len(argv) >= 4:
        metodo = argv[4] if len(argv) > 4 else "deflate"
        with open(argv[2], "rb") as f:
            datos = f.read()
        c = comprimir(datos, metodo)
        with open(argv[3], "wb") as f:
            f.write(c)
        print("%s: %d -> %d bytes (%.1f %%) con %s"
              % (argv[2], len(datos), len(c), 100 * len(c) / max(1, len(datos)), metodo))
    elif orden == "descomprimir" and len(argv) >= 4:
        with open(argv[2], "rb") as f:
            d = descomprimir(f.read())
        with open(argv[3], "wb") as f:
            f.write(d)
        print("%s -> %s (%d bytes)" % (argv[2], argv[3], len(d)))
    elif orden == "comparar" and len(argv) >= 3:
        with open(argv[2], "rb") as f:
            comparar(f.read(), argv[2])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv))
