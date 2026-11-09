"""
Utilidad: guardar una matriz de grises (0-255) como archivo .BMP de 8 bits,
sin librerías externas, para poder VER el efecto de la compresión JPEG.

Formato BMP (resumen): cabecera de archivo (14 bytes) + cabecera de imagen
(40 bytes) + paleta de 256 grises (1024 bytes) + filas de píxeles de abajo
hacia arriba, cada fila rellenada hasta un múltiplo de 4 bytes.
"""

import struct


def guardar_bmp_gris(ruta, matriz, escala=1):
    """`escala` amplía cada píxel a un cuadro de escala×escala (para verla grande
    sin suavizar, y así notar los bloques 8×8 de JPEG)."""
    if escala > 1:
        matriz = [[v for v in fila for _ in range(escala)]
                  for fila in matriz for _ in range(escala)]
    alto = len(matriz)
    ancho = len(matriz[0])
    relleno = (4 - ancho % 4) % 4
    tam_pixeles = (ancho + relleno) * alto
    desplazamiento = 14 + 40 + 1024
    with open(ruta, "wb") as f:
        f.write(b"BM")
        f.write(struct.pack("<IHHI", desplazamiento + tam_pixeles, 0, 0, desplazamiento))
        f.write(struct.pack("<IiiHHIIiiII", 40, ancho, alto, 1, 8, 0, tam_pixeles,
                            2835, 2835, 256, 0))
        for g in range(256):
            f.write(bytes([g, g, g, 0]))
        for fila in reversed(matriz):
            f.write(bytes(max(0, min(255, int(round(v)))) for v in fila))
            f.write(b"\x00" * relleno)
