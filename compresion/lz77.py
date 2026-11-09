"""
3 · SIN PÉRDIDA — LZ77 (Lempel y Ziv, 1977): «esto ya lo vi»
=============================================================

En vez de repetir una secuencia, se apunta a donde apareció antes:

    A B R A C A D | A B R A
    └── ventana deslizante (lo ya leído)     se guarda solo: (retrocede 7, copia 4)

Salida = lista de "tokens":
    ('L', símbolo)                 literal: un símbolo que no se pudo referenciar
    ('R', distancia, longitud)     referencia: "retrocede `distancia` y copia
                                   `longitud` símbolos"

Parámetros:
    VENTANA      cuánto hacia atrás se busca (DEFLATE usa 32 KB)
    MIN_COINC.   coincidencias más cortas no valen la pena (DEFLATE usa 3)
    MAX_COINC.   longitud máxima de una copia (DEFLATE usa 258)

¿Dónde entra la TABLA HASH?
    Buscar coincidencias comparando contra TODA la ventana cuesta O(VENTANA) por
    posición. En su lugar guardamos en un diccionario cada trío de símbolos
    (los 3 primeros de una posible coincidencia) -> lista de posiciones donde
    apareció. Así solo comparamos contra posiciones que ya empiezan igual:
    encontrar "si una secuencia ya apareció" es O(1) en promedio.
    Esto es exactamente lo que hace zlib (con "cadenas hash").

Es ADAPTATIVO: el "diccionario" (la ventana) se arma mientras se lee, en una
sola pasada, y el decodificador lo reconstruye solo: no hay que enviar tabla.

LZ77 + Huffman = DEFLATE  ->  ZIP · gzip · PNG   (ver archivo.py)
"""

VENTANA = 32 * 1024
MIN_COINCIDENCIA = 3
MAX_COINCIDENCIA = 258
MAX_CANDIDATOS = 64          # cuántas posiciones previas revisar como máximo


def codificar(datos, ventana=VENTANA, min_coinc=MIN_COINCIDENCIA,
              max_coinc=MAX_COINCIDENCIA, estadisticas=None, traza=None):
    """Codifica `datos` (str, bytes o lista) en tokens LZ77 usando tabla hash.

    Si se pasa un diccionario `estadisticas`, se anota cuántas comparaciones
    de símbolos se hicieron (para comparar con la búsqueda por fuerza bruta).
    Si se pasa una lista `traza`, se anota en cada paso qué clave se buscó en
    la tabla hash y qué posiciones candidatas devolvió (para la interfaz visual).
    """
    tokens = []
    tabla = {}                  # TABLA HASH: trío -> [posiciones donde aparece]
    comparaciones = 0
    n = len(datos)
    i = 0

    def registrar(pos):
        """Guarda la posición `pos` bajo la clave de sus 3 primeros símbolos."""
        if pos + min_coinc <= n:
            tabla.setdefault(datos[pos:pos + min_coinc], []).append(pos)

    while i < n:
        mejor_long, mejor_dist = 0, 0
        clave = datos[i:i + min_coinc]
        revisados = []
        if len(clave) == min_coinc and clave in tabla:        # O(1) promedio
            candidatos = tabla[clave]
            revisados = [p for p in candidatos[-MAX_CANDIDATOS:] if i - p <= ventana]
            # Revisamos desde la más reciente (distancias cortas primero).
            for pos in reversed(candidatos[-MAX_CANDIDATOS:]):
                distancia = i - pos
                if distancia > ventana:
                    break                     # ya se salió de la ventana
                longitud = 0
                # La copia puede "solaparse" con lo que se está escribiendo
                # (p. ej. 'AAAAAA' = 'A' + (retrocede 1, copia 5)).
                while (longitud < max_coinc and i + longitud < n
                       and datos[pos + longitud] == datos[i + longitud]):
                    longitud += 1
                    comparaciones += 1
                comparaciones += 1
                if longitud > mejor_long:
                    mejor_long, mejor_dist = longitud, distancia
                    if longitud == max_coinc:
                        break

        if traza is not None:
            traza.append({"i": i, "clave": clave, "candidatos": revisados,
                          "dist": mejor_dist, "long": mejor_long})
        if mejor_long >= min_coinc:
            tokens.append(("R", mejor_dist, mejor_long))
            for p in range(i, i + mejor_long):
                registrar(p)
            i += mejor_long
        else:
            tokens.append(("L", datos[i]))
            registrar(i)
            i += 1

    if estadisticas is not None:
        estadisticas["comparaciones"] = comparaciones
    return tokens


def codificar_fuerza_bruta(datos, ventana=VENTANA, min_coinc=MIN_COINCIDENCIA,
                           max_coinc=MAX_COINCIDENCIA, estadisticas=None):
    """Misma salida conceptual, pero buscando en TODA la ventana sin tabla hash.
    Sirve solo para comparar cuántas comparaciones se ahorra la tabla hash."""
    tokens = []
    comparaciones = 0
    n = len(datos)
    i = 0
    while i < n:
        mejor_long, mejor_dist = 0, 0
        for pos in range(i - 1, max(-1, i - ventana - 1), -1):
            longitud = 0
            while (longitud < max_coinc and i + longitud < n
                   and datos[pos + longitud] == datos[i + longitud]):
                longitud += 1
                comparaciones += 1
            comparaciones += 1
            if longitud > mejor_long:
                mejor_long, mejor_dist = longitud, i - pos
        if mejor_long >= min_coinc:
            tokens.append(("R", mejor_dist, mejor_long))
            i += mejor_long
        else:
            tokens.append(("L", datos[i]))
            i += 1
    if estadisticas is not None:
        estadisticas["comparaciones"] = comparaciones
    return tokens


def decodificar(tokens, como_bytes=False):
    """Reconstruye los datos. El decodificador no necesita tabla hash: solo
    copia desde lo que ya reconstruyó (por eso descomprimir ZIP es tan rápido)."""
    salida = []
    for token in tokens:
        if token[0] == "L":
            salida.append(token[1])
        else:
            _, distancia, longitud = token
            inicio = len(salida) - distancia
            for k in range(longitud):          # símbolo a símbolo (permite solape)
                salida.append(salida[inicio + k])
    if como_bytes:
        return bytes(salida)
    if salida and isinstance(salida[0], str):
        return "".join(salida)
    return salida


def a_texto(tokens):
    partes = []
    for t in tokens:
        if t[0] == "L":
            partes.append(str(t[1]) if not isinstance(t[1], int) else chr(t[1]))
        else:
            partes.append("(←%d,%d)" % (t[1], t[2]))
    return " ".join(partes)


def demo():
    print("=" * 70)
    print("3 · SIN PÉRDIDA — LZ77: «esto ya lo vi» (ventana deslizante + tabla hash)")
    print("=" * 70)

    texto = "ABRACADABRA"
    tokens = codificar(texto)
    print("\nTexto:  %s" % texto)
    print("Tokens: %s" % a_texto(tokens))
    print("  -> los 7 primeros son literales; luego 'ABRA' = (retrocede 7, copia 4)")
    print("Decodificado: %s  ¿igual? %s" % (decodificar(tokens), decodificar(tokens) == texto))

    texto2 = "AAAAAAAAAAAAAAAAAAAA"
    t2 = codificar(texto2)
    print("\nCopia que se solapa: %r -> %s" % (texto2, a_texto(t2)))
    print("  (retrocede 1 y copia 19: cada símbolo copiado sirve de fuente al siguiente)")

    frase = ("la compresion de datos usa la redundancia de los datos; "
             "la compresion sin perdida conserva los datos y la compresion "
             "con perdida descarta datos que no se perciben. ") * 4
    t3 = codificar(frase)
    refs = sum(1 for t in t3 if t[0] == "R")
    print("\nTexto repetitivo de %d caracteres -> %d tokens (%d literales, %d referencias)"
          % (len(frase), len(t3), len(t3) - refs, refs))

    e_hash, e_bruta = {}, {}
    codificar(frase, estadisticas=e_hash)
    codificar_fuerza_bruta(frase, estadisticas=e_bruta)
    print("\n¿Para qué la tabla hash? Comparaciones de símbolos al buscar coincidencias:")
    print("  fuerza bruta (toda la ventana): %8d" % e_bruta["comparaciones"])
    print("  con tabla hash (solo candidatos): %6d  (%.0f veces menos)"
          % (e_hash["comparaciones"], e_bruta["comparaciones"] / e_hash["comparaciones"]))


if __name__ == "__main__":
    demo()
