"""
3 · SIN PÉRDIDA — Codificación aritmética
==========================================

Todo el mensaje se convierte en UN SOLO NÚMERO dentro de un intervalo [0, 1).

  1. Se parte del intervalo [0, 1).
  2. Se divide en tramos proporcionales a la probabilidad de cada símbolo:
        A = 50 %  -> [0.00, 0.50)
        B = 25 %  -> [0.50, 0.75)
        C = 25 %  -> [0.75, 1.00)
  3. Al leer un símbolo se hace "zoom" dentro de su tramo, y ese tramo se
     vuelve a dividir en las mismas proporciones (AA, AB, AC ... ).
  4. Al terminar queda un intervalo pequeñito: cualquier número dentro de él
     identifica el mensaje. Se elige el que tenga MENOS dígitos binarios.

Ancho final del intervalo = producto de las probabilidades de los símbolos
=> bits necesarios ≈ −log2(ancho) = Σ −log2 p(x)  -> ¡exactamente la entropía!

Ventaja sobre Huffman: Huffman usa un número ENTERO de bits por símbolo (al
menos 1). La aritmética usa "fracciones de bit", así que se acerca más al
límite de Shannon. Se usa en JPEG2000 y en H.264 (CABAC).

Esta implementación es didáctica: usa `Fraction` (fracciones exactas) para que
se vea la matemática sin errores de redondeo. Las implementaciones reales usan
enteros de precisión fija y van emitiendo bits a medida que avanzan.
"""

import math
from collections import Counter
from fractions import Fraction


def modelo(texto):
    """Tramos acumulados: {símbolo: (inicio, fin)} con fracciones exactas."""
    conteos = Counter(texto)
    total = len(texto)
    tramos = {}
    acumulado = Fraction(0)
    for s in sorted(conteos):
        p = Fraction(conteos[s], total)
        tramos[s] = (acumulado, acumulado + p)
        acumulado += p
    return tramos


def codificar(texto, tramos=None, traza=None):
    """Devuelve (bits, tramos). `bits` es un string de '0'/'1' que representa
    el número binario 0.b1b2b3... que cae dentro del intervalo final."""
    if tramos is None:
        tramos = modelo(texto)
    bajo, alto = Fraction(0), Fraction(1)
    for s in texto:
        ancho = alto - bajo
        ini, fin = tramos[s]
        bajo, alto = bajo + ancho * ini, bajo + ancho * fin     # zoom
        if traza is not None:
            traza.append((s, bajo, alto))
    return _binario_mas_corto(bajo, alto), tramos


def _binario_mas_corto(bajo, alto):
    """Busca la fracción binaria con menos bits k tal que bajo <= m/2^k < alto."""
    k = 0
    while True:
        k += 1
        m = math.ceil(bajo * 2 ** k)          # el menor múltiplo de 1/2^k >= bajo
        if Fraction(m, 2 ** k) < alto:
            return format(m, "0%db" % k) if m > 0 else "0" * k


def decodificar(bits, tramos, n):
    """Reconstruye n símbolos: ver en qué tramo cae el número y hacer zoom."""
    x = Fraction(int(bits, 2), 2 ** len(bits)) if bits else Fraction(0)
    salida = []
    bajo, alto = Fraction(0), Fraction(1)
    for _ in range(n):
        ancho = alto - bajo
        pos = (x - bajo) / ancho              # dónde cae x dentro del intervalo
        for s, (ini, fin) in tramos.items():
            if ini <= pos < fin:
                salida.append(s)
                bajo, alto = bajo + ancho * ini, bajo + ancho * fin
                break
    return "".join(salida)


def demo():
    print("=" * 70)
    print("3 · SIN PÉRDIDA — Codificación aritmética: un mensaje = un número")
    print("=" * 70)

    texto = "AABAC"
    tramos = modelo(texto)
    print("\nMensaje: %s" % texto)
    print("Tramos iniciales:")
    for s, (a, b) in tramos.items():
        print("   %s -> [%s, %s)   (p = %s)" % (s, a, b, b - a))
    traza = []
    bits, _ = codificar(texto, tramos, traza)
    print("\nZoom símbolo a símbolo:")
    for s, a, b in traza:
        print("   lee %s -> [%-8s, %-8s)  ancho = %s ≈ %.5f" % (s, a, b, b - a, float(b - a)))
    print("\nNúmero elegido: 0.%s (binario) = %s" % (bits, Fraction(int(bits, 2), 2 ** len(bits))))
    print("Bits usados: %d   decodificado: %s"
          % (len(bits), decodificar(bits, tramos, len(texto))))

    # Donde la aritmética le gana a Huffman: probabilidades muy desiguales.
    sesgado = "AAAAAAAAABAAAAAAAAAB"        # 90 % A, 10 % B (moneda cargada)
    bits2, tramos2 = codificar(sesgado)
    from .entropia import entropia
    print("\nMoneda cargada (90 %% A / 10 %% B), %d símbolos:" % len(sesgado))
    print("   límite de Shannon:  %.1f bits  (%.2f bits/símbolo)"
          % (entropia(sesgado) * len(sesgado), entropia(sesgado)))
    print("   Huffman:            %d bits  (mínimo 1 bit por símbolo, ¡no puede bajar de ahí!)"
          % len(sesgado))
    print("   Aritmética:         %d bits  (usa fracciones de bit)" % len(bits2))
    print("   ¿Decodifica bien?   %s" % (decodificar(bits2, tramos2, len(sesgado)) == sesgado))


if __name__ == "__main__":
    demo()
