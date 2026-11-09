"""
3 · SIN PÉRDIDA — Transformada de Burrows-Wheeler (BWT, 1994)
==============================================================

La BWT NO comprime por sí sola: REORDENA los datos para juntar letras iguales,
de modo que después RLE (o move-to-front) + Huffman compriman mucho mejor.
Es la base de bzip2.

    BANANA$  --BWT-->  ANNB$AA        ($ marca el final del texto)

Cómo se calcula (versión didáctica):
  1. Escribir todas las ROTACIONES del texto (con el $ al final).
  2. Ordenarlas alfabéticamente ($ va antes que cualquier letra).
  3. La salida es la ÚLTIMA COLUMNA de esa tabla ordenada.

¿Por qué junta letras iguales? Las rotaciones que empiezan con el mismo
contexto ("ANA...", "NA...") quedan juntas al ordenar, y la letra que va
ANTES de un contexto suele ser siempre la misma (antes de "he" casi siempre
hay "t" en inglés). Es una técnica "basada en contexto".

Lo mágico: es REVERSIBLE. Con solo la última columna se recupera el texto.

Complejidad de esta versión didáctica: O(n² log n) (ordena n rotaciones de
largo n). Las implementaciones reales usan arreglos de sufijos: O(n).
"""

from . import rle

FIN = "$"


def rotaciones_ordenadas(texto):
    t = texto + FIN
    return sorted(t[i:] + t[:i] for i in range(len(t)))


def transformar(texto):
    """BWT: última columna de la tabla de rotaciones ordenadas."""
    if FIN in texto:
        raise ValueError("el texto no puede contener el marcador de fin '$'")
    return "".join(rot[-1] for rot in rotaciones_ordenadas(texto))


def inversa(ultima):
    """Inversa con la propiedad "LF" (last-to-first), en O(n log n).

    La primera columna es la última ordenada. La k-ésima aparición de una
    letra en la última columna corresponde a la k-ésima aparición de esa misma
    letra en la primera columna. Siguiendo ese enlace desde la fila que
    empieza con '$' se reconstruye el texto de atrás hacia adelante.
    """
    n = len(ultima)
    # Para cada posición de la última columna: (letra, cuántas veces apareció antes)
    vistos = {}
    rango = []
    for c in ultima:
        rango.append(vistos.get(c, 0))
        vistos[c] = vistos.get(c, 0) + 1
    # Dónde empieza cada letra en la primera columna (ordenada).
    inicio = {}
    acumulado = 0
    for c in sorted(vistos):
        inicio[c] = acumulado
        acumulado += vistos[c]

    # Empezamos en la fila cuya rotación comienza con '$' (el texto original
    # rotado). Ojo: no siempre es la fila 0, porque caracteres como el espacio
    # (código 32) van ANTES que '$' (código 36) al ordenar.
    fila = inicio[FIN]
    resultado = []
    for _ in range(n):
        c = ultima[fila]
        resultado.append(c)
        fila = inicio[c] + rango[fila]          # salto LF
    # Se leyó de atrás hacia adelante y lo último leído fue '$':
    # al invertir queda "$texto"; quitamos el marcador.
    return "".join(reversed(resultado))[1:]


def mover_al_frente(texto):
    """Move-to-front (MTF): cada letra se reemplaza por su posición en una lista
    que se reordena poniendo la última usada al frente. Tras la BWT, las letras
    repetidas producen muchos 0s, que Huffman/RLE comprimen muy bien."""
    lista = sorted(set(texto))
    salida = []
    for c in texto:
        i = lista.index(c)
        salida.append(i)
        lista.insert(0, lista.pop(i))
    return salida


def demo():
    print("=" * 70)
    print("3 · SIN PÉRDIDA — Burrows-Wheeler: reordenar para juntar letras iguales")
    print("=" * 70)

    texto = "BANANA"
    print("\nRotaciones ordenadas de %s$:" % texto)
    for rot in rotaciones_ordenadas(texto):
        print("   %s  -> última letra: %s" % (rot, rot[-1]))
    b = transformar(texto)
    print("BWT(%s) = %s" % (texto, b))
    print("Inversa(%s) = %s  ¿igual? %s" % (b, inversa(b), inversa(b) == texto))

    frase = "tres tristes tigres tragaban trigo en un trigal"
    bf = transformar(frase)
    print("\nTexto: %r" % frase)
    print("BWT:   %r" % bf)
    r_antes = rle.codificar(frase)
    r_despues = rle.codificar(bf)
    print("Rachas RLE antes de la BWT: %d   después de la BWT: %d"
          % (len(r_antes), len(r_despues)))
    print("MTF tras la BWT (muchos ceros = fácil de comprimir): %s" % mover_al_frente(bf))
    print("¿La inversa recupera el texto? %s" % (inversa(bf) == frase))


if __name__ == "__main__":
    demo()
