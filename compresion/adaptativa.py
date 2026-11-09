"""
2 · CLASIFICACIÓN — ¿Cuándo aprende el modelo? Estática vs. adaptativa
=======================================================================

ESTÁTICA (modelo fijo, DOS pasadas):
    1. Lee todo el archivo   2. Cuenta frecuencias y arma la tabla
    3. Codifica todo con la misma tabla   4. Guarda tabla + datos
    -> La tabla viaja junto con el archivo comprimido.
    -> Un símbolo siempre cuesta lo mismo, esté al principio o al final.
    Ejemplo: Huffman clásico (huffman.py).

ADAPTATIVA (aprende mientras lee, UNA pasada):
    Lee un símbolo -> lo codifica con la tabla ACTUAL -> actualiza la tabla
    ↺ se repite con cada símbolo. El decodificador hace las mismas
    actualizaciones, así que NO hace falta enviar la tabla.
    Ejemplo: Lempel-Ziv (lz77.py, lzw.py), Huffman adaptativo, CABAC.

Ojo: «basada en contexto» es OTRA idea: predecir según lo que vino antes
(puede ser estática o adaptativa).

En este módulo medimos el COSTO IDEAL en bits (−log2 p, lo que lograría un
codificador aritmético perfecto) de cada modelo, para comparar de forma justa.
"""

import math
from collections import Counter, deque


def costo_estatico(texto):
    """Bits = Σ −log2 p(x) con p fijas calculadas sobre TODO el texto,
    más el costo de enviar la tabla (aprox. 8 bits por símbolo + 8 por conteo)."""
    conteos = Counter(texto)
    n = len(texto)
    datos = sum(-math.log2(conteos[s] / n) for s in texto)
    tabla = len(conteos) * 16
    return datos, tabla


def costo_adaptativo(texto, alfabeto, memoria=None, detalle=None):
    """Bits = Σ −log2 p(x) donde p se calcula SOLO con lo leído hasta ahora.

    * Empieza sabiendo nada: todos los símbolos con conteo 1 (suavizado de
      Laplace, para que ninguno tenga probabilidad 0).
    * Tras codificar un símbolo, se suma 1 a su conteo.
    * `memoria` (opcional): solo recuerda los últimos `memoria` símbolos
      (ventana deslizante). Así se adapta rápido si el contenido CAMBIA.
    """
    conteos = {s: 1 for s in alfabeto}
    total = len(alfabeto)
    recientes = deque()
    bits = 0.0
    for i, s in enumerate(texto):
        p = conteos[s] / total
        costo = -math.log2(p)
        bits += costo
        if detalle is not None:
            detalle.append((i, s, p, costo))
        # Actualizar el modelo DESPUÉS de codificar (el decodificador hará lo mismo)
        conteos[s] += 1
        total += 1
        if memoria is not None:
            recientes.append(s)
            if len(recientes) > memoria:
                viejo = recientes.popleft()
                conteos[viejo] -= 1
                total -= 1
    return bits


def demo():
    print("=" * 70)
    print("2 · CLASIFICACIÓN — Estática (dos pasadas) vs. adaptativa (una pasada)")
    print("=" * 70)

    # Un texto cuyo comportamiento CAMBIA a mitad de camino.
    texto = "A" * 50 + "B" * 50
    alfabeto = "AB"
    datos_e, tabla_e = costo_estatico(texto)
    detalle = []
    adapt = costo_adaptativo(texto, alfabeto, detalle=detalle)
    adapt_vent = costo_adaptativo(texto, alfabeto, memoria=8)

    print("\nTexto: 50 'A' seguidas de 50 'B' (el contenido cambia a la mitad)")
    print("  Estática:   p(A)=p(B)=0.5 fijas -> %.1f bits de datos + %d bits de tabla = %.1f"
          % (datos_e, tabla_e, datos_e + tabla_e))
    print("  Adaptativa (recuerda todo):          %.1f bits, sin tabla" % adapt)
    print("  Adaptativa (recuerda los últimos 8): %.1f bits, sin tabla" % adapt_vent)

    print("\nCómo cambia el costo de cada símbolo en el modelo adaptativo:")
    for i, s, p, c in detalle:
        if i in (0, 1, 2, 10, 49, 50, 51, 60, 99):
            print("   posición %2d  lee %s  p(%s)=%.3f  -> cuesta %.2f bits" % (i, s, s, p, c))
    print("  -> Al principio no sabe nada (1 bit); a medida que ve muchas 'A',")
    print("     codificar 'A' se vuelve casi gratis. Cuando aparecen las 'B' le")
    print("     cuestan caro al inicio, pero el modelo aprende y se abaratan.")

    texto2 = "ABRACADABRA" * 3
    d2, t2 = costo_estatico(texto2)
    print("\nTexto estable %r (33 letras):" % "ABRACADABRA×3")
    print("  Estática:   %.1f + tabla %d = %.1f bits" % (d2, t2, d2 + t2))
    print("  Adaptativa: %.1f bits" % costo_adaptativo(texto2, "ABCDR"))
    print("Conclusión: la adaptativa no envía tabla y reacciona a los cambios;")
    print("la estática es más simple y sirve cuando los datos son homogéneos.")


if __name__ == "__main__":
    demo()
