"""
EJEMPLO PRÁCTICO — «¿Cómo cabe todo? Compresión de datos»
Universidad del Norte · Estructuras de Datos II
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

Ejecuta las demostraciones en el MISMO ORDEN de la presentación.

    python demo.py            -> menú interactivo
    python demo.py todo       -> todas las secciones seguidas
    python demo.py huffman    -> solo una sección (ver nombres abajo)

No necesita instalar nada: solo Python 3.8 o superior.
"""

import os
import sys

# En Windows la consola a veces no usa UTF-8: lo forzamos para ver tildes y dibujos.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from compresion import (adaptativa, archivo, aritmetica, audio, bwt, entropia,
                        estructuras, huffman, jpeg_dct, lz77, lzw, rle, video)

SALIDAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salidas")

# (clave, título, función) en el orden de la presentación
SECCIONES = [
    ("entropia",     "1 · Contexto: entropía de Shannon",                 entropia.demo),
    ("adaptativa",   "2 · Clasificación: estática vs. adaptativa",        adaptativa.demo),
    ("rle",          "3 · Sin pérdida: RLE",                              rle.demo),
    ("heap",         "5 · Estructura: cola de prioridad (min-heap)",       estructuras.demo),
    ("huffman",      "3 · Sin pérdida: Huffman",                          huffman.demo),
    ("lz77",         "3 · Sin pérdida: LZ77 (ventana + tabla hash)",       lz77.demo),
    ("lzw",          "3 · Sin pérdida: LZW (diccionario)",                lzw.demo),
    ("bwt",          "3 · Sin pérdida: Burrows-Wheeler",                  bwt.demo),
    ("aritmetica",   "3 · Sin pérdida: codificación aritmética",          aritmetica.demo),
    ("jpeg",         "4 · Con pérdida: imágenes (JPEG / DCT)",            lambda: jpeg_dct.demo(SALIDAS)),
    ("audio",        "4 · Con pérdida: audio (psicoacústica)",            lambda: audio.demo(SALIDAS)),
    ("video",        "4 · Con pérdida: video (cuadros I/P)",              video.demo),
    ("archivo",      "5 · Aplicaciones: compresor real de archivos",      archivo.demo),
]


def ejecutar(clave):
    for k, _, funcion in SECCIONES:
        if k == clave:
            funcion()
            print()
            return True
    return False


def menu():
    while True:
        print("\n¿CÓMO CABE TODO? — Ejemplo práctico de compresión de datos")
        print("-" * 60)
        for i, (_, titulo, _) in enumerate(SECCIONES, 1):
            print("  %2d. %s" % (i, titulo))
        print("   T. Todo seguido        0. Salir")
        opcion = input("Elija una opción: ").strip().lower()
        if opcion in ("0", "q", "salir", ""):
            break
        if opcion == "t":
            for k, _, _ in SECCIONES:
                ejecutar(k)
        elif opcion.isdigit() and 1 <= int(opcion) <= len(SECCIONES):
            ejecutar(SECCIONES[int(opcion) - 1][0])
        else:
            print("Opción no válida.")
            continue
        input("\n[Enter para volver al menú]")


def main(argv):
    if len(argv) == 1:
        menu()
    elif argv[1] == "todo":
        for k, _, _ in SECCIONES:
            ejecutar(k)
    elif not ejecutar(argv[1]):
        print("Sección desconocida. Opciones: todo, " + ", ".join(k for k, _, _ in SECCIONES))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
