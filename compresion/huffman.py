"""
3 · SIN PÉRDIDA — Codificación Huffman (David Huffman, 1952)
============================================================

Idea: códigos CORTOS para lo frecuente y LARGOS para lo raro (como el Morse,
donde la 'E' es un solo punto). Los códigos son "libres de prefijo": ningún
código es el comienzo de otro, así que al leer los bits no hay ambigüedad.

Algoritmo (usa las dos estructuras de datos de la presentación):
  1. Contar la frecuencia de cada símbolo                  (tabla hash, O(n))
  2. Meter una HOJA por símbolo en una COLA DE PRIORIDAD   (min-heap)
  3. Mientras quede más de un nodo en la cola:
       a. sacar los DOS de menor frecuencia                (O(log k) cada uno)
       b. crear un nodo padre con frecuencia = suma         (ÁRBOL BINARIO)
       c. meter el padre de nuevo en la cola               (O(log k))
  4. El nodo que queda es la raíz. El código de cada símbolo es el camino
     desde la raíz hasta su hoja: izquierda = 0, derecha = 1.

Complejidad: con k símbolos distintos hay k−1 fusiones, cada una O(log k)
=> construir el árbol cuesta O(k log k). Codificar el texto cuesta O(n).

Ejemplo de la diapositiva: ABRACADABRA
    Letra  Veces  Código
      A      5     0
      B      2     10
      R      2     110
      C      1     1110
      D      1     1111
    ASCII: 11 letras × 8 bits = 88 bits   ->   Huffman: 23 bits

Es un método ESTÁTICO (dos pasadas): primero se lee todo para contar, luego se
codifica con la misma tabla, y la tabla debe viajar junto al archivo.
"""

from collections import Counter

from .estructuras import MinHeap, NodoHuffman


# ---------------------------------------------------------------------------
# 1-4. Construcción del árbol
# ---------------------------------------------------------------------------
def construir_arbol(frecuencias, traza=None, fusiones=None):
    """Construye el árbol de Huffman a partir de {simbolo: frecuencia}.

    `traza` (opcional): lista donde se anotan los pasos, para explicar el
    algoritmo en la demo.
    `fusiones` (opcional): lista donde se anotan los objetos (a, b, padre) de
    cada fusión; la interfaz visual la usa para dibujar el bosque paso a paso.

    Desempate: en la cola guardamos tuplas (frecuencia, -orden, nodo). Si dos
    nodos tienen la misma frecuencia, sale primero el creado MÁS RECIENTEMENTE.
    Cualquier desempate da un código óptimo (mismo total de bits); este en
    particular produce las mismas longitudes de la diapositiva.
    """
    if not frecuencias:
        raise ValueError("no hay símbolos para codificar")

    cola = MinHeap()
    orden = 0
    for simbolo, freq in frecuencias.items():
        cola.insertar((freq, -orden, NodoHuffman(freq, simbolo)))
        orden += 1

    # Caso especial: un solo símbolo distinto (p. ej. "AAAA").
    # Le damos un padre artificial para que su código sea "0".
    if len(cola) == 1:
        _, _, unica = cola.extraer_minimo()
        return NodoHuffman(unica.frecuencia, izq=unica)

    while len(cola) > 1:
        f1, _, a = cola.extraer_minimo()     # el menor     -> rama izquierda (0)
        f2, _, b = cola.extraer_minimo()     # el siguiente -> rama derecha  (1)
        padre = NodoHuffman(f1 + f2, izq=a, der=b)
        if fusiones is not None:
            fusiones.append((a, b, padre))
        if traza is not None:
            traza.append("fusionar %s + %s -> nodo de %d"
                         % (_describir(a), _describir(b), f1 + f2))
        cola.insertar((padre.frecuencia, -orden, padre))
        orden += 1

    return cola.extraer_minimo()[2]


def _describir(nodo):
    if nodo.es_hoja():
        return "%s(%d)" % (nodo.simbolo, nodo.frecuencia)
    return "[%s](%d)" % ("".join(sorted(map(str, _hojas(nodo)))), nodo.frecuencia)


def _hojas(nodo):
    if nodo.es_hoja():
        return [nodo.simbolo]
    return _hojas(nodo.izq) + (_hojas(nodo.der) if nodo.der else [])


def generar_codigos(raiz):
    """Recorre el árbol (DFS) y arma la tabla {simbolo: "bits"}."""
    codigos = {}

    def recorrer(nodo, camino):
        if nodo is None:
            return
        if nodo.es_hoja():
            codigos[nodo.simbolo] = camino or "0"
            return
        recorrer(nodo.izq, camino + "0")   # izquierda = 0
        recorrer(nodo.der, camino + "1")   # derecha   = 1

    recorrer(raiz, "")
    return codigos


# ---------------------------------------------------------------------------
# Códigos CANÓNICOS: lo que usan DEFLATE (ZIP/PNG/gzip) y JPEG.
# Solo importan las LONGITUDES de los códigos; con ellas se reconstruyen los
# códigos de forma determinista. Así la "tabla" que viaja con el archivo es
# mucho más pequeña: basta guardar una longitud por símbolo.
# ---------------------------------------------------------------------------
def codigos_canonicos(longitudes):
    """{simbolo: longitud} -> {simbolo: código canónico}.

    Regla: ordenar por (longitud, símbolo) y asignar números binarios
    consecutivos; al pasar a una longitud mayor se desplaza a la izquierda.
    """
    ordenados = sorted(longitudes.items(), key=lambda par: (par[1], par[0]))
    codigos = {}
    codigo = 0
    longitud_previa = ordenados[0][1]
    for simbolo, longitud in ordenados:
        codigo <<= (longitud - longitud_previa)
        codigos[simbolo] = format(codigo, "0%db" % longitud)
        codigo += 1
        longitud_previa = longitud
    return codigos


# ---------------------------------------------------------------------------
# Codificar / decodificar
# ---------------------------------------------------------------------------
def codificar(datos, codigos=None):
    """Devuelve (bits_como_string, tabla_de_codigos)."""
    if codigos is None:
        codigos = generar_codigos(construir_arbol(Counter(datos)))
    bits = "".join(codigos[s] for s in datos)
    return bits, codigos


def decodificar(bits, codigos):
    """Decodifica usando la tabla (como los códigos son libres de prefijo,
    basta ir acumulando bits hasta que coincidan con algún código)."""
    inverso = {codigo: simbolo for simbolo, codigo in codigos.items()}
    resultado = []
    actual = ""
    for b in bits:
        actual += b
        if actual in inverso:            # búsqueda O(1) en tabla hash
            resultado.append(inverso[actual])
            actual = ""
    if actual:
        raise ValueError("bits sobrantes: el mensaje está incompleto")
    return resultado


def decodificar_con_arbol(bits, raiz):
    """Decodifica recorriendo el árbol: 0 = bajar a la izquierda, 1 = a la
    derecha; al llegar a una hoja se emite su símbolo y se vuelve a la raíz."""
    resultado = []
    nodo = raiz
    for b in bits:
        nodo = nodo.izq if b == "0" else nodo.der
        if nodo.es_hoja():
            resultado.append(nodo.simbolo)
            nodo = raiz
    return resultado


def es_libre_de_prefijo(codigos):
    """Verifica que ningún código sea prefijo de otro."""
    lista = sorted(codigos.values())
    # Tras ordenar, si a es prefijo de algún código, lo es del siguiente.
    return all(not lista[i + 1].startswith(lista[i]) for i in range(len(lista) - 1))


def dibujar_arbol(nodo, prefijo="", rama="", es_ultimo=True):
    """Devuelve el árbol como texto (para verlo en consola)."""
    lineas = []
    conector = "" if rama == "" else ("└─%s─ " % rama if es_ultimo else "├─%s─ " % rama)
    if nodo.es_hoja():
        lineas.append("%s%s%r (%d)" % (prefijo, conector, nodo.simbolo, nodo.frecuencia))
    else:
        lineas.append("%s%s(%d)" % (prefijo, conector, nodo.frecuencia))
        nuevo = prefijo + ("" if rama == "" else ("     " if es_ultimo else "│    "))
        hijos = [("0", nodo.izq), ("1", nodo.der)]
        hijos = [(r, h) for r, h in hijos if h is not None]
        for i, (r, h) in enumerate(hijos):
            lineas.extend(dibujar_arbol(h, nuevo, r, i == len(hijos) - 1))
    return lineas


def demo(texto="ABRACADABRA"):
    print("=" * 70)
    print("3 · SIN PÉRDIDA — Huffman: corto para lo frecuente")
    print("=" * 70)

    freqs = Counter(texto)
    print("\nTexto: %s   frecuencias: %s" % (texto, dict(freqs)))

    traza = []
    raiz = construir_arbol(freqs, traza)
    print("\nPasos (la cola de prioridad siempre entrega los dos menores):")
    for i, paso in enumerate(traza, 1):
        print("  %d. %s" % (i, paso))

    print("\nÁrbol resultante (0 = izquierda, 1 = derecha):")
    for linea in dibujar_arbol(raiz):
        print("   " + linea)

    codigos_arbol = generar_codigos(raiz)
    longitudes = {s: len(c) for s, c in codigos_arbol.items()}
    canon = codigos_canonicos(longitudes)

    print("\nLetra  Veces  Código(árbol)  Código canónico (= diapositiva)")
    for s in sorted(freqs, key=lambda x: (-freqs[x], x)):
        print("  %s     %2d     %-13s  %s" % (s, freqs[s], codigos_arbol[s], canon[s]))

    bits, _ = codificar(texto, canon)
    print("\nASCII:   %d letras × 8 bits = %d bits" % (len(texto), 8 * len(texto)))
    print("Huffman: %d bits -> %s" % (len(bits), bits))
    print("¿Libre de prefijo? %s" % es_libre_de_prefijo(canon))
    recuperado = "".join(decodificar(bits, canon))
    print("Decodificado: %s  ¿igual? %s" % (recuperado, recuperado == texto))

    from .entropia import entropia
    print("\nComparación con el límite de Shannon:")
    print("  Entropía H = %.3f bits/símbolo -> mínimo teórico %.1f bits"
          % (entropia(texto), entropia(texto) * len(texto)))
    print("  Huffman    = %.3f bits/símbolo -> %d bits (muy cerca del límite)"
          % (len(bits) / len(texto), len(bits)))


if __name__ == "__main__":
    demo()
