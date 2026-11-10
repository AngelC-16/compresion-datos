# Explicación detallada del código

**«¿Cómo cabe todo? Compresión de datos»** · Estructuras de Datos II · Uninorte
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

Este documento explica **el código de los algoritmos** (carpeta `compresion/`), función por
función y línea por línea, con trazas a mano de los mismos ejemplos de las diapositivas. **No
explica la interfaz web**: `app.py`, `web/` y `compresion/api.py` solo muestran en pantalla lo que
calculan los módulos de aquí.

> Cómo leerlo: cada sección tiene (1) **la idea** en una frase, (2) **el código** (copiado del
> proyecto; a veces resumido, y se indica), (3) **qué hace cada línea**, (4) **una traza** con
> valores reales, (5) **complejidad** y (6) **qué preguntar / qué puede fallar**.
> Si quieren ver cualquier traza en vivo: `python app.py` y la sección correspondiente.

---

## Índice

0. [Mapa: qué archivo hace qué](#0-mapa-qué-archivo-hace-qué)
1. [`entropia.py` — el límite de Shannon](#1-entropiapy--el-límite-de-shannon)
2. [`adaptativa.py` — modelo estático vs. adaptativo](#2-adaptativapy--modelo-estático-vs-adaptativo)
3. [`rle.py` — Run-Length Encoding](#3-rlepy--run-length-encoding)
4. [`estructuras.py` — min-heap y nodo del árbol](#4-estructuraspy--min-heap-y-nodo-del-árbol)
5. [`huffman.py` — codificación Huffman](#5-huffmanpy--codificación-huffman)
6. [`lz77.py` — ventana deslizante + tabla hash](#6-lz77py--ventana-deslizante--tabla-hash)
7. [`lzw.py` — diccionario dinámico](#7-lzwpy--diccionario-dinámico)
8. [`bwt.py` — Burrows-Wheeler](#8-bwtpy--burrows-wheeler)
9. [`aritmetica.py` — codificación aritmética](#9-aritmeticapy--codificación-aritmética)
10. [`jpeg_dct.py` — imágenes con pérdida](#10-jpeg_dctpy--imágenes-con-pérdida)
11. [`audio.py` — enmascaramiento psicoacústico](#11-audiopy--enmascaramiento-psicoacústico)
12. [`video.py` — cuadros I/P y vectores de movimiento](#12-videopy--cuadros-ip-y-vectores-de-movimiento)
13. [`archivo.py` — compresor real (mini-DEFLATE)](#13-archivopy--compresor-real-mini-deflate)
14. [Tabla resumen de complejidades](#14-tabla-resumen-de-complejidades)
15. [Conceptos de Python que aparecen en el código](#15-conceptos-de-python-que-aparecen-en-el-código)
16. [Preguntas que nos pueden hacer (con respuesta)](#16-preguntas-que-nos-pueden-hacer-con-respuesta)

---

## 0. Mapa: qué archivo hace qué

```
compresion/
├── entropia.py      1 · Contexto       H = −Σ p·log2 p, redundancia
├── adaptativa.py    2 · Clasificación  costo de un modelo fijo vs. uno que aprende
├── rle.py           3 · Sin pérdida    (cantidad, símbolo)
├── estructuras.py   5 · Estructuras    MinHeap (cola de prioridad) y NodoHuffman (árbol)
├── huffman.py       3 · Sin pérdida    árbol + códigos + códigos canónicos
├── lz77.py          3 · Sin pérdida    (retrocede, copia) con tabla hash
├── lzw.py           3 · Sin pérdida    diccionario que crece
├── bwt.py           3 · Sin pérdida    rotaciones ordenadas + inversa LF
├── aritmetica.py    3 · Sin pérdida    intervalo [0,1) con fracciones exactas
├── jpeg_dct.py      4 · Con pérdida    bloques 8×8, DCT, cuantización, zigzag
├── audio.py         4 · Con pérdida    FFT + curva de enmascaramiento
├── video.py         4 · Con pérdida    block matching (SAD), vectores, residuo
├── archivo.py       5 · Aplicaciones   compresor de archivos real (formato .edd)
└── imagen_bmp.py    utilidad           guardar imágenes .bmp
```

**Dependencias entre módulos** (quién usa a quién):

```
huffman ──usa──> estructuras (MinHeap, NodoHuffman)
archivo ──usa──> huffman, lz77, rle
jpeg_dct ─usa──> huffman (para estimar el tamaño final)
bwt ─────usa──> rle (para contar rachas antes/después)
```

Todo usa solo la **librería estándar** de Python: `collections.Counter`, `fractions.Fraction`,
`math`, `cmath`, `struct`, `wave`, `zlib`/`bz2`/`lzma` (solo para comparar).

---

## 1. `entropia.py` — el límite de Shannon

**Idea:** medir cuántos bits *hacen falta de verdad* para guardar un mensaje sin perder nada.

### 1.1 Contar frecuencias

```python
def frecuencias(datos):
    return Counter(datos)
```

- `Counter` es un **diccionario** (tabla hash) que cuenta: `Counter("ABRACADABRA")` →
  `{'A': 5, 'B': 2, 'R': 2, 'C': 1, 'D': 1}`.
- Recorre los datos una vez y cada suma cuesta O(1) promedio → **O(n)**.
- Funciona con `str` (cuenta letras) y con `bytes` (cuenta números 0–255).

### 1.2 Probabilidades

```python
def probabilidades(datos):
    total = len(datos)
    return {simbolo: veces / total for simbolo, veces in frecuencias(datos).items()}
```

Comprensión de diccionario: para cada par `(símbolo, veces)` guarda `veces / total`.
ABRACADABRA → `{'A': 0.4545, 'B': 0.1818, 'R': 0.1818, 'C': 0.0909, 'D': 0.0909}`.

### 1.3 La fórmula

```python
def entropia_de_distribucion(probs):
    valores = probs.values() if isinstance(probs, dict) else probs
    h = -sum(p * math.log2(p) for p in valores if p > 0)
    return h if h > 0 else 0.0           # evita mostrar "-0.000"
```

| Línea | Qué hace |
|---|---|
| `valores = …` | Acepta un diccionario (`{símbolo: p}`) o una lista (`[0.9, 0.1]`) |
| `p * math.log2(p)` | Un término de la suma. Como `p < 1`, `log2(p)` es negativo |
| `if p > 0` | `log2(0)` no existe; por convención `0·log2(0) = 0`, así que se salta |
| `-sum(...)` | El signo menos vuelve positivo el resultado |
| `h if h > 0 else 0.0` | Si todo es el mismo símbolo da `-0.0`; lo mostramos como `0.0` |

**Traza (moneda cargada 90/10):**
`0.9·log2(0.9) = 0.9·(−0.152) = −0.137` y `0.1·log2(0.1) = 0.1·(−3.322) = −0.332`
→ suma `−0.469` → con el menos: **H = 0.469 bits**.

**Traza (ABRACADABRA):**

| símbolo | p | −log2 p | p·(−log2 p) |
|---|---|---|---|
| A | 5/11 = 0.455 | 1.138 | 0.517 |
| B | 2/11 = 0.182 | 2.459 | 0.447 |
| R | 2/11 = 0.182 | 2.459 | 0.447 |
| C | 1/11 = 0.091 | 3.459 | 0.315 |
| D | 1/11 = 0.091 | 3.459 | 0.315 |
| | | **H =** | **2.040 bits/símbolo** |

Mínimo para todo el texto: 11 × 2.040 = **22.4 bits** (en ASCII son 88).

### 1.4 `analisis(datos)`

Devuelve un diccionario con `entropia`, `bits_originales = n·8`, `bits_minimos = n·H` y
`redundancia = 1 − bits_minimos / bits_originales`. Para ABRACADABRA: 1 − 22.4/88 = **74.5 %**
de los bits sobran.

### 1.5 Lo que hay que entender

Esta H es de **orden 0**: solo mira cuántas veces aparece cada símbolo, no el orden.
`"ABABABAB"` da 1 bit/símbolo aunque sea totalmente predecible. Los algoritmos con **contexto**
(LZ77, BWT) aprovechan el orden y por eso pueden bajar de esta cifra (lo vemos en la sección 13).

---

## 2. `adaptativa.py` — modelo estático vs. adaptativo

**Idea:** comparar cuántos bits gasta un modelo con tabla fija contra uno que aprende mientras lee.
Se usa el **costo ideal** `−log2 p` (lo que gastaría un codificador perfecto) para que la
comparación sea justa.

### 2.1 Estático

```python
def costo_estatico(texto):
    conteos = Counter(texto)
    n = len(texto)
    datos = sum(-math.log2(conteos[s] / n) for s in texto)
    tabla = len(conteos) * 16
    return datos, tabla
```

- Primera pasada: `Counter` cuenta todo.
- Segunda pasada: cada símbolo cuesta `−log2(veces/n)` **siempre lo mismo**.
- `tabla`: la tabla viaja con el archivo; estimamos 16 bits por entrada (8 del símbolo + 8 del
  conteo).

### 2.2 Adaptativo

```python
def costo_adaptativo(texto, alfabeto, memoria=None, detalle=None):
    conteos = {s: 1 for s in alfabeto}      # todos empiezan en 1
    total = len(alfabeto)
    recientes = deque()
    bits = 0.0
    for i, s in enumerate(texto):
        p = conteos[s] / total               # probabilidad con lo visto HASTA AHORA
        costo = -math.log2(p)
        bits += costo
        conteos[s] += 1                      # actualizar DESPUÉS de codificar
        total += 1
        if memoria is not None:              # ventana: olvidar lo más viejo
            recientes.append(s)
            if len(recientes) > memoria:
                viejo = recientes.popleft()
                conteos[viejo] -= 1
                total -= 1
    return bits
```

| Línea | Por qué |
|---|---|
| `conteos = {s: 1 ...}` | **Suavizado de Laplace**: si un conteo fuera 0, p = 0 y `log2(0)` explota |
| `p = conteos[s] / total` | El modelo solo sabe lo que ya leyó: es justo lo que sabrá el decodificador |
| actualizar **después** | Si actualizara antes, el decodificador no podría repetirlo (aún no conoce `s`) |
| `deque` + `popleft()` | Cola doble: sacar del frente es O(1). Implementa la «memoria corta» |

**Traza** con `"A"×50 + "B"×50`, alfabeto `AB`:

| posición | lee | p | costo |
|---|---|---|---|
| 0 | A | 1/2 = 0.500 | 1.00 bit |
| 1 | A | 2/3 = 0.667 | 0.58 |
| 49 | A | 50/51 = 0.980 | 0.03 |
| 50 | B | 1/52 = 0.019 | **5.70** ← sorpresa |
| 99 | B | 50/101 = 0.495 | 1.01 |

Totales: estática **132** bits (100 + 32 de tabla), adaptativa **103**, adaptativa con memoria de 8
**27.2**. Con memoria corta el modelo «olvida» las A y se adapta enseguida a las B.

---

## 3. `rle.py` — Run-Length Encoding

**Idea:** `AAAAABBBCC` → `(5,A) (3,B) (2,C)`.

### 3.1 Codificar

```python
def codificar(datos):
    rachas = []
    i = 0
    n = len(datos)
    while i < n:
        simbolo = datos[i]
        cantidad = 1
        while i + cantidad < n and datos[i + cantidad] == simbolo:
            cantidad += 1
        rachas.append((cantidad, simbolo))
        i += cantidad
    return rachas
```

| Línea | Qué hace |
|---|---|
| `while i < n` | `i` apunta al inicio de la racha actual |
| `simbolo = datos[i]` | El símbolo que se va a contar |
| `while i + cantidad < n and ...` | Avanza mientras el siguiente sea igual. **Primero** revisa no salirse del arreglo (`and` evalúa en corto circuito) |
| `rachas.append(...)` | Guarda la tupla |
| `i += cantidad` | **Salta** toda la racha: por eso cada posición se mira una sola vez |

**Traza `AAAAABBBCC`:**

| i | símbolo | cantidad al terminar | se guarda | nuevo i |
|---|---|---|---|---|
| 0 | A | 5 | (5, A) | 5 |
| 5 | B | 3 | (3, B) | 8 |
| 8 | C | 2 | (2, C) | 10 → fin |

**Complejidad:** aunque hay dos `while` anidados es **O(n)**: el interno avanza `cantidad` y el
externo salta esas mismas posiciones; en total se visita cada posición una vez.

### 3.2 Decodificar

```python
partes = [simbolo * cantidad for cantidad, simbolo in rachas]
return "".join(partes)
```

En Python `"A" * 5 == "AAAAA"`. Si los símbolos no son texto (p. ej. números), usa
`resultado.extend([simbolo] * cantidad)`.

### 3.3 Versión por bytes (para archivos)

```python
def codificar_bytes(datos: bytes) -> bytes:
    ...
        while ... and datos[i + cantidad] == b and cantidad < 255:
            cantidad += 1
        salida += bytes([cantidad, b])
```

Cada racha ocupa **2 bytes**: `[cantidad, byte]`. Como un byte guarda máximo 255, las rachas más
largas se parten (`cantidad < 255`).

### 3.4 La trampa

`ABC` → `(1,A)(1,B)(1,C)` = 6 casillas para 3 símbolos. En el guion de la exposición (texto
normal) RLE deja el archivo en **198 %**: casi el doble.

---

## 4. `estructuras.py` — min-heap y nodo del árbol

### 4.1 Por qué un heap

Huffman necesita, una y otra vez, **sacar los dos elementos de menor frecuencia** y **meter uno
nuevo**. Con una lista ordenada, meter cuesta O(n). Con un **montículo binario mínimo**, ambas
cosas cuestan **O(log n)**.

### 4.2 Cómo se guarda un árbol en una lista

```
índice:   0   1   2   3   4   5   6
lista:  [ 1,  3,  2,  7,  4,  9,  5 ]

               1 (0)
             /      \
          3 (1)     2 (2)
          /  \      /  \
       7(3) 4(4)  9(5) 5(6)
```

Para la posición `i`: **padre = (i−1)//2**, **hijo izquierdo = 2i+1**, **hijo derecho = 2i+2**.
No hacen falta punteros: la posición lo dice todo. Esto funciona porque el árbol es **completo**
(se llena de izquierda a derecha, nivel por nivel).

**Propiedad de heap:** cada padre ≤ sus hijos ⇒ el mínimo está siempre en `lista[0]`.

### 4.3 Insertar = agregar al final + subir

```python
def insertar(self, elemento):
    self._datos.append(elemento)
    self._subir(len(self._datos) - 1)

def _subir(self, i):
    while i > 0:
        padre = (i - 1) // 2
        if self._datos[i] < self._datos[padre]:
            self._datos[i], self._datos[padre] = self._datos[padre], self._datos[i]
            i = padre
        else:
            break
```

*(En el archivo real hay además líneas `self._avisar(...)`: solo avisan a la interfaz para
animar; no cambian el algoritmo.)*

- `append` pone el nuevo al final (sigue siendo árbol completo).
- Mientras sea menor que su padre, se intercambian (`a, b = b, a` es el intercambio en Python).
- Se detiene al llegar a la raíz (`i > 0`) o cuando ya no es menor.

**Traza: insertar 1 en `[3, 7, 9]`:**

| paso | lista | i | padre | ¿menor? |
|---|---|---|---|---|
| append | `[3, 7, 9, 1]` | 3 | (3−1)//2 = 1 → 7 | sí → intercambiar |
| | `[3, 1, 9, 7]` | 1 | (1−1)//2 = 0 → 3 | sí → intercambiar |
| | `[1, 3, 9, 7]` | 0 | — | llegó a la raíz |

Dos intercambios = la altura del árbol.

### 4.4 Extraer mínimo = sacar la raíz + bajar

```python
def extraer_minimo(self):
    minimo = self._datos[0]
    ultimo = self._datos.pop()
    if self._datos:
        self._datos[0] = ultimo
        self._bajar(0)
    return minimo

def _bajar(self, i):
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
```

- Se guarda el mínimo (la raíz) para devolverlo.
- El **último** pasa a la raíz (así el árbol sigue completo) y luego **baja**: se compara con sus
  dos hijos y se cambia con el **menor** de ellos. Si se cambiara con el mayor, ese mayor quedaría
  de padre del menor y se rompería la propiedad.
- `izq < n` revisa que el hijo exista.

**Traza: extraer de `[1, 3, 2, 7, 4, 9, 5]`:**

| paso | lista | i | hijos | acción |
|---|---|---|---|---|
| sacar 1, el último (5) a la raíz | `[5, 3, 2, 7, 4, 9]` | 0 | 3 y 2 → menor 2 (pos 2) | intercambiar |
| | `[2, 3, 5, 7, 4, 9]` | 2 | 9 (pos 5) | 5 < 9 → parar |

Devuelve **1**; el nuevo mínimo es **2**.

### 4.5 `NodoHuffman`

```python
class NodoHuffman:
    __slots__ = ("simbolo", "frecuencia", "izq", "der")
    def __init__(self, frecuencia, simbolo=None, izq=None, der=None): ...
    def es_hoja(self):
        return self.izq is None and self.der is None
```

- **Hoja:** tiene `simbolo`, sin hijos.
- **Nodo interno:** `simbolo = None`, frecuencia = suma de los hijos.
- `__slots__` le dice a Python que solo existen esos 4 atributos: ocupa menos memoria.

---

## 5. `huffman.py` — codificación Huffman

### 5.1 Construir el árbol

```python
def construir_arbol(frecuencias, traza=None, fusiones=None):
    cola = MinHeap()
    orden = 0
    for simbolo, freq in frecuencias.items():
        cola.insertar((freq, -orden, NodoHuffman(freq, simbolo)))
        orden += 1

    if len(cola) == 1:                                   # caso "AAAA"
        _, _, unica = cola.extraer_minimo()
        return NodoHuffman(unica.frecuencia, izq=unica)

    while len(cola) > 1:
        f1, _, a = cola.extraer_minimo()     # el menor     -> izquierda (0)
        f2, _, b = cola.extraer_minimo()     # el siguiente -> derecha  (1)
        padre = NodoHuffman(f1 + f2, izq=a, der=b)
        cola.insertar((padre.frecuencia, -orden, padre))
        orden += 1

    return cola.extraer_minimo()[2]
```

**¿Por qué tuplas `(freq, -orden, nodo)`?** El heap compara con `<`. Python compara tuplas
posición por posición: primero la frecuencia; si empatan, `-orden`. Así:
1. Se ordena por frecuencia (lo que pide Huffman).
2. El desempate es determinista: sale primero el de `orden` más alto, o sea, **el creado más
   recientemente**.
3. Nunca se llega a comparar dos `NodoHuffman` (que no saben compararse y darían error), porque
   `orden` es único.

**Caso especial `len(cola) == 1`:** con un solo símbolo distinto (`"AAAA"`) no hay nada que
fusionar y el código saldría vacío. Se crea un padre artificial para que el código sea `"0"`.

**Traza completa con ABRACADABRA.** `Counter` guarda los símbolos en orden de aparición
(A, B, R, C, D), así que reciben `orden` 0…4:

| en la cola (clave) | |
|---|---|
| A (5, 0) · B (2, −1) · R (2, −2) · C (1, −3) · D (1, −4) | estado inicial |

| fusión | sale 1º (izq, bit 0) | sale 2º (der, bit 1) | nuevo nodo (clave) |
|---|---|---|---|
| 1 | D (1, −4) | C (1, −3) | [DC] (2, −5) |
| 2 | [DC] (2, −5) | R (2, −2) | [DCR] (4, −6) |
| 3 | B (2, −1) | [DCR] (4, −6) | [BDCR] (6, −7) |
| 4 | A (5, 0) | [BDCR] (6, −7) | raíz (11, −8) |

En la fusión 1, D sale antes que C porque `(1, −4) < (1, −3)`. En la 2, `[DC]` sale antes que R
y B porque `−5` es el menor de los desempates con frecuencia 2.

Árbol resultante (el mismo de la diapositiva 8):

```
(11)
├─0─ A (5)
└─1─ (6)
     ├─0─ B (2)
     └─1─ (4)
          ├─0─ (2)
          │    ├─0─ D (1)
          │    └─1─ C (1)
          └─1─ R (2)
```

**Complejidad:** k símbolos distintos → k−1 fusiones × (2 extracciones + 1 inserción) de
O(log k) cada una → **O(k log k)**. Contar las frecuencias antes es O(n).

### 5.2 Generar los códigos (recorrido DFS)

```python
def generar_codigos(raiz):
    codigos = {}
    def recorrer(nodo, camino):
        if nodo is None:
            return
        if nodo.es_hoja():
            codigos[nodo.simbolo] = camino or "0"
            return
        recorrer(nodo.izq, camino + "0")
        recorrer(nodo.der, camino + "1")
    recorrer(raiz, "")
    return codigos
```

Recursión en **preorden**: al bajar a la izquierda se agrega `"0"`, a la derecha `"1"`; al llegar
a una hoja, el camino acumulado es su código. Resultado: `A=0, B=10, D=1100, C=1101, R=111`.
Costo O(k) (visita cada nodo una vez).

### 5.3 Códigos canónicos

```python
def codigos_canonicos(longitudes):
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
```

| Línea | Qué hace |
|---|---|
| `sorted(... key=(longitud, símbolo))` | Primero los códigos cortos; si empatan, por orden alfabético |
| `codigo <<= (…)` | Desplazar a la izquierda = multiplicar por 2 por cada bit de más |
| `format(codigo, "04b")` | Escribe el número en binario con ceros a la izquierda hasta 4 dígitos |
| `codigo += 1` | El siguiente código de la misma longitud es el número siguiente |

**Traza** (longitudes A:1, B:2, R:3, C:4, D:4):

| símbolo | long. | `codigo` antes | desplaz. | queda | binario |
|---|---|---|---|---|---|
| A | 1 | 0 | 0 | 0 | `0` |
| B | 2 | 1 | ×2 | 2 | `10` |
| R | 3 | 3 | ×2 | 6 | `110` |
| C | 4 | 7 | ×2 | 14 | `1110` |
| D | 4 | 15 | — | 15 | `1111` |

Son exactamente los códigos de la diapositiva. **¿Por qué existen?** Porque con solo las
longitudes se reconstruyen los códigos: el archivo comprimido no necesita guardar el árbol, solo
una longitud por símbolo. Lo usan ZIP, PNG y JPEG (y nuestro `archivo.py`).

### 5.4 Codificar y decodificar

```python
def codificar(datos, codigos=None):
    if codigos is None:
        codigos = generar_codigos(construir_arbol(Counter(datos)))
    bits = "".join(codigos[s] for s in datos)
    return bits, codigos
```

Cambia cada símbolo por su código y los pega. ABRACADABRA →
`0 10 110 0 1110 0 1111 0 10 110 0` = **23 bits** (5·1 + 2·2 + 2·3 + 1·4 + 1·4).

```python
def decodificar(bits, codigos):
    inverso = {codigo: simbolo for simbolo, codigo in codigos.items()}
    resultado, actual = [], ""
    for b in bits:
        actual += b
        if actual in inverso:            # búsqueda O(1) en tabla hash
            resultado.append(inverso[actual])
            actual = ""
    ...
```

Acumula bits hasta que coinciden con algún código. Funciona **porque los códigos son libres de
prefijo**: si `actual` ya es un código, no puede ser el inicio de otro, así que no hay ambigüedad.

```python
def decodificar_con_arbol(bits, raiz):
    nodo = raiz
    for b in bits:
        nodo = nodo.izq if b == "0" else nodo.der
        if nodo.es_hoja():
            resultado.append(nodo.simbolo)
            nodo = raiz
```

La otra forma: bajar por el árbol con cada bit; al llegar a una hoja, emitir y volver a la raíz.

```python
def es_libre_de_prefijo(codigos):
    lista = sorted(codigos.values())
    return all(not lista[i + 1].startswith(lista[i]) for i in range(len(lista) - 1))
```

Truco: al ordenar alfabéticamente, si un código es prefijo de otro, quedan **uno junto al otro**.
Basta comparar vecinos: O(k log k) en vez de comparar todos con todos (O(k²)).

---

## 6. `lz77.py` — ventana deslizante + tabla hash

**Idea:** si lo que viene ya apareció antes, guardar `(retrocede, copia)` en vez de repetirlo.

### 6.1 Parámetros

```python
VENTANA = 32 * 1024        # cuánto se mira hacia atrás (como DEFLATE)
MIN_COINCIDENCIA = 3       # copias de menos de 3 no valen la pena
MAX_COINCIDENCIA = 258     # copia máxima (como DEFLATE)
MAX_CANDIDATOS = 64        # cuántas posiciones previas revisar como mucho
```

### 6.2 El codificador (resumido)

```python
def codificar(datos, ventana=VENTANA, ...):
    tokens = []
    tabla = {}                  # TABLA HASH: trío -> [posiciones donde aparece]
    i = 0
    def registrar(pos):
        if pos + 3 <= n:
            tabla.setdefault(datos[pos:pos + 3], []).append(pos)

    while i < n:
        mejor_long, mejor_dist = 0, 0
        clave = datos[i:i + 3]
        if len(clave) == 3 and clave in tabla:                 # O(1) promedio
            for pos in reversed(tabla[clave][-MAX_CANDIDATOS:]):
                distancia = i - pos
                if distancia > ventana:
                    break
                longitud = 0
                while (longitud < max_coinc and i + longitud < n
                       and datos[pos + longitud] == datos[i + longitud]):
                    longitud += 1
                if longitud > mejor_long:
                    mejor_long, mejor_dist = longitud, distancia

        if mejor_long >= 3:
            tokens.append(("R", mejor_dist, mejor_long))
            for p in range(i, i + mejor_long):
                registrar(p)
            i += mejor_long
        else:
            tokens.append(("L", datos[i]))
            registrar(i)
            i += 1
    return tokens
```

| Parte | Qué hace |
|---|---|
| `tabla = {}` | **La tabla hash**. Clave: los 3 símbolos que empiezan en una posición. Valor: lista de posiciones donde apareció ese trío |
| `registrar(pos)` | Anota la posición `pos` bajo su trío. `setdefault` crea la lista si no existía |
| `clave in tabla` | «¿Ya vi estos 3 símbolos?» en **O(1)**. Si no, ni siquiera se busca |
| `reversed(...[-64:])` | Revisa primero las apariciones **más recientes** (distancias cortas) y máximo 64 |
| `if distancia > ventana: break` | Más atrás de la ventana no se puede referenciar |
| `while ... datos[pos+k] == datos[i+k]` | Mide cuánto coincide desde ese candidato |
| `if mejor_long >= 3` | Si vale la pena, se emite una referencia; si no, un literal |
| `registrar` en ambos casos | Todo lo leído pasa a ser «ventana» para el futuro |

**Traza ABRACADABRA** (posiciones 0–10):

| i | clave | ¿en la tabla? | token | se registra |
|---|---|---|---|---|
| 0 | ABR | no | `A` | ABR→[0] |
| 1 | BRA | no | `B` | BRA→[1] |
| 2 | RAC | no | `R` | RAC→[2] |
| 3 | ACA | no | `A` | ACA→[3] |
| 4 | CAD | no | `C` | CAD→[4] |
| 5 | ADA | no | `A` | ADA→[5] |
| 6 | DAB | no | `D` | DAB→[6] |
| 7 | ABR | **sí → [0]** | distancia 7; compara A=A, B=B, R=R, A=A → long 4 → **`(←7, 4)`** | |

Fin: `A B R A C A D (←7,4)` = el **«retrocede 7, copia 4»** de la diapositiva.

**Copias solapadas:** con `"A" × 20`, en `i = 1` la clave `AAA` está en `[0]`, distancia 1, y la
comparación `datos[0+k] == datos[1+k]` sigue hasta el final → `(←1, 19)`. La fuente y el destino
se pisan, y está bien: se copia símbolo a símbolo.

**¿Cuánto ayuda la tabla hash?** `codificar_fuerza_bruta` hace lo mismo pero comparando contra
**toda** la ventana. Con un texto repetitivo de 656 caracteres: **8 961** comparaciones sin tabla
vs. **935** con tabla (≈ 10 veces menos).

### 6.3 Decodificar

```python
for token in tokens:
    if token[0] == "L":
        salida.append(token[1])
    else:
        _, distancia, longitud = token
        inicio = len(salida) - distancia
        for k in range(longitud):
            salida.append(salida[inicio + k])
```

No necesita tabla: solo copia desde lo que ya reconstruyó. Se copia **de a un símbolo** para que
las copias solapadas funcionen (cada símbolo copiado ya está disponible para el siguiente). Por eso
descomprimir un ZIP es mucho más rápido que comprimirlo.

**Complejidad:** sin tabla O(n · ventana); con tabla, en la práctica cercano a O(n) (limitado por
`MAX_CANDIDATOS` y `MAX_COINCIDENCIA`).

---

## 7. `lzw.py` — diccionario dinámico

**Idea:** en vez de apuntar hacia atrás, numerar las secuencias en un diccionario que crece.

```python
def codificar(texto, alfabeto=None):
    diccionario = {s: i for i, s in enumerate(alfabeto)}       # TABLA HASH
    siguiente = len(diccionario)
    w = ""
    codigos = []
    for c in texto:
        wc = w + c
        if wc in diccionario:
            w = wc                       # seguir alargando
        else:
            codigos.append(diccionario[w])
            diccionario[wc] = siguiente  # entrada nueva
            siguiente += 1
            w = c
    if w:
        codigos.append(diccionario[w])
    return codigos, diccionario, pasos
```

- `w` = la secuencia más larga reconocida hasta ahora.
- Si `w + c` existe, se alarga. Si no, se emite el código de `w`, se agrega `w + c` como entrada
  nueva y se empieza de nuevo desde `c`.

**Traza** `TOBEORNOTTOBEORTOBEORNOT`, diccionario inicial `B=0, E=1, N=2, O=3, R=4, T=5`:

| lee c | w+c | ¿existe? | emite | nueva entrada | w queda |
|---|---|---|---|---|---|
| T | T | sí | | | T |
| O | TO | no | 5 (T) | TO = 6 | O |
| B | OB | no | 3 (O) | OB = 7 | B |
| … | | | | | |
| T, O | TO | **sí** (es la 6) | | | TO |
| B | TOB | no | **6** (TO) | TOB = 15 | B |
| … | | | | | |

Al final: 24 letras → **16 códigos**. A medida que avanza, cada código reemplaza más letras.

### 7.1 El decodificador y su caso especial

```python
for codigo in codigos[1:]:
    if codigo in diccionario:
        entrada = diccionario[codigo]
    elif codigo == siguiente:
        entrada = w + w[0]               # caso especial
    diccionario[siguiente] = w + entrada[0]
    siguiente += 1
    w = entrada
```

El decodificador va **un paso atrasado**: crea la entrada `w + (primera letra de lo siguiente)`.
A veces recibe justo el código que está por crear (pasa con `ABABABA`). Esa entrada solo puede ser
`w + w[0]`. Sin este `elif`, LZW fallaría con ese tipo de textos.

**El diccionario nunca se envía:** el decodificador lo reconstruye igual. Es **adaptativo**.

---

## 8. `bwt.py` — Burrows-Wheeler

**Idea:** reordenar para juntar letras iguales. No comprime sola: ayuda a RLE y Huffman.

### 8.1 Transformar

```python
FIN = "$"

def rotaciones_ordenadas(texto):
    t = texto + FIN
    return sorted(t[i:] + t[:i] for i in range(len(t)))

def transformar(texto):
    return "".join(rot[-1] for rot in rotaciones_ordenadas(texto))
```

- `t[i:] + t[:i]` es la rotación que empieza en `i` (`"BANANA$"`, `"ANANA$B"`, …).
- `sorted` las ordena; `rot[-1]` toma la última letra de cada una.
- BANANA → **`ANNB$AA`**.
- Complejidad didáctica: n rotaciones de largo n, ordenar cuesta O(n² log n). bzip2 usa
  *arreglos de sufijos*, O(n).

### 8.2 La inversa (propiedad LF)

```python
def inversa(ultima):
    vistos, rango = {}, []
    for c in ultima:                      # rango = cuántas veces apareció c antes
        rango.append(vistos.get(c, 0))
        vistos[c] = vistos.get(c, 0) + 1
    inicio, acumulado = {}, 0
    for c in sorted(vistos):              # dónde empieza cada letra en la 1.ª columna
        inicio[c] = acumulado
        acumulado += vistos[c]
    fila = inicio[FIN]                    # la fila que empieza con '$'
    resultado = []
    for _ in range(len(ultima)):
        c = ultima[fila]
        resultado.append(c)
        fila = inicio[c] + rango[fila]    # salto LF
    return "".join(reversed(resultado))[1:]
```

**La propiedad clave:** la primera columna es la última ordenada, y la k-ésima «A» de la última
columna es la misma k-ésima «A» de la primera. Así se puede saltar de una fila a la anterior del
texto.

**Traza** con `ANNB$AA`:
- `rango` = A:0, N:0, N:1, B:0, $:0, A:1, A:2
- `inicio` = $:0, A:1, B:4, N:5

| fila | ultima[fila] | salto: inicio + rango | nueva fila |
|---|---|---|---|
| 0 | A | 1 + 0 | 1 |
| 1 | N | 5 + 0 | 5 |
| 5 | A | 1 + 1 | 2 |
| 2 | N | 5 + 1 | 6 |
| 6 | A | 1 + 2 | 3 |
| 3 | B | 4 + 0 | 4 |
| 4 | $ | 0 + 0 | 0 |

Leído: `A N A N A B $` → al revés `$BANANA` → quitando el `$`: **BANANA**. ✔

> **Error real que encontramos:** al principio el código empezaba en `fila = 0` suponiendo que la
> fila 0 empieza con `$`. Falla con textos con espacios: el espacio (código 32) va antes que `$`
> (código 36). Por eso ahora es `fila = inicio[FIN]`. Lo detectó una prueba automática con
> «tres tristes tigres…».

### 8.3 Move-to-front

```python
def mover_al_frente(texto):
    lista = sorted(set(texto))
    for c in texto:
        i = lista.index(c)
        salida.append(i)
        lista.insert(0, lista.pop(i))
```

Cada letra se cambia por su posición en una lista y luego se mueve al frente. Una letra repetida
seguida da **0**. Tras la BWT hay muchos ceros, que Huffman comprime muy bien.

---

## 9. `aritmetica.py` — codificación aritmética

**Idea:** todo el mensaje = un número dentro de un intervalo de [0, 1).

### 9.1 El modelo

```python
def modelo(texto):
    conteos = Counter(texto)
    total = len(texto)
    tramos, acumulado = {}, Fraction(0)
    for s in sorted(conteos):
        p = Fraction(conteos[s], total)
        tramos[s] = (acumulado, acumulado + p)
        acumulado += p
    return tramos
```

`Fraction(3, 5)` es **exactamente** 3/5, no 0.6000000001. Para `AABAC`: A → [0, 3/5),
B → [3/5, 4/5), C → [4/5, 1).

### 9.2 Codificar = hacer zoom

```python
bajo, alto = Fraction(0), Fraction(1)
for s in texto:
    ancho = alto - bajo
    ini, fin = tramos[s]
    bajo, alto = bajo + ancho * ini, bajo + ancho * fin
```

El tramo del símbolo dentro del intervalo **actual**. Traza `AABAC`:

| lee | intervalo nuevo | ancho |
|---|---|---|
| A | [0, 3/5) | 0.6 |
| A | [0, 9/25) | 0.36 |
| B | [27/125, 36/125) | 0.072 |
| A | [27/125, 162/625) | 0.0432 |
| C | [783/3125, 162/625) | 0.00864 |

### 9.3 Elegir el número con menos bits

```python
def _binario_mas_corto(bajo, alto):
    k = 0
    while True:
        k += 1
        m = math.ceil(bajo * 2 ** k)          # menor múltiplo de 1/2^k que sea >= bajo
        if Fraction(m, 2 ** k) < alto:
            return format(m, "0%db" % k)
```

Prueba con 1 bit, 2 bits, …: con k bits los números posibles son `m / 2^k`. Para `AABAC`
(intervalo ≈ [0.25056, 0.25920)):

| k | m | m / 2^k | ¿< alto? |
|---|---|---|---|
| 1…6 | | 0.5, 0.5, 0.375, 0.3125, 0.281, 0.266 | no |
| 7 | 33 | 0.2578 | **sí** → `0100001` |

**7 bits.** La entropía dice 5 × 1.371 = 6.86 bits: casi exacto.

### 9.4 Decodificar

```python
x = Fraction(int(bits, 2), 2 ** len(bits))
for _ in range(n):
    pos = (x - bajo) / ancho
    for s, (ini, fin) in tramos.items():
        if ini <= pos < fin:
            salida.append(s)
            bajo, alto = ...        # el mismo zoom
```

Mira en qué tramo cae el número, emite ese símbolo y hace el mismo zoom. Necesita saber `n` (la
longitud del mensaje) para saber cuándo parar.

**Por qué gana a Huffman:** con 90 % A / 10 % B, Huffman gasta **1 bit por símbolo** como mínimo
(20 bits para 20 símbolos). La aritmética usó **8**; el límite de Shannon es 9.4 (que salga por
debajo es suerte de alineación; en promedio gasta la entropía + 1 o 2 bits).

---

## 10. `jpeg_dct.py` — imágenes con pérdida

Tubería: **bloques 8×8 → DCT → cuantización → zigzag + Huffman**.

### 10.1 DCT

```python
_COS = [[math.cos((2 * x + 1) * u * math.pi / 16) for u in range(8)] for x in range(8)]
_C = [1 / math.sqrt(2)] + [1.0] * 7

def dct2(bloque):
    F = [[0.0] * 8 for _ in range(8)]
    for u in range(8):
        for v in range(8):
            s = 0.0
            for x in range(8):
                for y in range(8):
                    s += bloque[x][y] * _COS[x][u] * _COS[y][v]
            F[u][v] = 0.25 * _C[u] * _C[v] * s
    return F
```

- Es la fórmula de la diapositiva, literal: 4 ciclos (u, v, x, y) = 8⁴ = 4 096 multiplicaciones
  por bloque.
- `_COS` se **precalcula** una vez (64 cosenos) para no recalcularlos en cada bloque.
- `F[0][0]` (DC) es el promedio del bloque × 8; las demás posiciones (AC) son detalles de mayor
  frecuencia cuanto más abajo-derecha.
- Antes de la DCT se resta 128 a cada píxel (valores de −128 a 127, centrados en 0).
- `idct2` es la inversa (misma estructura). **DCT → IDCT da el bloque original** (error 10⁻¹⁴):
  la DCT no pierde nada.

### 10.2 Cuantización: donde se pierde

```python
TABLA_Q50 = [[16, 11, 10, 16, 24, 40, 51, 61], ..., [72, 92, 95, 98, 112, 100, 103, 99]]

def tabla_calidad(calidad):
    escala = 5000 / calidad if calidad < 50 else 200 - 2 * calidad
    return [[max(1, min(255, int((q * escala + 50) // 100))) for q in fila] for fila in TABLA_Q50]

def cuantizar(F, Q):
    return [[int(round(F[u][v] / Q[u][v])) for v in range(8)] for u in range(8)]
```

- `TABLA_Q50` es la tabla **oficial** del estándar JPEG (calidad 50). Crece hacia abajo-derecha.
- `tabla_calidad` la escala como lo hace libjpeg: calidad 10 → escala 500 % (números 5 veces más
  grandes); calidad 90 → escala 20 %.
- `cuantizar` divide y **redondea**. Ejemplo: −55 / 11 = −5.0 → −5 (al reconstruir: −55, bien).
  Pero −2 / 10 = −0.2 → **0**: ese detalle desaparece para siempre.

En el bloque de ejemplo: **60 de 64** coeficientes quedan en 0.

### 10.3 Zigzag y símbolos

```python
def orden_zigzag():
    return sorted(((u, v) for u in range(8) for v in range(8)),
                  key=lambda p: (p[0] + p[1], p[0] if (p[0] + p[1]) % 2 else p[1]))
```

Ordena las 64 posiciones por **diagonal** (`u + v`); dentro de cada diagonal alterna la dirección
según si la diagonal es par o impar. Da el recorrido (0,0), (0,1), (1,0), (2,0), (1,1), (0,2)…

```python
def simbolos_entropia(Fq, dc_anterior):
    secuencia = [Fq[u][v] for u, v in ZIGZAG]
    simbolos = [("DC", secuencia[0] - dc_anterior)]       # DC: diferencia con el bloque anterior
    ...
    for c in ac[:ultimo_no_cero + 1]:
        if c == 0:
            ceros += 1
        else:
            simbolos.append((ceros, c))                   # (ceros antes, valor)
            ceros = 0
    simbolos.append("EOB")                                # "el resto son ceros"
```

Bloque de ejemplo → `[('DC', 2), (0, -5), (0, -9), (6, -1), 'EOB']`: **64 números → 5 símbolos**,
que luego van a nuestro Huffman.

### 10.4 Imagen completa y PSNR

`comprimir_imagen` recorre la imagen de 8 en 8, aplica DCT + cuantización + símbolos a cada bloque,
reconstruye con la inversa y al final pasa **todos** los símbolos por `huffman.codificar` para
estimar los bits. `psnr` mide el parecido: `10 · log10(255² / error cuadrático medio)`.

| calidad | % del original | PSNR |
|---|---|---|
| 90 | 16.1 % | 42.6 dB |
| 50 | 8.4 % | 32.2 dB |
| 10 | 3.4 % | 24.5 dB |

---

## 11. `audio.py` — enmascaramiento psicoacústico

### 11.1 FFT (divide y vencerás)

```python
def fft(x):
    n = len(x)
    if n == 1:
        return [complex(x[0])]
    pares = fft(x[0::2])
    impares = fft(x[1::2])
    resultado = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * impares[k]
        resultado[k] = pares[k] + t
        resultado[k + n // 2] = pares[k] - t
    return resultado
```

- Algoritmo de **Cooley-Tukey**: parte la señal en posiciones pares e impares, resuelve cada
  mitad recursivamente y las combina. Recurrencia T(n) = 2T(n/2) + O(n) → **O(n log n)** (igual
  que *merge sort*). La definición directa sería O(n²).
- `x[0::2]` = posiciones pares; `x[1::2]` = impares.
- Resultado: cuánta «energía» hay en cada frecuencia. Con 512 muestras a 8 000 Hz, cada casilla
  (*bin*) mide 8000/512 = 15.625 Hz.

### 11.2 La curva de enmascaramiento

```python
def curva_enmascaramiento(niveles, resolucion, caida_db_por_100hz=6.0, margen_db=20.0,
                          umbral_absoluto_db=-60.0):
    picos = [k for k in range(1, mitad) if niveles[k] > umbral_absoluto_db
             and niveles[k] >= niveles[k - 1] and niveles[k] >= niveles[k + 1]]
    for k in range(mitad + 1):
        umbral = umbral_absoluto_db
        for p in picos:
            if p == k:
                continue
            distancia_hz = abs(k - p) * resolucion
            enmascara = niveles[p] - margen_db - caida_db_por_100hz * distancia_hz / 100
            umbral = max(umbral, enmascara)
        umbrales.append(umbral)
```

- **Picos** = máximos locales (más altos que sus vecinos) y audibles.
- Para cada frecuencia `k`, cada pico **la tapa** con una curva: 20 dB por debajo del pico justo
  al lado, y bajando 6 dB por cada 100 Hz de distancia.
- El umbral final es el **máximo** entre el umbral absoluto de audición (−60 dB) y lo que tapan
  todos los picos.

### 11.3 Borrar lo que no se oye

```python
for k in range(mitad + 1):
    if niveles[k] > umbrales[k]:
        Y[k] = X[k]
        if k not in (0, mitad):
            Y[n - k] = X[n - k]          # simetría de una señal real
        conservados += 1
reconstruida = [v.real for v in ifft(Y)]
```

Lo que está por encima del umbral se copia; lo demás queda en 0 (se borra). Una señal real tiene
espectro **simétrico**, por eso se copia también la casilla espejo `n − k`.

**Resultado:** el tono de 1156 Hz (−40 dB) se borra porque está a 156 Hz del fuerte de 1000 Hz:
umbral ≈ −4.4 − 20 − 6·1.56 = −33.8 dB, y −40 < −33.8. El de 2000 Hz tiene el **mismo volumen**
pero está a 1000 Hz de distancia: lo que tapa el pico es −4.4 − 20 − 60 = −84.4 dB, así que manda
el umbral absoluto (−60 dB), y −40 > −60 → **se conserva**.

> Nyquist: todas las frecuencias deben ser < 4000 Hz (la mitad de 8000). Un tono de 6000 Hz
> aparecería disfrazado de 2000 Hz (*aliasing*).

---

## 12. `video.py` — cuadros I/P y vectores de movimiento

### 12.1 SAD

```python
def sad(ref, cur, bx, by, dx, dy):
    total = 0
    for y in range(BLOQUE):
        for x in range(BLOQUE):
            total += abs(cur[by + y][bx + x] - ref[by + y + dy][bx + x + dx])
    return total
```

*Sum of Absolute Differences*: qué tan distinto es el bloque actual del bloque desplazado
`(dx, dy)` en el cuadro anterior. 0 = idénticos.

### 12.2 Buscar el mejor desplazamiento

```python
def estimar_movimiento(ref, cur):
    for by in range(0, alto, BLOQUE):
        for bx in range(0, ancho, BLOQUE):
            mejor = (sad(ref, cur, bx, by, 0, 0), 0, 0)     # preferir (0,0) si empata
            for dy in range(-BUSQUEDA, BUSQUEDA + 1):
                for dx in range(-BUSQUEDA, BUSQUEDA + 1):
                    if <el bloque desplazado cabe en la imagen>:
                        s = sad(ref, cur, bx, by, dx, dy)
                        if s < mejor[0]:
                            mejor = (s, dx, dy)
            vectores[(bx, by)] = (mejor[1], mejor[2])
```

Búsqueda **exhaustiva**: para cada bloque prueba los 9 × 9 = 81 desplazamientos de −4 a +4. Costo
por cuadro: (#bloques) × 81 × 64. Los códecs reales usan búsquedas más rápidas (diamante,
jerárquica).

### 12.3 Predicción y residuo

```python
pred = predecir(referencia, vectores, ancho, alto)        # copiar bloques según los vectores
residuo = [[cur[y][x] - pred[y][x] ...]]                   # lo que la predicción no acertó
flujo.append(("P", vectores, residuo))
```

El decodificador hace `pred + residuo` y recupera el cuadro exacto. `costo` cuenta lo que hay que
guardar: un cuadro I = todos los píxeles; un P = 2 números por vector + los valores del residuo
distintos de 0.

**Cómo leer `(−2, −1)`:** el contenido estaba 2 px a la izquierda y 1 arriba en el cuadro anterior
→ el objeto **se movió 2 a la derecha y 1 abajo**.

---

## 13. `archivo.py` — compresor real (mini-DEFLATE)

Comprime **cualquier archivo**, lo guarda en un formato propio `.edd` y lo descomprime.

### 13.1 Escribir bits en bytes

```python
class EscritorBits:
    def escribir(self, valor, cantidad_bits):
        self._acum = (self._acum << cantidad_bits) | valor
        self._n += cantidad_bits
        while self._n >= 8:
            self._n -= 8
            self.bytes.append((self._acum >> self._n) & 0xFF)
        self._acum &= (1 << self._n) - 1
```

Los archivos se guardan en bytes (8 bits), pero los códigos Huffman tienen longitudes variables.
`_acum` acumula bits pendientes como un entero:

| operación | qué hace |
|---|---|
| `acum << cantidad` \| `valor` | Corre lo pendiente a la izquierda y pega los bits nuevos al final |
| `while n >= 8` | Cada vez que hay 8 o más, saca los **8 de más a la izquierda** como un byte |
| `& 0xFF` | Se queda solo con 8 bits (0xFF = 11111111) |
| `acum &= (1 << n) − 1` | Borra los bits ya escritos; deja solo los `n` pendientes |

**Traza:** escribir `10` (2 bits), luego `110` (3), luego `1111` (4):
`acum` = `10` → `10110` → `101101111` (9 bits) → sale el byte `10110111` (183) y queda `1`.
`terminar()` rellena con ceros: `10000000` (128).

`LectorBits.leer_bit()` hace lo contrario: `byte >> (7 − pos % 8) & 1`.

### 13.2 Método 1: Huffman sobre bytes

```python
def comprimir_huffman(datos):
    longitudes = _longitudes(Counter(datos), 256)          # árbol -> longitud por byte
    tabla = _tabla_codificacion(longitudes)                # longitudes -> códigos canónicos
    for b in datos:
        codigo, l = tabla[b]
        w.escribir(codigo, l)
    cabecera = FIRMA + struct.pack("<BI", METODO_HUFFMAN, len(datos)) + bytes(longitudes)
    return cabecera + w.terminar()
```

`struct.pack("<BI", ...)` escribe 1 byte (`B`, el método) y un entero de 4 bytes (`I`, el tamaño)
en orden *little-endian* (`<`).

### 13.3 Método 2: mini-DEFLATE = LZ77 + Huffman

```python
def comprimir_deflate(datos):
    tokens = lz77.codificar(datos)
    simbolos = [t[1] if t[0] == "L" else 256 + t[2] - 3 for t in tokens]
    ...
    for t, s in zip(tokens, simbolos):
        codigo, l = tabla[s]
        w.escribir(codigo, l)                    # literal o longitud, con Huffman
        if t[0] == "R":
            w.escribir(t[1] - 1, BITS_DISTANCIA) # distancia con 15 bits fijos
```

Un **solo alfabeto** de 513 símbolos para Huffman: 0–255 = byte literal; 256–511 = «copia de
longitud `símbolo − 256 + 3`». Así Huffman también aprende qué longitudes de copia son comunes.

### 13.4 Formato `.edd`

| bytes | contenido |
|---|---|
| 4 | `EDD2` (firma: para reconocer el formato) |
| 1 | método (1 = huffman, 2 = deflate) |
| 4 | tamaño original |
| 256 ó 513 | longitud del código de cada símbolo (gracias a los **canónicos**, no el árbol) |
| resto | los bits |

### 13.5 Decodificar un símbolo

```python
def _leer_simbolo(lector, tabla_dec):
    codigo = longitud = 0
    while True:
        codigo = (codigo << 1) | lector.leer_bit()
        longitud += 1
        if (longitud, codigo) in tabla_dec:
            return tabla_dec[(longitud, codigo)]
```

Lee bit a bit y pregunta a una **tabla hash** `(longitud, código) → símbolo`. Se usa la longitud
en la clave porque `0` y `00` serían el mismo número.

### 13.6 Resultados con el guion (16 721 bytes)

| método | % del original |
|---|---|
| RLE (nuestro) | 198.3 % |
| Huffman (nuestro) | 60.7 % |
| mini-DEFLATE (nuestro) | 48.8 % |
| zlib (DEFLATE real) | 40.5 % |
| bz2 (BWT) | 37.5 % |
| lzma / xz | 39.1 % |

El límite para un compresor que solo mira frecuencias de bytes es 9 812 bytes (58.7 %). Huffman
queda justo por encima (no puede bajarlo); LZ77 + Huffman **sí** lo baja porque aprovecha palabras
repetidas. `medir()` verifica que **todos** devuelvan el archivo idéntico.

---

## 14. Tabla resumen de complejidades

| Algoritmo / operación | Tiempo | Estructura clave |
|---|---|---|
| Contar frecuencias | O(n) | tabla hash (`Counter`) |
| RLE codificar / decodificar | O(n) | — |
| Heap: ver mínimo | O(1) | arreglo |
| Heap: insertar / extraer | O(log n) | árbol completo en arreglo |
| Huffman: construir árbol | O(k log k) | min-heap + árbol binario |
| Huffman: generar códigos | O(k) | recorrido DFS |
| Huffman: codificar | O(n) | tabla hash símbolo → código |
| LZ77 sin tabla hash | O(n · ventana) | — |
| LZ77 con tabla hash | ≈ O(n) práctico | tabla hash trío → posiciones |
| LZ77 decodificar | O(n) | — |
| LZW | O(n) promedio | tabla hash secuencia → código |
| BWT (didáctica) / inversa | O(n² log n) / O(n log n) | ordenamiento |
| DCT de un bloque 8×8 | O(8⁴) = constante | — |
| FFT | O(n log n) | divide y vencerás |
| Block matching por cuadro | O(bloques · 81 · 64) | — |

(n = tamaño de los datos, k = número de símbolos distintos)

---

## 15. Conceptos de Python que aparecen en el código

| En el código | Qué significa |
|---|---|
| `Counter(datos)` | Diccionario que cuenta apariciones |
| `{s: v for s, v in ...}` | Comprensión de diccionario |
| `a, b = b, a` | Intercambio sin variable auxiliar |
| `(freq, -orden, nodo) < (...)` | Las tuplas se comparan elemento por elemento |
| `x[0::2]`, `x[1::2]` | Posiciones pares / impares |
| `t[i:] + t[:i]` | Rotación de un texto |
| `dict.setdefault(k, [])` | Devuelve la lista de `k`, creándola vacía si no existía |
| `deque` | Cola doble: agregar/sacar por ambos extremos en O(1) |
| `Fraction(3, 5)` | Fracción exacta, sin errores de redondeo |
| `x << n`, `x >> n`, `&`, `\|` | Operaciones de bits: correr a izquierda/derecha, Y, O |
| `format(6, "03b")` | `"110"`: número en binario con 3 dígitos |
| `struct.pack("<BI", ...)` | Convertir números en bytes con un formato fijo |
| `__slots__` | Fija los atributos de una clase (menos memoria) |
| `def f(...): def g(...):` | Función interna (recursiva en `generar_codigos`) |

---

## 16. Preguntas que nos pueden hacer (con respuesta)

**¿Por qué implementaron el heap en vez de usar `heapq`?**
Para mostrar cómo funciona por dentro (es el tema del curso). `heapq` hace exactamente lo mismo:
`_subir` y `_bajar` son su `_siftdown` / `_siftup`.

**¿Por qué sus códigos de Huffman no son iguales a los de la diapositiva?**
El árbol da otros códigos con **las mismas longitudes** (ambos son óptimos: 23 bits). Los de la
diapositiva son los **canónicos**, que el código también calcula (`codigos_canonicos`).

**¿Huffman siempre es óptimo?**
Es óptimo entre los códigos que asignan un número **entero** de bits a cada símbolo por separado.
La aritmética puede ganarle porque usa fracciones de bit, y LZ77 porque mira secuencias.

**¿Se puede comprimir cualquier cosa? ¿Comprimir dos veces ayuda?**
No. Un archivo ya comprimido o aleatorio casi no tiene redundancia (su entropía es máxima); el RLE
incluso lo agranda. Ningún compresor sin pérdida puede achicar **todos** los archivos (principio
del palomar: hay menos archivos cortos que largos).

**¿Para qué sirve la tabla hash en LZ77?**
Para responder en O(1) «¿dónde apareció antes este trío?». Sin ella se compara contra toda la
ventana: en nuestra prueba, 8 961 comparaciones contra 935.

**¿Dónde se pierde información en JPEG?**
Solo en la **cuantización** (dividir y redondear). La DCT y Huffman son reversibles.

**¿La IA rompe el límite de Shannon?**
No. Usa un modelo mejor (que ve más contexto), y con un modelo mejor el límite es más bajo.

**¿Cómo sabemos que el código funciona?**
`python -m unittest discover -s tests -v`: 25 pruebas automáticas verifican los números de las
diapositivas y que todo lo sin pérdida vuelva idéntico, incluso con datos aleatorios.
