"""
4 · CON PÉRDIDA — Imágenes: el corazón de JPEG
===============================================

Tubería de JPEG (diapositiva «Imágenes: JPEG»):

  1. BLOQUES 8×8    Divide la foto en cuadritos de 8×8 píxeles.
  2. DCT            Pasa cada bloque a FRECUENCIAS. No pierde nada: solo cambia
                    de "idioma". Arriba-izquierda = cambios suaves (frecuencias
                    bajas); abajo-derecha = detalles finos (frecuencias altas).
  3. CUANTIZACIÓN   Divide cada coeficiente por un número de una tabla y
                    REDONDEA. La tabla tiene números grandes en las frecuencias
                    altas porque el ojo casi no las nota -> casi todo queda en 0.
                    ¡AQUÍ ES DONDE SE PIERDE INFORMACIÓN! (paso irreversible)
  4. HUFFMAN        Recorre el bloque en zigzag (de bajas a altas frecuencias),
                    agrupa las rachas de ceros (RLE) y comprime con Huffman,
                    SIN pérdida.

Fórmula de la DCT-II 2D usada por JPEG (bloque f de 8×8, u,v = 0..7):

    F(u,v) = ¼ C(u) C(v) Σx Σy f(x,y) · cos((2x+1)uπ/16) · cos((2y+1)vπ/16)
    con C(0) = 1/√2 y C(k) = 1 para k > 0.

F(0,0) se llama coeficiente DC (el "promedio" del bloque); los otros 63 son AC.
"""

import math
from collections import Counter

from . import huffman

N = 8

# Tabla de cuantización de LUMINANCIA del estándar JPEG (Anexo K, calidad 50).
# Fíjese cómo crece hacia abajo a la derecha (frecuencias altas).
TABLA_Q50 = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
]

# Precalculamos los cosenos: COS[x][u] = cos((2x+1)uπ/16)
_COS = [[math.cos((2 * x + 1) * u * math.pi / 16) for u in range(N)] for x in range(N)]
_C = [1 / math.sqrt(2)] + [1.0] * (N - 1)


def dct2(bloque):
    """DCT-II 2D de un bloque 8×8 (valores ya centrados en 0: píxel − 128)."""
    F = [[0.0] * N for _ in range(N)]
    for u in range(N):
        for v in range(N):
            s = 0.0
            for x in range(N):
                for y in range(N):
                    s += bloque[x][y] * _COS[x][u] * _COS[y][v]
            F[u][v] = 0.25 * _C[u] * _C[v] * s
    return F


def idct2(F):
    """DCT inversa (DCT-III): vuelve de frecuencias a píxeles."""
    f = [[0.0] * N for _ in range(N)]
    for x in range(N):
        for y in range(N):
            s = 0.0
            for u in range(N):
                for v in range(N):
                    s += _C[u] * _C[v] * F[u][v] * _COS[x][u] * _COS[y][v]
            f[x][y] = 0.25 * s
    return f


def tabla_calidad(calidad):
    """Escala la tabla estándar según la calidad (1-100), igual que libjpeg."""
    calidad = max(1, min(100, calidad))
    escala = 5000 / calidad if calidad < 50 else 200 - 2 * calidad
    return [[max(1, min(255, int((q * escala + 50) // 100))) for q in fila]
            for fila in TABLA_Q50]


def cuantizar(F, Q):
    """El paso con PÉRDIDA: dividir y redondear al entero más cercano."""
    return [[int(round(F[u][v] / Q[u][v])) for v in range(N)] for u in range(N)]


def descuantizar(Fq, Q):
    return [[Fq[u][v] * Q[u][v] for v in range(N)] for u in range(N)]


def orden_zigzag():
    """Posiciones (u,v) en el orden zigzag de JPEG: de bajas a altas frecuencias."""
    return sorted(((u, v) for u in range(N) for v in range(N)),
                  key=lambda p: (p[0] + p[1], p[0] if (p[0] + p[1]) % 2 else p[1]))


ZIGZAG = orden_zigzag()


def simbolos_entropia(Fq, dc_anterior):
    """Convierte un bloque cuantizado en símbolos para Huffman, como JPEG:
       - DC: se guarda la DIFERENCIA con el DC del bloque anterior.
       - AC: pares (ceros_antes, valor) recorriendo en zigzag; 'EOB' (fin de
         bloque) cuando todo lo que queda es 0."""
    secuencia = [Fq[u][v] for u, v in ZIGZAG]
    simbolos = [("DC", secuencia[0] - dc_anterior)]
    ac = secuencia[1:]
    ultimo_no_cero = max((i for i, c in enumerate(ac) if c != 0), default=-1)
    ceros = 0
    for c in ac[:ultimo_no_cero + 1]:
        if c == 0:
            ceros += 1
        else:
            simbolos.append((ceros, c))
            ceros = 0
    simbolos.append("EOB")
    return simbolos, secuencia[0]


def comprimir_imagen(img, calidad):
    """Aplica toda la tubería JPEG (en grises) a una imagen cuyo ancho y alto
    sean múltiplos de 8. Devuelve (imagen_reconstruida, bits_estimados, ceros)."""
    alto, ancho = len(img), len(img[0])
    Q = tabla_calidad(calidad)
    salida = [[0.0] * ancho for _ in range(alto)]
    todos_simbolos = []
    dc_anterior = 0
    ceros = 0
    for by in range(0, alto, N):
        for bx in range(0, ancho, N):
            bloque = [[img[by + i][bx + j] - 128 for j in range(N)] for i in range(N)]
            Fq = cuantizar(dct2(bloque), Q)
            ceros += sum(1 for fila in Fq for c in fila if c == 0)
            simbolos, dc_anterior = simbolos_entropia(Fq, dc_anterior)
            todos_simbolos.extend(simbolos)
            rec = idct2(descuantizar(Fq, Q))
            for i in range(N):
                for j in range(N):
                    salida[by + i][bx + j] = max(0, min(255, rec[i][j] + 128))
    bits, _ = huffman.codificar(todos_simbolos)
    return salida, len(bits), ceros


def psnr(a, b):
    """Peak Signal-to-Noise Ratio en dB: más alto = más parecido (>35 dB ≈ excelente)."""
    mse = sum((a[i][j] - b[i][j]) ** 2 for i in range(len(a)) for j in range(len(a[0])))
    mse /= len(a) * len(a[0])
    return float("inf") if mse == 0 else 10 * math.log10(255 ** 2 / mse)


def imagen_sintetica(tam=64):
    """Imagen de prueba: degradado suave + un círculo + una zona de textura fina."""
    img = []
    for y in range(tam):
        fila = []
        for x in range(tam):
            v = 60 + 120 * x / (tam - 1)                          # degradado
            if (x - 40) ** 2 + (y - 24) ** 2 < 14 ** 2:            # círculo
                v = 230
            if x < 24 and y > 40:                                  # textura fina
                v = 200 if (x + y) % 2 == 0 else 40
            fila.append(v)
        img.append(fila)
    return img


def _imprimir(titulo, M, fmt="%6.0f"):
    print(titulo)
    for fila in M:
        print("   " + " ".join(fmt % v for v in fila))


def demo(carpeta_salida=None):
    print("=" * 70)
    print("4 · CON PÉRDIDA — JPEG: bloques 8×8 -> DCT -> cuantización -> Huffman")
    print("=" * 70)

    # Bloque 8×8 de ejemplo: un degradado suave con un pequeño detalle.
    bloque = [[100 + 6 * x + 3 * y + (12 if (x, y) == (3, 4) else 0)
               for y in range(N)] for x in range(N)]
    _imprimir("\n1) Bloque original (píxeles 0-255):", bloque, "%4d")
    centrado = [[v - 128 for v in fila] for fila in bloque]
    F = dct2(centrado)
    _imprimir("\n2) Tras la DCT (energía concentrada arriba a la izquierda):", F)

    vuelta = idct2(F)
    err = max(abs(vuelta[i][j] + 128 - bloque[i][j]) for i in range(N) for j in range(N))
    print("   La DCT sola no pierde nada: DCT -> DCT inversa, error máximo = %.1e" % err)

    Q = tabla_calidad(50)
    Fq = cuantizar(F, Q)
    _imprimir("\n3) Tras cuantizar con la tabla estándar (calidad 50):", Fq, "%4d")
    ceros = sum(1 for fila in Fq for c in fila if c == 0)
    print("   %d de 64 coeficientes quedaron en 0 (eso se comprime muy bien)" % ceros)

    simbolos, _ = simbolos_entropia(Fq, 0)
    print("\n4) Zigzag + rachas de ceros (lo que entra a Huffman): %s" % simbolos)

    rec = [[round(v + 128) for v in fila] for fila in idct2(descuantizar(Fq, Q))]
    _imprimir("\n   Bloque reconstruido (comparar con el original):", rec, "%4d")
    errores = [abs(rec[i][j] - bloque[i][j]) for i in range(N) for j in range(N)]
    print("   Error máximo por píxel: %d   (se perdió algo, pero el ojo casi no lo nota)"
          % max(errores))

    # --- Imagen completa a distintas calidades ------------------------------
    img = imagen_sintetica()
    bits_original = 64 * 64 * 8
    print("\nImagen sintética 64×64 en grises = %d bits sin comprimir" % bits_original)
    print("  calidad   bits (estim.)   % del original   coef. en 0     PSNR")
    resultados = {}
    for calidad in (90, 50, 10, 2):
        rec_img, bits, ceros = comprimir_imagen(img, calidad)
        resultados[calidad] = rec_img
        print("    %3d       %6d          %5.1f %%        %4d/4096   %5.1f dB"
              % (calidad, bits, 100 * bits / bits_original, ceros, psnr(img, rec_img)))
    print("  -> Menos calidad = más ceros = archivo más pequeño, pero más diferencia.")

    if carpeta_salida:
        import os
        from .imagen_bmp import guardar_bmp_gris
        os.makedirs(carpeta_salida, exist_ok=True)
        guardar_bmp_gris(os.path.join(carpeta_salida, "jpeg_original.bmp"), img, 4)
        for calidad, rec_img in resultados.items():
            guardar_bmp_gris(os.path.join(carpeta_salida, "jpeg_calidad_%02d.bmp" % calidad),
                             rec_img, 4)
        print("  Imágenes guardadas en '%s' (ábralas para comparar a simple vista)."
              % carpeta_salida)


if __name__ == "__main__":
    demo("salidas")
