"""
5 · ESTRUCTURAS DE DATOS que hay "debajo" de la compresión
==========================================================

La presentación dice:
  * Árbol binario            -> Huffman guarda los códigos (izquierda = 0, derecha = 1)
  * Cola de prioridad (heap) -> Huffman saca los dos menores en O(log n)
  * Tabla hash               -> LZ77 / LZW encuentran al instante si una secuencia
                                 ya apareció (en Python: `dict`, ver lz77.py y lzw.py)

Aquí implementamos A MANO el montículo binario mínimo (min-heap) y el nodo del
árbol de Huffman, para que se vea exactamente cómo funcionan (no usamos `heapq`).

MONTÍCULO BINARIO MÍNIMO (min-heap)
-----------------------------------
Es un árbol binario COMPLETO guardado en un arreglo (lista):

        índice:   0   1   2   3   4   5   6
        lista:  [ 1,  3,  2,  7,  4,  5,  9 ]

                    1            <- la raíz (posición 0) siempre es el MENOR
                  /   \\
                 3     2
                / \\   / \\
               7   4 5   9

  Para el elemento en la posición i:
      padre      = (i - 1) // 2
      hijo izq.  = 2*i + 1
      hijo der.  = 2*i + 2

  Propiedad de heap: cada padre es <= que sus hijos.

  Operaciones:
      ver mínimo   O(1)      -> es lista[0]
      insertar     O(log n)  -> se pone al final y "sube" (sift-up)
      extraer min  O(log n)  -> el último pasa a la raíz y "baja" (sift-down)

  ¿Por qué O(log n)? Porque la altura de un árbol completo con n nodos es
  ⌊log2 n⌋, y subir o bajar recorre como máximo un camino raíz-hoja.
"""


class MinHeap:
    """Cola de prioridad implementada como montículo binario mínimo.

    Los elementos deben poder compararse con `<` (en Huffman usamos tuplas
    (frecuencia, desempate, nodo) para que la comparación sea por frecuencia).
    """

    def __init__(self):
        self._datos = []

    def __len__(self):
        return len(self._datos)

    def esta_vacio(self):
        return not self._datos

    def ver_minimo(self):
        """O(1): el mínimo siempre está en la raíz."""
        if not self._datos:
            raise IndexError("heap vacío")
        return self._datos[0]

    def insertar(self, elemento):
        """O(log n): se agrega al final y sube mientras sea menor que su padre."""
        self._datos.append(elemento)
        self._subir(len(self._datos) - 1)

    def extraer_minimo(self):
        """O(log n): saca la raíz; el último elemento ocupa su lugar y baja."""
        if not self._datos:
            raise IndexError("heap vacío")
        minimo = self._datos[0]
        ultimo = self._datos.pop()
        if self._datos:
            self._datos[0] = ultimo
            self._bajar(0)
        return minimo

    # --- operaciones internas ------------------------------------------------
    def _subir(self, i):
        """sift-up: intercambia con el padre mientras rompa la propiedad de heap."""
        while i > 0:
            padre = (i - 1) // 2
            if self._datos[i] < self._datos[padre]:
                self._datos[i], self._datos[padre] = self._datos[padre], self._datos[i]
                i = padre
            else:
                break

    def _bajar(self, i):
        """sift-down: intercambia con el hijo menor mientras sea mayor que él."""
        n = len(self._datos)
        while True:
            izq, der = 2 * i + 1, 2 * i + 2
            menor = i
            if izq < n and self._datos[izq] < self._datos[menor]:
                menor = izq
            if der < n and self._datos[der] < self._datos[menor]:
                menor = der
            if menor == i:
                break
            self._datos[i], self._datos[menor] = self._datos[menor], self._datos[i]
            i = menor

    def como_lista(self):
        """Copia del arreglo interno (útil para mostrar el estado del heap)."""
        return list(self._datos)


class NodoHuffman:
    """Nodo del ÁRBOL BINARIO de Huffman.

    * Hoja:          tiene `simbolo` y su `frecuencia`; no tiene hijos.
    * Nodo interno:  `simbolo` es None; su frecuencia es la suma de sus hijos.
    Convención: rama izquierda = bit 0, rama derecha = bit 1.
    """

    __slots__ = ("simbolo", "frecuencia", "izq", "der")

    def __init__(self, frecuencia, simbolo=None, izq=None, der=None):
        self.frecuencia = frecuencia
        self.simbolo = simbolo
        self.izq = izq
        self.der = der

    def es_hoja(self):
        return self.izq is None and self.der is None

    def __repr__(self):
        if self.es_hoja():
            return "Hoja(%r:%d)" % (self.simbolo, self.frecuencia)
        return "Nodo(%d)" % self.frecuencia


def demo():
    print("=" * 70)
    print("5 · ESTRUCTURAS — Montículo binario mínimo (cola de prioridad)")
    print("=" * 70)
    h = MinHeap()
    for x in [7, 3, 9, 1, 4, 5, 2]:
        h.insertar(x)
        print("insertar(%d) -> arreglo interno: %s" % (x, h.como_lista()))
    print("\nExtraer siempre devuelve el menor:")
    while not h.esta_vacio():
        m = h.extraer_minimo()
        print("extraer_minimo() = %d -> queda: %s" % (m, h.como_lista()))


if __name__ == "__main__":
    demo()
