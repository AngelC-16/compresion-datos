"""
3 · SIN PÉRDIDA — LZ78 / LZW (Lempel, Ziv y Welch, 1984): armar un diccionario
==============================================================================

LZ77 apunta "hacia atrás" en una ventana. La rama LZ78/LZW, en cambio, va
construyendo un DICCIONARIO de secuencias mientras lee, y emite el NÚMERO de
la entrada del diccionario. Como escribir «ONU» en vez de «Organización de
las Naciones Unidas»: la secuencia larga se reemplaza por un código corto.

Codificación LZW:
  1. El diccionario empieza con todos los símbolos sueltos (p. ej. 256 bytes).
  2. w = ""   (la secuencia más larga reconocida hasta ahora)
  3. Por cada símbolo c:
       si w+c está en el diccionario  -> w = w+c        (seguimos alargando)
       si no                          -> emitir código(w)
                                         agregar w+c al diccionario (nueva entrada)
                                         w = c
  4. Al final, emitir código(w).

El diccionario es una TABLA HASH (dict de Python): preguntar "¿w+c ya está?"
cuesta O(1) en promedio. Sin ella habría que buscar en toda la lista.

El decodificador reconstruye el MISMO diccionario a partir de los códigos, así
que el diccionario nunca se envía (compresión adaptativa, una sola pasada).
Uso real: formato GIF, el viejo `compress` de Unix, TIFF.
"""

import math


def codificar(texto, alfabeto=None):
    """Devuelve (lista_de_codigos, diccionario_final, pasos)."""
    if alfabeto is None:
        alfabeto = [chr(i) for i in range(256)]
    diccionario = {s: i for i, s in enumerate(alfabeto)}       # TABLA HASH
    siguiente = len(diccionario)

    w = ""
    codigos = []
    pasos = []
    for c in texto:
        wc = w + c
        if wc in diccionario:                 # búsqueda O(1)
            w = wc
        else:
            codigos.append(diccionario[w])
            diccionario[wc] = siguiente
            pasos.append((w, diccionario[w], wc, siguiente))
            siguiente += 1
            w = c
    if w:
        codigos.append(diccionario[w])
        pasos.append((w, diccionario[w], None, None))
    return codigos, diccionario, pasos


def decodificar(codigos, alfabeto=None):
    if alfabeto is None:
        alfabeto = [chr(i) for i in range(256)]
    diccionario = {i: s for i, s in enumerate(alfabeto)}
    siguiente = len(diccionario)
    if not codigos:
        return ""
    w = diccionario[codigos[0]]
    salida = [w]
    for codigo in codigos[1:]:
        if codigo in diccionario:
            entrada = diccionario[codigo]
        elif codigo == siguiente:
            # Caso especial "cScSc": el código se refiere a la entrada que
            # estamos a punto de crear. Necesariamente vale w + w[0].
            entrada = w + w[0]
        else:
            raise ValueError("código LZW inválido: %d" % codigo)
        salida.append(entrada)
        diccionario[siguiente] = w + entrada[0]
        siguiente += 1
        w = entrada
    return "".join(salida)


def bits_necesarios(codigos, tamano_alfabeto):
    """Tamaño en bits usando códigos de ancho creciente (como GIF): cuando el
    diccionario tiene d entradas, cada código ocupa ceil(log2 d) bits."""
    total = 0
    d = tamano_alfabeto
    for _ in codigos:
        total += max(1, math.ceil(math.log2(d + 1)))
        d += 1
    return total


def demo():
    print("=" * 70)
    print("3 · SIN PÉRDIDA — LZW: un diccionario que se arma mientras se lee")
    print("=" * 70)

    texto = "TOBEORNOTTOBEORTOBEORNOT"
    alfabeto = sorted(set(texto))            # diccionario inicial pequeño (legible)
    codigos, dic, pasos = codificar(texto, alfabeto)

    print("\nTexto: %s (%d letras)" % (texto, len(texto)))
    print("Diccionario inicial: %s" % {s: i for i, s in enumerate(alfabeto)})
    print("\n  w (reconocido)  emite   nueva entrada")
    for w, cod, nueva, num in pasos:
        if nueva:
            print("  %-15s  %3d     %-8s = %d" % (w, cod, nueva, num))
        else:
            print("  %-15s  %3d     (fin)" % (w, cod))
    print("\nCódigos emitidos: %s" % codigos)
    print("%d letras -> %d códigos" % (len(texto), len(codigos)))
    bits_fijos = len(texto) * math.ceil(math.log2(len(alfabeto)))
    print("Bits: sin comprimir (%d bits/letra) = %d   LZW (ancho creciente) = %d"
          % (math.ceil(math.log2(len(alfabeto))), bits_fijos,
             bits_necesarios(codigos, len(alfabeto))))
    rec = decodificar(codigos, alfabeto)
    print("Decodificado: %s  ¿igual? %s" % (rec, rec == texto))

    especial = "ABABABA"
    c2, _, _ = codificar(especial, ["A", "B"])
    print("\nCaso especial del decodificador: %r -> %s -> %r"
          % (especial, c2, decodificar(c2, ["A", "B"])))


if __name__ == "__main__":
    demo()
