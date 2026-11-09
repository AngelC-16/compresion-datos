"""
1 · CONTEXTO — Entropía de Shannon (Claude Shannon, 1948)
==========================================================

Fórmula de la diapositiva:

        H = − Σ p(x) · log2 p(x)

  * p(x)        = probabilidad (frecuencia relativa) del símbolo x.
  * −log2 p(x)  = "información" o "sorpresa" de ver x, medida en bits.
                  Si algo es muy probable, sorprende poco => pocos bits.
  * H           = promedio ponderado de esa sorpresa = mínimo número
                  promedio de bits por símbolo para guardar el mensaje
                  SIN perder nada (límite teórico de la compresión sin pérdida).

Ningún compresor sin pérdida puede, en promedio, bajar de H bits por símbolo
(para una fuente que se comporte como dice el modelo). Es la "naranja exprimida":
llega un punto en que ya no sale más jugo.

Redundancia = lo que sobra = (bits que usamos) − (bits que realmente hacen falta).
"""

import math
from collections import Counter


def frecuencias(datos):
    """Cuenta cuántas veces aparece cada símbolo.

    `Counter` es internamente una TABLA HASH (diccionario de Python): cada
    actualización cuesta O(1) en promedio, así que contar todo cuesta O(n).
    """
    return Counter(datos)


def probabilidades(datos):
    """Convierte las frecuencias en probabilidades p(x) = veces(x) / total."""
    total = len(datos)
    return {simbolo: veces / total for simbolo, veces in frecuencias(datos).items()}


def entropia_de_distribucion(probs):
    """H = −Σ p·log2(p) para una lista/diccionario de probabilidades.

    Los términos con p = 0 se omiten (por convención 0·log2(0) = 0).
    """
    valores = probs.values() if isinstance(probs, dict) else probs
    h = -sum(p * math.log2(p) for p in valores if p > 0)
    return h if h > 0 else 0.0           # evita mostrar "-0.000"


def entropia(datos):
    """Entropía (bits por símbolo) de una secuencia concreta de datos."""
    if not datos:
        return 0.0
    return entropia_de_distribucion(probabilidades(datos))


def informacion(p):
    """Información (sorpresa) en bits de un evento de probabilidad p: −log2 p."""
    return -math.log2(p)


def analisis(datos, bits_por_simbolo_original=8):
    """Resume cuánto se podría comprimir `datos` como máximo (sin pérdida),
    usando un modelo que solo mira la frecuencia de cada símbolo.

    Devuelve un diccionario con:
      - bits_originales:  tamaño con un código fijo (p. ej. ASCII = 8 bits)
      - entropia:         H en bits/símbolo
      - bits_minimos:     n · H  (límite teórico)
      - redundancia:      porcentaje que sobra en la representación original
    """
    n = len(datos)
    h = entropia(datos)
    bits_originales = n * bits_por_simbolo_original
    bits_minimos = n * h
    redundancia = 1 - (bits_minimos / bits_originales) if bits_originales else 0
    return {
        "simbolos": n,
        "distintos": len(set(datos)),
        "entropia": h,
        "bits_originales": bits_originales,
        "bits_minimos": bits_minimos,
        "redundancia": redundancia,
    }


def demo():
    print("=" * 70)
    print("1 · CONTEXTO — Entropía de Shannon: el límite de la compresión")
    print("=" * 70)

    # --- Ejemplo de la diapositiva: moneda justa vs. moneda cargada ----------
    justa = entropia_de_distribucion([0.5, 0.5])
    cargada = entropia_de_distribucion([0.9, 0.1])
    print("\nMoneda justa   (cara 50 %%, sello 50 %%):  H = %.2f bit por lanzamiento" % justa)
    print("Moneda cargada (cara 90 %%, sello 10 %%):  H = %.2f bits por lanzamiento" % cargada)
    print("  -> ver 'cara' en la cargada aporta solo %.3f bits (casi no sorprende)" % informacion(0.9))
    print("  -> ver 'sello' en la cargada aporta %.3f bits (sorprende mucho)" % informacion(0.1))
    print("  Conclusión: lo predecible se puede guardar con MENOS bits.")

    # --- Textos con distinta redundancia ------------------------------------
    print("\nTexto                          H (bits/símb)  8 bits/símb -> mínimo   redundancia")
    for texto in ["AAAAAAAAAAAAAAAA", "ABABABABABABABAB", "ABRACADABRA",
                  "súbete para arriba", "q7#Lz!0pW@k9&Xr2"]:
        a = analisis(texto)
        print("  %-28r  %6.3f        %4d -> %6.1f bits     %5.1f %%"
              % (texto, a["entropia"], a["bits_originales"], a["bits_minimos"],
                 100 * a["redundancia"]))
    print("\nOjo: 'ABABAB...' tiene H = 1 bit con este modelo (solo frecuencias),")
    print("pero en realidad es totalmente predecible. Un modelo con CONTEXTO")
    print("(que mira el símbolo anterior) detecta esa redundancia: así trabajan")
    print("Lempel-Ziv, BWT o los modelos de IA, que se acercan más al límite real.")


if __name__ == "__main__":
    demo()
