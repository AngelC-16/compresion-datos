# Explicación detallada del código

**«¿Cómo cabe todo? Compresión de datos»** · Estructuras de Datos II · Universidad del Norte
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

Este documento explica **el código de los algoritmos** (carpeta `compresion/`): cada función, línea
por línea, con trazas hechas a mano usando los mismos ejemplos de las diapositivas. **No explica la
interfaz web** (`app.py`, `web/`, `compresion/api.py`): esa parte solo muestra en pantalla lo que
calculan los módulos que se explican aquí.

### Cómo leer este documento

Cada algoritmo sigue el mismo orden:

1. **La idea** — qué problema resuelve, en palabras simples.
2. **La teoría que hay que saber** — lo mínimo para entender el código.
3. **El código completo** — copiado tal cual del proyecto, con **números de línea** a la izquierda
   (`12 │`). Las explicaciones dicen «L12» para referirse a la línea 12 de ese bloque.
4. **Línea por línea** — qué hace cada línea y **por qué** está ahí.
5. **Traza a mano** — los valores de las variables en cada vuelta, con el ejemplo de la diapositiva.
6. **Complejidad** — tiempo y memoria, justificados.
7. **Casos borde y errores típicos** — qué podría salir mal y cómo lo evita el código.
8. **Para experimentar** — cosas que pueden probar para entenderlo mejor.

> Para ver cualquier traza en vivo: `python app.py` y abrir la sección correspondiente.
> Para verla en texto: `python demo.py <seccion>` (por ejemplo `python demo.py huffman`).

---

## Índice

- [Parte 0 · Conceptos previos](#parte-0--conceptos-previos)
- [Parte 1 · `entropia.py` — el límite de Shannon](#parte-1--entropiapy--el-límite-de-shannon)
- [Parte 2 · `adaptativa.py` — estático vs. adaptativo](#parte-2--adaptativapy--estático-vs-adaptativo)
- [Parte 3 · `rle.py` — Run-Length Encoding](#parte-3--rlepy--run-length-encoding)
- [Parte 4 · `estructuras.py` — min-heap y nodo del árbol](#parte-4--estructuraspy--min-heap-y-nodo-del-árbol)
- [Parte 5 · `huffman.py` — codificación Huffman](#parte-5--huffmanpy--codificación-huffman)
- [Parte 6 · `lz77.py` — ventana deslizante y tabla hash](#parte-6--lz77py--ventana-deslizante-y-tabla-hash)
- [Parte 7 · `lzw.py` — diccionario dinámico](#parte-7--lzwpy--diccionario-dinámico)
- [Parte 8 · `bwt.py` — Burrows-Wheeler](#parte-8--bwtpy--burrows-wheeler)
- [Parte 9 · `aritmetica.py` — codificación aritmética](#parte-9--aritmeticapy--codificación-aritmética)
- [Parte 10 · `jpeg_dct.py` — imágenes con pérdida](#parte-10--jpeg_dctpy--imágenes-con-pérdida)
- [Parte 11 · `audio.py` — enmascaramiento psicoacústico](#parte-11--audiopy--enmascaramiento-psicoacústico)
- [Parte 12 · `video.py` — cuadros I/P y vectores de movimiento](#parte-12--videopy--cuadros-ip-y-vectores-de-movimiento)
- [Parte 13 · `archivo.py` — compresor real de archivos](#parte-13--archivopy--compresor-real-de-archivos)
- [Parte 14 · Las pruebas automáticas](#parte-14--las-pruebas-automáticas)
- [Parte 15 · Resumen de complejidades](#parte-15--resumen-de-complejidades)
- [Parte 16 · Glosario de Python usado](#parte-16--glosario-de-python-usado)
- [Parte 17 · Preguntas que nos pueden hacer](#parte-17--preguntas-que-nos-pueden-hacer)

---

## Parte 0 · Conceptos previos

### 0.1 Bits, bytes y ASCII

- Un **bit** es un 0 o un 1. Un **byte** son 8 bits: permite 2⁸ = 256 valores (0 a 255).
- En **ASCII** cada letra ocupa 1 byte: `A` = 65 = `01000001`. Por eso «ABRACADABRA» (11 letras)
  ocupa 11 × 8 = **88 bits** sin comprimir.
- Comprimir es encontrar una forma de escribir lo mismo con **menos bits**.

### 0.2 Todo compresor tiene dos partes

| Parte | Pregunta que responde | Ejemplos en el proyecto |
|---|---|---|
| **Modelo** | ¿Qué tan probable / predecible es lo que viene? | Contar frecuencias (`entropia`, `huffman`), la ventana de lo ya leído (`lz77`), el diccionario (`lzw`) |
| **Codificador** | Dada esa predicción, ¿cómo lo escribo en bits? | Códigos de Huffman, tokens `(retrocede, copia)`, un número en [0,1) (aritmética) |

Un buen modelo + un buen codificador = buena compresión. La entropía (Parte 1) mide qué tan bueno
puede ser el resultado **para un modelo dado**.

### 0.3 Código de longitud fija vs. variable, y «libre de prefijo»

- **Fija:** todas las letras gastan lo mismo (ASCII: 8 bits). Fácil de leer, desperdicia espacio.
- **Variable:** lo frecuente gasta menos (Huffman). Problema: ¿dónde termina cada letra?
- Solución: códigos **libres de prefijo**: ningún código es el comienzo de otro. Con
  `A=0, B=10, R=110`, al leer `0` ya sé que es A (ningún otro empieza con 0). Al leer `1` sé que
  no terminó; `10` es B; `11` sigue; `110` es R.

### 0.4 Logaritmo en base 2

`log2(x)` responde «¿2 elevado a qué da x?». `log2(8) = 3`, `log2(1/2) = −1`, `log2(1/8) = −3`.
Importa porque **con k bits se distinguen 2^k cosas**: para elegir entre 8 opciones igual de
probables hacen falta log2(8) = 3 bits. Un evento de probabilidad p «vale» −log2(p) bits.

### 0.5 Sin pérdida vs. con pérdida en el código

- **Sin pérdida:** siempre existe `decodificar(codificar(x)) == x`. Las pruebas lo verifican
  (Parte 14).
- **Con pérdida:** se mide **cuánto** se parece el resultado (PSNR en imágenes, error RMS en
  audio). No hay igualdad.

### 0.6 Notación de complejidad

- **n** = tamaño de la entrada (letras, bytes, muestras). **k** = número de símbolos **distintos**.
- O(1) constante · O(log n) logarítmico · O(n) lineal · O(n log n) · O(n²) cuadrático.

---

## Parte 1 · `entropia.py` — el límite de Shannon

### 1.1 La idea

Antes de comprimir conviene saber **cuánto se puede comprimir como máximo**. Claude Shannon (1948)
lo respondió con la **entropía**: el mínimo promedio de bits por símbolo para guardar un mensaje
**sin perder nada**, si solo sabemos con qué frecuencia aparece cada símbolo.

### 1.2 La teoría

$$H = -\sum_x p(x)\,\log_2 p(x)$$

- `−log2 p(x)` = **información** o **sorpresa** de ver x. p = 1 → 0 bits (no sorprende);
  p = 1/2 → 1 bit; p = 1/8 → 3 bits.
- H = **promedio ponderado** de la sorpresa: cada sorpresa multiplicada por qué tan seguido ocurre.
- **Redundancia** = lo que sobra = `1 − (bits mínimos / bits usados)`.

### 1.3 Código: contar frecuencias

`compresion/entropia.py` → `frecuencias`

```python
1 │ def frecuencias(datos):
2 │     """Cuenta cuántas veces aparece cada símbolo.
3 │ 
4 │     `Counter` es internamente una TABLA HASH (diccionario de Python): cada
5 │     actualización cuesta O(1) en promedio, así que contar todo cuesta O(n).
6 │     """
7 │     return Counter(datos)
```

- **L7** `Counter(datos)` recorre los datos y cuenta cuántas veces aparece cada elemento.
  Internamente es un `dict` (una **tabla hash**): sumar 1 a un conteo cuesta O(1) promedio.
- Sirve igual para `str` (cuenta letras) y para `bytes` (cuenta números 0–255): Python itera
  ambos elemento por elemento.
- Ejemplo: `frecuencias("ABRACADABRA")` → `Counter({'A': 5, 'B': 2, 'R': 2, 'C': 1, 'D': 1})`.
- **Complejidad:** O(n) tiempo, O(k) memoria.

### 1.4 Código: probabilidades

`compresion/entropia.py` → `probabilidades`

```python
1 │ def probabilidades(datos):
2 │     """Convierte las frecuencias en probabilidades p(x) = veces(x) / total."""
3 │     total = len(datos)
4 │     return {simbolo: veces / total for simbolo, veces in frecuencias(datos).items()}
```

- **L3** `total` = número de símbolos.
- **L4** comprensión de diccionario: por cada `(símbolo, veces)` guarda `veces / total`.
- ABRACADABRA → `{'A': 0.4545, 'B': 0.1818, 'R': 0.1818, 'C': 0.0909, 'D': 0.0909}`. La suma
  siempre da 1.

### 1.5 Código: la fórmula

`compresion/entropia.py` → `entropia_de_distribucion`

```python
1 │ def entropia_de_distribucion(probs):
2 │     """H = −Σ p·log2(p) para una lista/diccionario de probabilidades.
3 │ 
4 │     Los términos con p = 0 se omiten (por convención 0·log2(0) = 0).
5 │     """
6 │     valores = probs.values() if isinstance(probs, dict) else probs
7 │     h = -sum(p * math.log2(p) for p in valores if p > 0)
8 │     return h if h > 0 else 0.0           # evita mostrar "-0.000"
```

- **L6** acepta dos formatos: un diccionario `{símbolo: p}` (usa sus valores) o una lista
  `[0.9, 0.1]` (la moneda). `isinstance` pregunta el tipo.
- **L7** la fórmula literal. El generador `p * math.log2(p) for p in valores if p > 0`:
  - `if p > 0`: `log2(0)` no existe (−∞). Por convención `0 · log2(0) = 0`, así que se omite.
  - Cada término es **negativo** (p < 1 ⇒ log2 p < 0); el `-` de adelante vuelve positivo H.
- **L8** con un solo símbolo, la suma es `-0.0` (cero negativo de los flotantes). Se cambia por
  `0.0` solo para que se vea bien.

### 1.6 Código: entropía de unos datos e información

`compresion/entropia.py` → `entropia`

```python
1 │ def entropia(datos):
2 │     """Entropía (bits por símbolo) de una secuencia concreta de datos."""
3 │     if not datos:
4 │         return 0.0
5 │     return entropia_de_distribucion(probabilidades(datos))
```

`compresion/entropia.py` → `informacion`

```python
1 │ def informacion(p):
2 │     """Información (sorpresa) en bits de un evento de probabilidad p: −log2 p."""
3 │     return -math.log2(p)
```

- `entropia`: **L3–4** si no hay datos, H = 0 (evita dividir por cero). **L5** encadena:
  datos → probabilidades → fórmula.
- `informacion`: la sorpresa de un solo evento.

### 1.7 Código: análisis completo

`compresion/entropia.py` → `analisis`

```python
 1 │ def analisis(datos, bits_por_simbolo_original=8):
 2 │     """Resume cuánto se podría comprimir `datos` como máximo (sin pérdida),
 3 │     usando un modelo que solo mira la frecuencia de cada símbolo.
 4 │ 
 5 │     Devuelve un diccionario con:
 6 │       - bits_originales:  tamaño con un código fijo (p. ej. ASCII = 8 bits)
 7 │       - entropia:         H en bits/símbolo
 8 │       - bits_minimos:     n · H  (límite teórico)
 9 │       - redundancia:      porcentaje que sobra en la representación original
10 │     """
11 │     n = len(datos)
12 │     h = entropia(datos)
13 │     bits_originales = n * bits_por_simbolo_original
14 │     bits_minimos = n * h
15 │     redundancia = 1 - (bits_minimos / bits_originales) if bits_originales else 0
16 │     return {
17 │         "simbolos": n,
18 │         "distintos": len(set(datos)),
19 │         "entropia": h,
20 │         "bits_originales": bits_originales,
21 │         "bits_minimos": bits_minimos,
22 │         "redundancia": redundancia,
23 │     }
```

- **L11–14** n, H, bits originales (n × 8) y bits mínimos (n × H).
- **L15** redundancia. El `if bits_originales else 0` evita dividir por cero con datos vacíos.
- **L18** `len(set(datos))` = símbolos distintos (`set` elimina repetidos).

### 1.8 Trazas a mano

**Moneda cargada `[0.9, 0.1]`:**

| p | log2 p | p · log2 p |
|---|---|---|
| 0.9 | −0.152 | −0.137 |
| 0.1 | −3.322 | −0.332 |
| | suma | −0.469 |

H = −(−0.469) = **0.469 bits** (diapositiva: 0,47). Moneda justa: −(0.5·(−1) + 0.5·(−1)) = **1 bit**.

**ABRACADABRA:**

| símbolo | veces | p | −log2 p (sorpresa) | p · (−log2 p) |
|---|---|---|---|---|
| A | 5 | 0.455 | 1.138 | 0.517 |
| B | 2 | 0.182 | 2.459 | 0.447 |
| R | 2 | 0.182 | 2.459 | 0.447 |
| C | 1 | 0.091 | 3.459 | 0.315 |
| D | 1 | 0.091 | 3.459 | 0.315 |
| | | | **H** | **2.040** |

- Bits mínimos = 11 × 2.040 = **22.4** · originales = 88 · redundancia = 1 − 22.4/88 = **74.5 %**.

### 1.9 Lo más importante: el modelo importa

Esta es la entropía de **orden 0**: solo mira frecuencias, no el orden. Por eso:

| texto | H (orden 0) | ¿realmente es tan impredecible? |
|---|---|---|
| `AAAAAAAAAAAAAAAA` | 0 | No: es totalmente predecible ✔ |
| `ABABABABABABABAB` | 1 bit | **No**: después de A siempre viene B, pero el modelo no lo ve |
| `q7#Lz!0pW@k9&Xr2` | 4 bits | Sí: 16 símbolos distintos, cada uno una vez |

Los algoritmos que miran **contexto** (LZ77, LZW, BWT) aprovechan el orden y bajan de esta cifra
(en la Parte 13 se ve: LZ77 + Huffman comprime el guion por debajo del límite de orden 0).

### 1.10 Para experimentar

- `python -c "from compresion.entropia import *; print(entropia('hola mundo'))"`
- Probar con `"AB"*50` vs. `"A"*50+"B"*50`: dan la **misma** H. ¿Por qué? (Respuesta: tienen las
  mismas frecuencias; el orden no cuenta para este modelo.)

---

## Parte 2 · `adaptativa.py` — estático vs. adaptativo

### 2.1 La idea

Diapositiva 6: un modelo **estático** cuenta todo primero (dos pasadas) y usa la misma tabla para
todo el archivo; un modelo **adaptativo** aprende mientras lee (una pasada). Para compararlos de
forma justa, este módulo no genera bits reales: calcula el **costo ideal** `−log2 p` de cada
símbolo, que es lo que gastaría un codificador perfecto (el aritmético se acerca mucho).

### 2.2 Código: estático

`compresion/adaptativa.py` → `costo_estatico`

```python
1 │ def costo_estatico(texto):
2 │     """Bits = Σ −log2 p(x) con p fijas calculadas sobre TODO el texto,
3 │     más el costo de enviar la tabla (aprox. 8 bits por símbolo + 8 por conteo)."""
4 │     conteos = Counter(texto)
5 │     n = len(texto)
6 │     datos = sum(-math.log2(conteos[s] / n) for s in texto)
7 │     tabla = len(conteos) * 16
8 │     return datos, tabla
```

- **L4** primera pasada: contar todo el texto.
- **L6** segunda pasada: cada símbolo cuesta `−log2(veces/n)`. Es la misma cifra esté donde esté.
- **L7** la tabla viaja con el archivo: estimamos 16 bits por entrada (8 para el símbolo y 8 para
  su conteo).
- **L8** devuelve los dos por separado para poder mostrarlos.

### 2.3 Código: adaptativo

`compresion/adaptativa.py` → `costo_adaptativo`

```python
 1 │ def costo_adaptativo(texto, alfabeto, memoria=None, detalle=None):
 2 │     """Bits = Σ −log2 p(x) donde p se calcula SOLO con lo leído hasta ahora.
 3 │ 
 4 │     * Empieza sabiendo nada: todos los símbolos con conteo 1 (suavizado de
 5 │       Laplace, para que ninguno tenga probabilidad 0).
 6 │     * Tras codificar un símbolo, se suma 1 a su conteo.
 7 │     * `memoria` (opcional): solo recuerda los últimos `memoria` símbolos
 8 │       (ventana deslizante). Así se adapta rápido si el contenido CAMBIA.
 9 │     """
10 │     conteos = {s: 1 for s in alfabeto}
11 │     total = len(alfabeto)
12 │     recientes = deque()
13 │     bits = 0.0
14 │     for i, s in enumerate(texto):
15 │         p = conteos[s] / total
16 │         costo = -math.log2(p)
17 │         bits += costo
18 │         if detalle is not None:
19 │             detalle.append((i, s, p, costo))
20 │         # Actualizar el modelo DESPUÉS de codificar (el decodificador hará lo mismo)
21 │         conteos[s] += 1
22 │         total += 1
23 │         if memoria is not None:
24 │             recientes.append(s)
25 │             if len(recientes) > memoria:
26 │                 viejo = recientes.popleft()
27 │                 conteos[viejo] -= 1
28 │                 total -= 1
29 │     return bits
```

| Línea | Qué hace | Por qué |
|---|---|---|
| L10 | Todos los conteos empiezan en 1 | **Suavizado de Laplace**: si un conteo fuera 0, p = 0 y −log2(0) = ∞ |
| L11 | `total` = suma de los conteos | Necesario para calcular p |
| L12 | `deque()` | Cola doble: `append` y `popleft` en O(1). Guarda lo reciente |
| L15 | p con lo visto **hasta ahora** | Es lo único que sabría el decodificador en ese momento |
| L16–17 | Costo del símbolo y acumulado | |
| L18–19 | Guarda el detalle si se pidió | Lo usan la demo y la interfaz |
| L21–22 | Actualiza el modelo **después** | Si actualizara antes, el decodificador no podría imitarlo |
| L23–28 | Con `memoria`, olvida lo más viejo | Ventana deslizante: se adapta rápido a cambios |

**Idea clave del adaptativo:** el codificador y el decodificador empiezan igual y hacen las mismas
actualizaciones con los mismos datos ⇒ siempre tienen la misma tabla ⇒ **no hace falta enviarla**.

### 2.4 Traza con `"A"×50 + "B"×50`, alfabeto `AB`, sin memoria

| i | lee | conteos antes (A, B) | p | costo |
|---|---|---|---|---|
| 0 | A | (1, 1) | 1/2 = 0.500 | 1.00 |
| 1 | A | (2, 1) | 2/3 = 0.667 | 0.58 |
| 2 | A | (3, 1) | 3/4 = 0.750 | 0.42 |
| 49 | A | (50, 1) | 50/51 = 0.980 | 0.03 |
| 50 | B | (51, 1) | 1/52 = 0.019 | **5.70** |
| 51 | B | (51, 2) | 2/53 = 0.038 | 4.73 |
| 99 | B | (51, 50) | 50/101 = 0.495 | 1.01 |

Totales: estático **100 + 32 = 132** bits · adaptativo **103** · adaptativo con memoria 8 **27.2**.

¿Por qué la memoria ayuda tanto? Con memoria 8, cuando llegan las B el modelo «olvida» las A en 8
pasos y la B pasa enseguida a costar casi 0. Sin memoria, recuerda las 50 A para siempre.

### 2.5 Para experimentar

- Con `"ABRACADABRA"*3` (texto estable) el estático gana en datos (67.3) pero pierde por la tabla
  (80 bits): 147.3 vs. 74.3 del adaptativo.

---

## Parte 3 · `rle.py` — Run-Length Encoding

### 3.1 La idea

`AAAAABBBCC` → `(5,A) (3,B) (2,C)`: 10 letras → 6 símbolos. Funciona con **rachas** largas.

### 3.2 Código: codificar

`compresion/rle.py` → `codificar`

```python
 1 │ def codificar(datos):
 2 │     """Devuelve la lista de rachas [(cantidad, simbolo), ...]."""
 3 │     rachas = []
 4 │     i = 0
 5 │     n = len(datos)
 6 │     while i < n:
 7 │         simbolo = datos[i]
 8 │         cantidad = 1
 9 │         # Avanzamos mientras el siguiente símbolo sea igual al actual.
10 │         while i + cantidad < n and datos[i + cantidad] == simbolo:
11 │             cantidad += 1
12 │         rachas.append((cantidad, simbolo))
13 │         i += cantidad
14 │     return rachas
```

| Línea | Qué hace |
|---|---|
| L3–5 | Lista de salida, índice `i` (inicio de la racha actual) y largo `n` |
| L6 | Mientras queden datos |
| L7 | El símbolo que se va a contar |
| L8 | Ya hay uno |
| L10 | Avanza mientras el siguiente sea igual. **Orden importante:** primero `i + cantidad < n` (no salirse); como `and` evalúa en corto circuito, si es falso **no** se ejecuta `datos[i + cantidad]` (que daría `IndexError`) |
| L12 | Guarda la tupla `(cantidad, símbolo)` |
| L13 | **Salta** toda la racha |

**Traza `AAAAABBBCC`** (n = 10):

| vuelta | i | símbolo | comparaciones del while interno | cantidad | se guarda | nuevo i |
|---|---|---|---|---|---|---|
| 1 | 0 | A | d[1]=A ✔, d[2]=A ✔, d[3]=A ✔, d[4]=A ✔, d[5]=B ✘ | 5 | (5, A) | 5 |
| 2 | 5 | B | d[6]=B ✔, d[7]=B ✔, d[8]=C ✘ | 3 | (3, B) | 8 |
| 3 | 8 | C | d[9]=C ✔, 8+2 < 10 ✘ (fin) | 2 | (2, C) | 10 |

**Complejidad: O(n)**, aunque haya dos `while` anidados. Razón: el `while` interno avanza
`cantidad` posiciones y el externo **salta** esas mismas posiciones (L13). Cada posición se mira
una sola vez en total. Memoria: O(número de rachas).

### 3.3 Código: decodificar

`compresion/rle.py` → `decodificar`

```python
 1 │ def decodificar(rachas):
 2 │     """Operación inversa: expande cada (cantidad, simbolo)."""
 3 │     partes = [simbolo * cantidad for cantidad, simbolo in rachas]
 4 │     # Si los símbolos son caracteres, unimos en un string; si no, en una lista.
 5 │     if partes and isinstance(partes[0], str):
 6 │         return "".join(partes)
 7 │     resultado = []
 8 │     for cantidad, simbolo in rachas:
 9 │         resultado.extend([simbolo] * cantidad)
10 │     return resultado
```

- **L3** en Python `"A" * 5 == "AAAAA"`: se repite cada símbolo.
- **L5–6** si son letras, se pegan con `"".join` (más eficiente que sumar strings uno por uno).
- **L7–10** si son otra cosa (números, píxeles), se arma una lista con `extend`.

### 3.4 Código: utilidades

`compresion/rle.py` → `a_texto`

```python
1 │ def a_texto(rachas):
2 │     """Representación compacta tipo '5A3B2C' (solo para mostrar)."""
3 │     return "".join("%d%s" % (cantidad, simbolo) for cantidad, simbolo in rachas)
```

`compresion/rle.py` → `tamano_en_simbolos`

```python
1 │ def tamano_en_simbolos(rachas):
2 │     """Cada racha ocupa 2 "casillas": la cantidad y el símbolo."""
3 │     return 2 * len(rachas)
```

- `a_texto` produce `5A3B2C`. `tamano_en_simbolos` cuenta **2 casillas por racha** (la cantidad y
  el símbolo): es la medida que usa la diapositiva («6 símbolos»).

### 3.5 Código: versión por bytes (para archivos)

`compresion/rle.py` → `codificar_bytes`

```python
 1 │ def codificar_bytes(datos: bytes) -> bytes:
 2 │     salida = bytearray()
 3 │     i = 0
 4 │     while i < len(datos):
 5 │         b = datos[i]
 6 │         cantidad = 1
 7 │         while i + cantidad < len(datos) and datos[i + cantidad] == b and cantidad < 255:
 8 │             cantidad += 1
 9 │         salida += bytes([cantidad, b])
10 │         i += cantidad
11 │     return bytes(salida)
```

`compresion/rle.py` → `decodificar_bytes`

```python
1 │ def decodificar_bytes(datos: bytes) -> bytes:
2 │     salida = bytearray()
3 │     for i in range(0, len(datos), 2):
4 │         salida += bytes([datos[i + 1]]) * datos[i]
5 │     return bytes(salida)
```

- `bytearray` es como `bytes` pero se puede modificar (agregar al final).
- **L7** del codificador: `cantidad < 255` porque un byte guarda como máximo 255. Una racha de 600
  se parte en 255 + 255 + 90.
- **L9** cada racha = 2 bytes: `[cantidad, byte]`.
- Decodificador **L3** recorre de 2 en 2: `datos[i]` es la cantidad y `datos[i+1]` el byte.

### 3.6 Casos borde

| Entrada | Salida | Comentario |
|---|---|---|
| `""` | `[]` | El `while` no entra |
| `"A"` | `[(1, 'A')]` | 1 → 2 casillas: crece |
| `"ABC"` | `[(1,'A'),(1,'B'),(1,'C')]` | **La trampa**: 3 → 6 |
| guion (16 721 bytes) | 33 158 bytes | **198 %**: casi el doble |

### 3.7 Para experimentar

En la interfaz (sección RLE) se pueden dibujar píxeles: bloques grandes → comprime; tablero de
ajedrez → crece.

---

## Parte 4 · `estructuras.py` — min-heap y nodo del árbol

### 4.1 La idea

Huffman necesita repetir muchas veces: «dame los **dos** de menor frecuencia» y «guarda este
nuevo». Comparación de opciones:

| Estructura | sacar el mínimo | insertar |
|---|---|---|
| Lista desordenada | O(n) (buscarlo) | O(1) |
| Lista ordenada | O(1) | O(n) (correr elementos) |
| **Montículo binario (heap)** | **O(log n)** | **O(log n)** |

### 4.2 La teoría: un árbol guardado en un arreglo

```
índice:   0   1   2   3   4   5   6
lista:  [ 1,  3,  2,  7,  4,  9,  5 ]

                1 (0)
              /       \
          3 (1)        2 (2)
          /   \        /   \
       7 (3) 4 (4)  9 (5) 5 (6)
```

- Es un **árbol binario completo**: se llena nivel por nivel, de izquierda a derecha. Gracias a
  eso no necesita punteros: la posición lo dice todo.
- Fórmulas para la posición `i`:
  - padre = `(i − 1) // 2` (`//` es división entera)
  - hijo izquierdo = `2i + 1` · hijo derecho = `2i + 2`
- **Propiedad de heap (mínimo):** todo padre ≤ sus hijos ⇒ el mínimo está en la posición 0.
- La altura de un árbol completo con n nodos es ⌊log2 n⌋: con 1 000 000 de elementos, ¡solo 19
  niveles!

### 4.3 Código completo de `MinHeap`

`compresion/estructuras.py` → `MinHeap`

```python
 1 │ class MinHeap:
 2 │     """Cola de prioridad implementada como montículo binario mínimo.
 3 │ 
 4 │     Los elementos deben poder compararse con `<` (en Huffman usamos tuplas
 5 │     (frecuencia, desempate, nodo) para que la comparación sea por frecuencia).
 6 │     """
 7 │ 
 8 │     def __init__(self, observador=None):
 9 │         self._datos = []
10 │         # `observador` (opcional): función que se llama en cada comparación e
11 │         # intercambio. La usa la interfaz visual para animar el heap paso a paso.
12 │         self.observador = observador
13 │ 
14 │     def _avisar(self, accion, i, j):
15 │         if self.observador:
16 │             self.observador(accion, i, j, list(self._datos))
17 │ 
18 │     def __len__(self):
19 │         return len(self._datos)
20 │ 
21 │     def esta_vacio(self):
22 │         return not self._datos
23 │ 
24 │     def ver_minimo(self):
25 │         """O(1): el mínimo siempre está en la raíz."""
26 │         if not self._datos:
27 │             raise IndexError("heap vacío")
28 │         return self._datos[0]
29 │ 
30 │     def insertar(self, elemento):
31 │         """O(log n): se agrega al final y sube mientras sea menor que su padre."""
32 │         self._datos.append(elemento)
33 │         self._subir(len(self._datos) - 1)
34 │ 
35 │     def extraer_minimo(self):
36 │         """O(log n): saca la raíz; el último elemento ocupa su lugar y baja."""
37 │         if not self._datos:
38 │             raise IndexError("heap vacío")
39 │         minimo = self._datos[0]
40 │         ultimo = self._datos.pop()
41 │         if self._datos:
42 │             self._datos[0] = ultimo
43 │             self._bajar(0)
44 │         return minimo
45 │ 
46 │     # --- operaciones internas ------------------------------------------------
47 │     def _subir(self, i):
48 │         """sift-up: intercambia con el padre mientras rompa la propiedad de heap."""
49 │         while i > 0:
50 │             padre = (i - 1) // 2
51 │             self._avisar("comparar", i, padre)
52 │             if self._datos[i] < self._datos[padre]:
53 │                 self._datos[i], self._datos[padre] = self._datos[padre], self._datos[i]
54 │                 self._avisar("intercambiar", i, padre)
55 │                 i = padre
56 │             else:
57 │                 break
58 │ 
59 │     def _bajar(self, i):
60 │         """sift-down: intercambia con el hijo menor mientras sea mayor que él."""
61 │         n = len(self._datos)
62 │         while True:
63 │             izq, der = 2 * i + 1, 2 * i + 2
64 │             menor = i
65 │             if izq < n and self._datos[izq] < self._datos[menor]:
66 │                 menor = izq
67 │             if der < n and self._datos[der] < self._datos[menor]:
68 │                 menor = der
69 │             if menor != i or izq < n:
70 │                 self._avisar("comparar", i, menor if menor != i else izq)
71 │             if menor == i:
72 │                 break
73 │             self._datos[i], self._datos[menor] = self._datos[menor], self._datos[i]
74 │             self._avisar("intercambiar", i, menor)
75 │             i = menor
76 │ 
77 │     def como_lista(self):
78 │         """Copia del arreglo interno (útil para mostrar el estado del heap)."""
79 │         return list(self._datos)
```

> Las líneas **L14–16** (`_avisar`) y las que lo llaman (**L51, L54, L69–70, L74**) solo avisan a
> la interfaz visual para animar el heap. Si no hay observador no hacen nada. **No cambian el
> algoritmo**: pueden ignorarlas al estudiar.

### 4.4 Línea por línea

| Líneas | Método | Explicación |
|---|---|---|
| L8–12 | `__init__` | El heap es solo una lista vacía `_datos` (el `_` indica que es «interna») |
| L18–19 | `__len__` | Permite escribir `len(cola)` |
| L21–22 | `esta_vacio` | `not []` es `True` |
| L24–28 | `ver_minimo` | O(1): el mínimo siempre está en `_datos[0]` |
| L30–33 | `insertar` | Agrega al **final** (sigue siendo completo) y lo hace **subir** |
| L35–44 | `extraer_minimo` | Guarda la raíz (L39), saca el **último** (L40), lo pone en la raíz (L42) y lo hace **bajar** (L43). Si solo había un elemento, `pop` deja la lista vacía y no hay nada que bajar (L41) |
| L47–57 | `_subir` (*sift-up*) | Mientras no sea la raíz (L49): calcula el padre (L50); si es menor que el padre (L52), los intercambia (L53, con `a, b = b, a`) y sigue desde la posición del padre (L55); si no, ya está bien (L57) |
| L59–75 | `_bajar` (*sift-down*) | Calcula los hijos (L63). Busca el menor entre el nodo y sus hijos (L64–68), revisando que los hijos existan (`izq < n`). Si el menor es el mismo nodo, ya está bien (L71–72). Si no, intercambia con el **hijo menor** (L73) y sigue desde ahí (L75) |
| L77–79 | `como_lista` | Copia para mostrar el estado |

**¿Por qué bajar con el hijo MENOR y no con cualquiera?** Si el padre 9 tiene hijos 3 y 2 y se
cambia con el 3, el 3 queda como padre del 2: ¡3 > 2 rompe la propiedad! Con el menor (2), el 2
queda arriba del 3 y del 9: correcto.

### 4.5 Traza: insertar 7, 3, 9, 1, 4, 5, 2 (la de la demo)

| insertar | lista tras `append` | subir | resultado |
|---|---|---|---|
| 7 | [7] | ya es raíz | [7] |
| 3 | [7, 3] | 3 < padre 7 → intercambiar | [3, 7] |
| 9 | [3, 7, 9] | 9 > padre 3 → parar | [3, 7, 9] |
| 1 | [3, 7, 9, 1] | pos 3: 1 < 7 (pos 1) → intercambiar; pos 1: 1 < 3 (pos 0) → intercambiar | [1, 3, 9, 7] |
| 4 | [1, 3, 9, 7, 4] | pos 4: padre pos 1 (3) → 4 > 3 parar | [1, 3, 9, 7, 4] |
| 5 | [1, 3, 9, 7, 4, 5] | pos 5: padre pos 2 (9) → intercambiar; pos 2: padre 1 → parar | [1, 3, 5, 7, 4, 9] |
| 2 | [1, 3, 5, 7, 4, 9, 2] | pos 6: padre pos 2 (5) → intercambiar; pos 2: padre 1 → parar | [1, 3, 2, 7, 4, 9, 5] |

### 4.6 Traza: extraer el mínimo de `[1, 3, 2, 7, 4, 9, 5]`

| paso | lista | i | hijos (posiciones) | menor | acción |
|---|---|---|---|---|---|
| guardar 1; el último (5) va a la raíz | [5, 3, 2, 7, 4, 9] | 0 | 3 (1), 2 (2) | 2 en pos 2 | intercambiar |
| | [2, 3, 5, 7, 4, 9] | 2 | 9 (5), pos 6 no existe | el mismo 5 | parar |

Devuelve **1**. Si se siguen extrayendo salen **1, 2, 3, 4, 5, 7, 9**: ordenados (eso es
*heapsort*).

### 4.7 Complejidad

- `insertar`, `extraer_minimo`: **O(log n)**: suben o bajan como máximo la altura del árbol.
- `ver_minimo`, `__len__`: **O(1)**.
- Memoria: O(n), solo la lista.

### 4.8 `NodoHuffman`

`compresion/estructuras.py` → `NodoHuffman`

```python
 1 │ class NodoHuffman:
 2 │     """Nodo del ÁRBOL BINARIO de Huffman.
 3 │ 
 4 │     * Hoja:          tiene `simbolo` y su `frecuencia`; no tiene hijos.
 5 │     * Nodo interno:  `simbolo` es None; su frecuencia es la suma de sus hijos.
 6 │     Convención: rama izquierda = bit 0, rama derecha = bit 1.
 7 │     """
 8 │ 
 9 │     __slots__ = ("simbolo", "frecuencia", "izq", "der")
10 │ 
11 │     def __init__(self, frecuencia, simbolo=None, izq=None, der=None):
12 │         self.frecuencia = frecuencia
13 │         self.simbolo = simbolo
14 │         self.izq = izq
15 │         self.der = der
16 │ 
17 │     def es_hoja(self):
18 │         return self.izq is None and self.der is None
19 │ 
20 │     def __repr__(self):
21 │         if self.es_hoja():
22 │             return "Hoja(%r:%d)" % (self.simbolo, self.frecuencia)
23 │         return "Nodo(%d)" % self.frecuencia
```

- **L9** `__slots__` le dice a Python «estos objetos solo tienen estos 4 atributos». Ahorra
  memoria (no crea un diccionario por objeto) y evita errores de tipeo (`nodo.izquierda = …` daría
  error).
- **L11–15** una **hoja** se crea con `NodoHuffman(5, "A")`; un **nodo interno** con
  `NodoHuffman(11, izq=a, der=b)` (`simbolo` queda `None`).
- **L17–18** es hoja si no tiene hijos.
- **L20–23** `__repr__` define cómo se imprime: `Hoja('A':5)` o `Nodo(11)`. Solo para depurar.

---

## Parte 5 · `huffman.py` — codificación Huffman

### 5.1 La idea

Códigos **cortos** para lo frecuente, **largos** para lo raro, y libres de prefijo. David Huffman
(1952) demostró que su método da el código de este tipo **óptimo** (el de menos bits totales).

### 5.2 La teoría: por qué fusionar los dos menores

Los dos símbolos menos frecuentes deben tener los códigos **más largos** (están más abajo en el
árbol). Huffman los pone como hermanos al fondo y los trata como un solo «símbolo» con la suma de
sus frecuencias. Repite hasta que queda uno: la raíz. Cada fusión agrega 1 bit a todos los símbolos
de ese subárbol; por eso conviene que las fusiones «caras» (las primeras, que quedan más hondo) se
hagan con lo menos frecuente.

### 5.3 Código: construir el árbol

`compresion/huffman.py` → `construir_arbol`

```python
 1 │ def construir_arbol(frecuencias, traza=None, fusiones=None):
 2 │     """Construye el árbol de Huffman a partir de {simbolo: frecuencia}.
 3 │ 
 4 │     `traza` (opcional): lista donde se anotan los pasos, para explicar el
 5 │     algoritmo en la demo.
 6 │     `fusiones` (opcional): lista donde se anotan los objetos (a, b, padre) de
 7 │     cada fusión; la interfaz visual la usa para dibujar el bosque paso a paso.
 8 │ 
 9 │     Desempate: en la cola guardamos tuplas (frecuencia, -orden, nodo). Si dos
10 │     nodos tienen la misma frecuencia, sale primero el creado MÁS RECIENTEMENTE.
11 │     Cualquier desempate da un código óptimo (mismo total de bits); este en
12 │     particular produce las mismas longitudes de la diapositiva.
13 │     """
14 │     if not frecuencias:
15 │         raise ValueError("no hay símbolos para codificar")
16 │ 
17 │     cola = MinHeap()
18 │     orden = 0
19 │     for simbolo, freq in frecuencias.items():
20 │         cola.insertar((freq, -orden, NodoHuffman(freq, simbolo)))
21 │         orden += 1
22 │ 
23 │     # Caso especial: un solo símbolo distinto (p. ej. "AAAA").
24 │     # Le damos un padre artificial para que su código sea "0".
25 │     if len(cola) == 1:
26 │         _, _, unica = cola.extraer_minimo()
27 │         return NodoHuffman(unica.frecuencia, izq=unica)
28 │ 
29 │     while len(cola) > 1:
30 │         f1, _, a = cola.extraer_minimo()     # el menor     -> rama izquierda (0)
31 │         f2, _, b = cola.extraer_minimo()     # el siguiente -> rama derecha  (1)
32 │         padre = NodoHuffman(f1 + f2, izq=a, der=b)
33 │         if fusiones is not None:
34 │             fusiones.append((a, b, padre))
35 │         if traza is not None:
36 │             traza.append("fusionar %s + %s -> nodo de %d"
37 │                          % (_describir(a), _describir(b), f1 + f2))
38 │         cola.insertar((padre.frecuencia, -orden, padre))
39 │         orden += 1
40 │ 
41 │     return cola.extraer_minimo()[2]
```

| Líneas | Qué hace |
|---|---|
| L14–15 | Sin símbolos no hay árbol: error claro |
| L17–21 | Crea la **cola de prioridad** y mete una **hoja** por símbolo, como tupla `(frecuencia, -orden, nodo)` |
| L25–27 | **Caso especial:** un solo símbolo distinto (`"AAAA"`). No hay nada que fusionar y el código saldría vacío `""`. Se crea un padre artificial: el código de la hoja será `"0"` |
| L29 | Mientras quede más de un árbol |
| L30–31 | Saca los **dos menores**. El primero será hijo izquierdo (bit 0), el segundo derecho (bit 1). El `_` descarta el desempate |
| L32 | Crea el padre con la **suma** de frecuencias |
| L33–37 | Solo para la demo/interfaz: anota la fusión |
| L38–39 | Mete el padre en la cola con un `orden` nuevo |
| L41 | Lo único que queda es la raíz; `[2]` toma el nodo de la tupla |

**¿Por qué tuplas `(frecuencia, -orden, nodo)`?**

1. El `MinHeap` compara con `<`. Python compara tuplas **posición por posición**: primero la
   frecuencia; si empatan, la segunda posición; y así.
2. Así se ordena por frecuencia, que es lo que pide Huffman.
3. Si dos nodos tienen la misma frecuencia, desempata `-orden`: sale primero el de **orden más
   alto** (el creado más recientemente). Así el resultado es siempre el mismo (determinista).
4. Como `orden` nunca se repite, Python **nunca** llega a comparar dos `NodoHuffman` (no saben
   compararse y darían `TypeError`).

### 5.4 Traza completa con ABRACADABRA

`Counter` mantiene el orden de aparición (A, B, R, C, D), así que reciben `orden` 0, 1, 2, 3, 4.

**Estado inicial de la cola** (clave = `(freq, -orden)`):
A (5, 0) · B (2, −1) · R (2, −2) · C (1, −3) · D (1, −4)

| fusión | 1.º en salir (izq = 0) | 2.º en salir (der = 1) | padre (clave) | queda en la cola |
|---|---|---|---|---|
| 1 | D (1, −4) | C (1, −3) | [DC] 2 (2, −5) | A, B, R, [DC] |
| 2 | [DC] (2, −5) | R (2, −2) | [DCR] 4 (4, −6) | A, B, [DCR] |
| 3 | B (2, −1) | [DCR] (4, −6) | [BDCR] 6 (6, −7) | A, [BDCR] |
| 4 | A (5, 0) | [BDCR] (6, −7) | raíz 11 | raíz |

- Fusión 1: D sale antes que C porque `(1, −4) < (1, −3)` (−4 < −3).
- Fusión 2: hay tres con frecuencia 2: B (−1), R (−2) y [DC] (−5). El menor desempate es −5
  ([DC], el más nuevo), luego −2 (R).

Árbol final (igual al de la diapositiva 8):

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

**Complejidad:** k hojas → k − 1 fusiones; cada fusión hace 2 extracciones y 1 inserción, cada una
O(log k) ⇒ **O(k log k)**. (Más O(n) de contar las frecuencias antes.)

### 5.5 Código: generar los códigos

`compresion/huffman.py` → `generar_codigos`

```python
 1 │ def generar_codigos(raiz):
 2 │     """Recorre el árbol (DFS) y arma la tabla {simbolo: "bits"}."""
 3 │     codigos = {}
 4 │ 
 5 │     def recorrer(nodo, camino):
 6 │         if nodo is None:
 7 │             return
 8 │         if nodo.es_hoja():
 9 │             codigos[nodo.simbolo] = camino or "0"
10 │             return
11 │         recorrer(nodo.izq, camino + "0")   # izquierda = 0
12 │         recorrer(nodo.der, camino + "1")   # derecha   = 1
13 │ 
14 │     recorrer(raiz, "")
15 │     return codigos
```

- **L5–12** función **interna** y **recursiva** (recorrido en profundidad, DFS, en preorden).
  `camino` acumula los bits desde la raíz.
- **L6–7** caso base de seguridad: hijo inexistente.
- **L8–10** caso base: llegó a una hoja → su código es el camino. `camino or "0"`: si la raíz misma
  fuera una hoja, el camino sería `""`; se usa `"0"`.
- **L11–12** baja a la izquierda agregando `"0"` y a la derecha agregando `"1"`.

**Traza:** raíz → izq: A con `"0"` · der `"1"` → izq: B `"10"` · der `"11"` → izq `"110"` → D
`"1100"`, C `"1101"` · der: R `"111"`.
Resultado: **A=0, B=10, R=111, D=1100, C=1101**. Costo: O(k) (visita cada nodo una vez).

### 5.6 Código: códigos canónicos

`compresion/huffman.py` → `codigos_canonicos`

```python
 1 │ def codigos_canonicos(longitudes):
 2 │     """{simbolo: longitud} -> {simbolo: código canónico}.
 3 │ 
 4 │     Regla: ordenar por (longitud, símbolo) y asignar números binarios
 5 │     consecutivos; al pasar a una longitud mayor se desplaza a la izquierda.
 6 │     """
 7 │     ordenados = sorted(longitudes.items(), key=lambda par: (par[1], par[0]))
 8 │     codigos = {}
 9 │     codigo = 0
10 │     longitud_previa = ordenados[0][1]
11 │     for simbolo, longitud in ordenados:
12 │         codigo <<= (longitud - longitud_previa)
13 │         codigos[simbolo] = format(codigo, "0%db" % longitud)
14 │         codigo += 1
15 │         longitud_previa = longitud
16 │     return codigos
```

**¿Para qué?** El archivo comprimido necesita decirle al decodificador qué código tiene cada
símbolo. Guardar el árbol es complicado; con la regla canónica basta guardar **la longitud** de cada
código, y el decodificador reconstruye los mismos códigos. Lo usan **ZIP, PNG, gzip y JPEG**.

| Línea | Qué hace |
|---|---|
| L7 | Ordena por **(longitud, símbolo)**: los cortos primero; si empatan, alfabético. `lambda par: (par[1], par[0])` arma esa clave |
| L9 | El primer código es 0 |
| L12 | `<<=` corre bits a la izquierda: cada bit de longitud extra multiplica por 2 |
| L13 | `format(6, "03b")` → `"110"`: el número en binario con ceros a la izquierda |
| L14 | El siguiente código de la misma longitud es el número siguiente |

**Traza** (longitudes A:1, B:2, R:3, C:4, D:4):

| símbolo | longitud | `codigo` al llegar | desplazar | queda | binario | `codigo` sale |
|---|---|---|---|---|---|---|
| A | 1 | 0 | 1−1 = 0 | 0 | `0` | 1 |
| B | 2 | 1 | 2−1 = 1 (×2) | 2 | `10` | 3 |
| R | 3 | 3 | 1 (×2) | 6 | `110` | 7 |
| C | 4 | 7 | 1 (×2) | 14 | `1110` | 15 |
| D | 4 | 15 | 0 | 15 | `1111` | 16 |

Son **exactamente los de la diapositiva**. ¿Por qué son distintos a los del árbol (R=111, C=1101,
D=1100)? Porque cuando hay empates existen **varios árboles óptimos**; lo que importa son las
**longitudes**, que coinciden (A:1, B:2, R:3, C:4, D:4): los dos dan 23 bits.

### 5.7 Código: codificar

`compresion/huffman.py` → `codificar`

```python
1 │ def codificar(datos, codigos=None):
2 │     """Devuelve (bits_como_string, tabla_de_codigos)."""
3 │     if codigos is None:
4 │         codigos = generar_codigos(construir_arbol(Counter(datos)))
5 │     bits = "".join(codigos[s] for s in datos)
6 │     return bits, codigos
```

- **L3–4** si no se pasan códigos, los calcula: contar → árbol → códigos.
- **L5** reemplaza cada símbolo por su código y los pega.

ABRACADABRA con los canónicos:

```
A  B   R    A  C     A  D     A  B   R    A
0  10  110  0  1110  0  1111  0  10  110  0   → 01011001110011110101100 (23 bits)
```

Cuenta: 5·1 (A) + 2·2 (B) + 2·3 (R) + 1·4 (C) + 1·4 (D) = 5 + 4 + 6 + 4 + 4 = **23**.
Comparación: ASCII 88 · Huffman 23 · Shannon 22.4. Huffman = 2.091 bits/símbolo vs. H = 2.040.

### 5.8 Código: decodificar con tabla

`compresion/huffman.py` → `decodificar`

```python
 1 │ def decodificar(bits, codigos):
 2 │     """Decodifica usando la tabla (como los códigos son libres de prefijo,
 3 │     basta ir acumulando bits hasta que coincidan con algún código)."""
 4 │     inverso = {codigo: simbolo for simbolo, codigo in codigos.items()}
 5 │     resultado = []
 6 │     actual = ""
 7 │     for b in bits:
 8 │         actual += b
 9 │         if actual in inverso:            # búsqueda O(1) en tabla hash
10 │             resultado.append(inverso[actual])
11 │             actual = ""
12 │     if actual:
13 │         raise ValueError("bits sobrantes: el mensaje está incompleto")
14 │     return resultado
```

- **L4** invierte la tabla: `{"0": "A", "10": "B", …}` (tabla hash código → símbolo).
- **L7–11** agrega bits a `actual` hasta que coincida con un código; entonces emite y reinicia.
- **L12–13** si al final sobran bits, el mensaje estaba incompleto.
- Funciona **porque es libre de prefijo**: cuando `actual` coincide, no puede ser el comienzo de
  otro código más largo.

**Traza** de los primeros bits `0 1 0 1 1 0 …`: `"0"` → A ✔ · `"1"` no · `"10"` → B ✔ · `"1"` no ·
`"11"` no · `"110"` → R ✔ · …

### 5.9 Código: decodificar con el árbol

`compresion/huffman.py` → `decodificar_con_arbol`

```python
 1 │ def decodificar_con_arbol(bits, raiz):
 2 │     """Decodifica recorriendo el árbol: 0 = bajar a la izquierda, 1 = a la
 3 │     derecha; al llegar a una hoja se emite su símbolo y se vuelve a la raíz."""
 4 │     resultado = []
 5 │     nodo = raiz
 6 │     for b in bits:
 7 │         nodo = nodo.izq if b == "0" else nodo.der
 8 │         if nodo.es_hoja():
 9 │             resultado.append(nodo.simbolo)
10 │             nodo = raiz
11 │     return resultado
```

- **L7** con cada bit baja: 0 izquierda, 1 derecha.
- **L8–10** al llegar a una hoja emite su símbolo y vuelve a la raíz.
- Con los códigos del árbol: `1100` → raíz → 1 → 1 → 0 → 0 → hoja D.

### 5.10 Código: verificar «libre de prefijo»

`compresion/huffman.py` → `es_libre_de_prefijo`

```python
1 │ def es_libre_de_prefijo(codigos):
2 │     """Verifica que ningún código sea prefijo de otro."""
3 │     lista = sorted(codigos.values())
4 │     # Tras ordenar, si a es prefijo de algún código, lo es del siguiente.
5 │     return all(not lista[i + 1].startswith(lista[i]) for i in range(len(lista) - 1))
```

**Truco:** si se ordenan alfabéticamente, un código que es prefijo de otro queda **justo antes**
de algún código que empieza por él (todo lo que empieza por `"11"` queda junto, después de `"11"`).
Por eso basta comparar **vecinos**: O(k log k) por el ordenamiento, en lugar de comparar todos
contra todos (O(k²)).

### 5.11 Casos borde

| Entrada | Qué pasa |
|---|---|
| `""` | `construir_arbol` lanza `ValueError` (L14–15) |
| `"AAAA"` | Un solo símbolo: código `"0"` → `"0000"` (4 bits) |
| Todas las letras con la misma frecuencia | El árbol queda equilibrado: códigos de igual largo |

---

## Parte 6 · `lz77.py` — ventana deslizante y tabla hash

### 6.1 La idea

Si lo que viene ya apareció, se guarda **(retrocede `d`, copia `l`)**. Abraham Lempel y Jacob Ziv,
1977. Es la base de ZIP, gzip y PNG (junto con Huffman).

### 6.2 La teoría

- **Ventana deslizante:** lo ya leído, hasta cierta distancia hacia atrás (en DEFLATE, 32 KB).
- **Tokens:** `('L', símbolo)` (literal) o `('R', distancia, longitud)` (referencia).
- **Coincidencia mínima de 3:** una referencia ocupa más que 1 o 2 literales; no vale la pena.
- **El problema de velocidad:** buscar la coincidencia más larga comparando contra toda la ventana
  es lento. Solución: **tabla hash** de tríos.

Constantes del módulo:

```python
VENTANA = 32 * 1024        # cuánto se mira hacia atrás (como DEFLATE)
MIN_COINCIDENCIA = 3       # copias de menos de 3 no valen la pena
MAX_COINCIDENCIA = 258     # longitud máxima de una copia (como DEFLATE)
MAX_CANDIDATOS = 64        # cuántas posiciones previas revisar como máximo
```

### 6.3 Código: el codificador

`compresion/lz77.py` → `codificar`

```python
 1 │ def codificar(datos, ventana=VENTANA, min_coinc=MIN_COINCIDENCIA,
 2 │               max_coinc=MAX_COINCIDENCIA, estadisticas=None, traza=None):
 3 │     """Codifica `datos` (str, bytes o lista) en tokens LZ77 usando tabla hash.
 4 │ 
 5 │     Si se pasa un diccionario `estadisticas`, se anota cuántas comparaciones
 6 │     de símbolos se hicieron (para comparar con la búsqueda por fuerza bruta).
 7 │     Si se pasa una lista `traza`, se anota en cada paso qué clave se buscó en
 8 │     la tabla hash y qué posiciones candidatas devolvió (para la interfaz visual).
 9 │     """
10 │     tokens = []
11 │     tabla = {}                  # TABLA HASH: trío -> [posiciones donde aparece]
12 │     comparaciones = 0
13 │     n = len(datos)
14 │     i = 0
15 │ 
16 │     def registrar(pos):
17 │         """Guarda la posición `pos` bajo la clave de sus 3 primeros símbolos."""
18 │         if pos + min_coinc <= n:
19 │             tabla.setdefault(datos[pos:pos + min_coinc], []).append(pos)
20 │ 
21 │     while i < n:
22 │         mejor_long, mejor_dist = 0, 0
23 │         clave = datos[i:i + min_coinc]
24 │         revisados = []
25 │         if len(clave) == min_coinc and clave in tabla:        # O(1) promedio
26 │             candidatos = tabla[clave]
27 │             revisados = [p for p in candidatos[-MAX_CANDIDATOS:] if i - p <= ventana]
28 │             # Revisamos desde la más reciente (distancias cortas primero).
29 │             for pos in reversed(candidatos[-MAX_CANDIDATOS:]):
30 │                 distancia = i - pos
31 │                 if distancia > ventana:
32 │                     break                     # ya se salió de la ventana
33 │                 longitud = 0
34 │                 # La copia puede "solaparse" con lo que se está escribiendo
35 │                 # (p. ej. 'AAAAAA' = 'A' + (retrocede 1, copia 5)).
36 │                 while (longitud < max_coinc and i + longitud < n
37 │                        and datos[pos + longitud] == datos[i + longitud]):
38 │                     longitud += 1
39 │                     comparaciones += 1
40 │                 comparaciones += 1
41 │                 if longitud > mejor_long:
42 │                     mejor_long, mejor_dist = longitud, distancia
43 │                     if longitud == max_coinc:
44 │                         break
45 │ 
46 │         if traza is not None:
47 │             traza.append({"i": i, "clave": clave, "candidatos": revisados,
48 │                           "dist": mejor_dist, "long": mejor_long})
49 │         if mejor_long >= min_coinc:
50 │             tokens.append(("R", mejor_dist, mejor_long))
51 │             for p in range(i, i + mejor_long):
52 │                 registrar(p)
53 │             i += mejor_long
54 │         else:
55 │             tokens.append(("L", datos[i]))
56 │             registrar(i)
57 │             i += 1
58 │ 
59 │     if estadisticas is not None:
60 │         estadisticas["comparaciones"] = comparaciones
61 │     return tokens
```

> **L24, L27, L46–48** solo guardan información para la interfaz (`revisados`, `traza`). **L12,
> L39–40, L59–60** cuentan comparaciones para la demo. No cambian el resultado.

| Líneas | Qué hace |
|---|---|
| L11 | **La tabla hash**: clave = 3 símbolos seguidos; valor = lista de posiciones donde aparecieron |
| L16–19 | `registrar(pos)` anota que en `pos` empieza ese trío. `setdefault(clave, [])` devuelve la lista existente o crea una vacía. **L18** evita tríos incompletos al final |
| L21 | Recorre los datos; `i` es la posición actual |
| L22 | Mejor coincidencia encontrada hasta ahora |
| L23 | Los próximos 3 símbolos (la clave a buscar) |
| L25 | `clave in tabla` → **O(1)**: «¿ya vi estos 3 símbolos?». Si no, ni se busca |
| L29 | Revisa los candidatos **del más reciente al más viejo** (`reversed`) y solo los últimos 64 (`[-64:]`) |
| L30–32 | Distancia; si ya se salió de la ventana, los siguientes también (son más viejos): `break` |
| L36–38 | Mide cuántos símbolos coinciden a partir de ese candidato |
| L41–44 | Se queda con la coincidencia más larga; si llega al máximo (258), deja de buscar |
| L49–53 | Si mide al menos 3: emite **referencia**, registra todas las posiciones copiadas y salta |
| L54–57 | Si no: emite **literal**, lo registra y avanza 1 |

### 6.4 Traza ABRACADABRA

| i | clave (L23) | ¿en la tabla? (L25) | mejor | token | registra (L52/L56) |
|---|---|---|---|---|---|
| 0 | ABR | no | — | `A` | ABR → [0] |
| 1 | BRA | no | — | `B` | BRA → [1] |
| 2 | RAC | no | — | `R` | RAC → [2] |
| 3 | ACA | no | — | `A` | ACA → [3] |
| 4 | CAD | no | — | `C` | CAD → [4] |
| 5 | ADA | no | — | `A` | ADA → [5] |
| 6 | DAB | no | — | `D` | DAB → [6] |
| 7 | ABR | **sí: [0]** | pos 0, distancia 7: A=A, B=B, R=R, A=A, fin de los datos → 4 | **`(←7, 4)`** | ABR, BRA, … |

Resultado: `A B R A C A D (←7,4)` = **«retrocede 7, copia 4»** de la diapositiva 9.

### 6.5 Traza: copia solapada `"A" × 20`

| i | clave | tabla | coincidencia | token |
|---|---|---|---|---|
| 0 | AAA | no | — | `A` (registra AAA → [0]) |
| 1 | AAA | **[0]** | distancia 1. Compara `datos[0+k]` con `datos[1+k]` para k = 0…18: todas A → 19 | `(←1, 19)` |

La fuente (posiciones 0–18) y el destino (1–19) **se solapan**. No es un error: el decodificador
copia de a un símbolo, y cada A copiada ya está disponible para la siguiente. Así LZ77 también
hace el trabajo de RLE.

### 6.6 Código: decodificar

`compresion/lz77.py` → `decodificar`

```python
 1 │ def decodificar(tokens, como_bytes=False):
 2 │     """Reconstruye los datos. El decodificador no necesita tabla hash: solo
 3 │     copia desde lo que ya reconstruyó (por eso descomprimir ZIP es tan rápido)."""
 4 │     salida = []
 5 │     for token in tokens:
 6 │         if token[0] == "L":
 7 │             salida.append(token[1])
 8 │         else:
 9 │             _, distancia, longitud = token
10 │             inicio = len(salida) - distancia
11 │             for k in range(longitud):          # símbolo a símbolo (permite solape)
12 │                 salida.append(salida[inicio + k])
13 │     if como_bytes:
14 │         return bytes(salida)
15 │     if salida and isinstance(salida[0], str):
16 │         return "".join(salida)
17 │     return salida
```

- **L6–7** literal: se agrega tal cual.
- **L9–12** referencia: `inicio = len(salida) − distancia` y copia `longitud` símbolos **uno por
  uno**. Si se copiara un bloque de una vez (`salida[inicio:inicio+longitud]`), la copia solapada
  fallaría porque esos símbolos aún no existen.
- **L13–17** arma el resultado en el tipo correcto (bytes, texto o lista).
- **No usa tabla hash:** solo copia. Por eso descomprimir es mucho más rápido que comprimir.

### 6.7 ¿Cuánto ayuda la tabla hash?

`codificar_fuerza_bruta` (en el mismo archivo) busca comparando contra **cada** posición de la
ventana. Comparaciones de símbolos:

| texto | sin tabla | con tabla |
|---|---|---|
| ABRACADABRA | 37 | 5 |
| «la compresion de la compresion» | 171 | 14 |
| texto repetitivo de 656 letras (demo de consola) | 8 961 | 935 |

### 6.8 Complejidad

- Sin tabla: O(n · ventana · longitud de coincidencia).
- Con tabla: cada posición hace 1 consulta O(1) y revisa como máximo 64 candidatos de hasta 258
  símbolos ⇒ en la práctica cercano a **O(n)**.
- Decodificar: O(n).
- Memoria de la tabla: O(n) posiciones.

### 6.9 Para experimentar

- Cambiar la ventana a 3 en la interfaz con «ABRACADABRA»: la «A B R A» ya no se encuentra porque
  está a distancia 7 > 3.

---

## Parte 7 · `lzw.py` — diccionario dinámico

### 7.1 La idea

LZ78/LZW (Lempel, Ziv, Welch, 1984): en vez de apuntar hacia atrás, se construye un
**diccionario** de secuencias y se emite el **número** de cada una. «ONU» en lugar de
«Organización de las Naciones Unidas». Se usa en GIF y TIFF.

### 7.2 Código: codificar

`compresion/lzw.py` → `codificar`

```python
 1 │ def codificar(texto, alfabeto=None):
 2 │     """Devuelve (lista_de_codigos, diccionario_final, pasos)."""
 3 │     if alfabeto is None:
 4 │         alfabeto = [chr(i) for i in range(256)]
 5 │     diccionario = {s: i for i, s in enumerate(alfabeto)}       # TABLA HASH
 6 │     siguiente = len(diccionario)
 7 │ 
 8 │     w = ""
 9 │     codigos = []
10 │     pasos = []
11 │     for c in texto:
12 │         wc = w + c
13 │         if wc in diccionario:                 # búsqueda O(1)
14 │             w = wc
15 │         else:
16 │             codigos.append(diccionario[w])
17 │             diccionario[wc] = siguiente
18 │             pasos.append((w, diccionario[w], wc, siguiente))
19 │             siguiente += 1
20 │             w = c
21 │     if w:
22 │         codigos.append(diccionario[w])
23 │         pasos.append((w, diccionario[w], None, None))
24 │     return codigos, diccionario, pasos
```

| Líneas | Qué hace |
|---|---|
| L3–4 | Por defecto el alfabeto son los 256 caracteres |
| L5 | El diccionario empieza con cada símbolo suelto: `{'B': 0, 'E': 1, …}`. **Tabla hash** |
| L6 | El próximo número libre |
| L8 | `w` = la secuencia más larga reconocida hasta ahora |
| L12–14 | Si `w + c` ya existe, se alarga `w` |
| L16 | Si no: se emite el código de `w` |
| L17 | Se agrega `w + c` como entrada nueva |
| L18 | (para la demo) anota el paso |
| L20 | Se empieza de nuevo desde `c` |
| L21–23 | Al terminar, queda `w` por emitir |

### 7.3 Traza completa `TOBEORNOTTOBEORTOBEORNOT`

Diccionario inicial: B=0, E=1, N=2, O=3, R=4, T=5.

| # | w reconocida | emite | nueva entrada |
|---|---|---|---|
| 1 | T | 5 | TO = 6 |
| 2 | O | 3 | OB = 7 |
| 3 | B | 0 | BE = 8 |
| 4 | E | 1 | EO = 9 |
| 5 | O | 3 | OR = 10 |
| 6 | R | 4 | RN = 11 |
| 7 | N | 2 | NO = 12 |
| 8 | O | 3 | OT = 13 |
| 9 | T | 5 | TT = 14 |
| 10 | **TO** | 6 | TOB = 15 |
| 11 | **BE** | 8 | BEO = 16 |
| 12 | **OR** | 10 | ORT = 17 |
| 13 | **TOB** | 15 | TOBE = 18 |
| 14 | **EO** | 9 | EOR = 19 |
| 15 | **RN** | 11 | RNO = 20 |
| 16 | **OT** | 13 | (fin) |

24 letras → **16 códigos**. Desde el paso 10, cada código reemplaza 2 o 3 letras.

### 7.4 Código: decodificar

`compresion/lzw.py` → `decodificar`

```python
 1 │ def decodificar(codigos, alfabeto=None):
 2 │     if alfabeto is None:
 3 │         alfabeto = [chr(i) for i in range(256)]
 4 │     diccionario = {i: s for i, s in enumerate(alfabeto)}
 5 │     siguiente = len(diccionario)
 6 │     if not codigos:
 7 │         return ""
 8 │     w = diccionario[codigos[0]]
 9 │     salida = [w]
10 │     for codigo in codigos[1:]:
11 │         if codigo in diccionario:
12 │             entrada = diccionario[codigo]
13 │         elif codigo == siguiente:
14 │             # Caso especial "cScSc": el código se refiere a la entrada que
15 │             # estamos a punto de crear. Necesariamente vale w + w[0].
16 │             entrada = w + w[0]
17 │         else:
18 │             raise ValueError("código LZW inválido: %d" % codigo)
19 │         salida.append(entrada)
20 │         diccionario[siguiente] = w + entrada[0]
21 │         siguiente += 1
22 │         w = entrada
23 │     return "".join(salida)
```

- **L4** el mismo diccionario inicial, pero al revés: número → secuencia.
- **L8–9** el primer código siempre es un símbolo suelto.
- **L11–12** caso normal: el código ya existe.
- **L13–16** **caso especial**: el decodificador va un paso atrasado (crea cada entrada un paso
  después que el codificador). A veces recibe justo el código que está a punto de crear. Esa
  entrada solo puede ser `w + w[0]` (la secuencia anterior + su propia primera letra).
- **L20** crea la entrada que el codificador creó en el paso anterior: `w + primera letra de lo
  nuevo`.

**Ejemplo del caso especial** `ABABABA` con alfabeto `A=0, B=1`: códigos `[0, 1, 2, 4]`. Al leer
el 4, el diccionario solo llega hasta 3 → `entrada = w + w[0] = "AB" + "A" = "ABA"` ✔.

### 7.5 Código: tamaño en bits

`compresion/lzw.py` → `bits_necesarios`

```python
1 │ def bits_necesarios(codigos, tamano_alfabeto):
2 │     """Tamaño en bits usando códigos de ancho creciente (como GIF): cuando el
3 │     diccionario tiene d entradas, cada código ocupa ceil(log2 d) bits."""
4 │     total = 0
5 │     d = tamano_alfabeto
6 │     for _ in codigos:
7 │         total += max(1, math.ceil(math.log2(d + 1)))
8 │         d += 1
9 │     return total
```

Como GIF, cada código usa los bits justos para el tamaño **actual** del diccionario
(`ceil(log2(d + 1))`), que crece con cada código. En el ejemplo: 72 bits sin comprimir (3 por
letra) → 68 con LZW. Con textos cortos la ganancia es poca; con textos largos es mucha.

### 7.6 Complejidad

O(n) consultas a la tabla hash; cada concatenación `w + c` cuesta O(|w|). Memoria O(número de
entradas).

---

## Parte 8 · `bwt.py` — Burrows-Wheeler

### 8.1 La idea

La BWT (Burrows y Wheeler, 1994) **no comprime**: reordena el texto para que las letras iguales
queden juntas, y así RLE + Huffman comprimen mejor. Es reversible. Base de **bzip2**.

### 8.2 Código: transformar

`compresion/bwt.py` → `rotaciones_ordenadas`

```python
1 │ def rotaciones_ordenadas(texto):
2 │     t = texto + FIN
3 │     return sorted(t[i:] + t[:i] for i in range(len(t)))
```

`compresion/bwt.py` → `transformar`

```python
1 │ def transformar(texto):
2 │     """BWT: última columna de la tabla de rotaciones ordenadas."""
3 │     if FIN in texto:
4 │         raise ValueError("el texto no puede contener el marcador de fin '$'")
5 │     return "".join(rot[-1] for rot in rotaciones_ordenadas(texto))
```

- `FIN = "$"` marca el final del texto (para poder deshacer la transformación).
- `t[i:] + t[:i]` es la rotación que empieza en `i`: con `t = "BANANA$"`, `i = 2` → `"NANA$" +
  "BA"` = `"NANA$BA"`.
- `sorted` ordena las rotaciones; `rot[-1]` toma la última letra de cada una.
- **L3–4** de `transformar`: si el texto ya tuviera `$`, la inversa se confundiría.

**Traza BANANA:**

| fila | rotación ordenada | última letra |
|---|---|---|
| 0 | `$BANANA` | A |
| 1 | `A$BANAN` | N |
| 2 | `ANA$BAN` | N |
| 3 | `ANANA$B` | B |
| 4 | `BANANA$` | $ |
| 5 | `NA$BANA` | A |
| 6 | `NANA$BA` | A |

BWT = **`ANNB$AA`**. Las rotaciones que empiezan con «A» (contexto «A…») quedan juntas, y la letra
anterior a ese contexto suele repetirse (aquí N, N).

**Complejidad didáctica:** n rotaciones de largo n, ordenar cuesta O(n log n) comparaciones de
O(n) cada una ⇒ O(n² log n). bzip2 usa *arreglos de sufijos*: O(n).

### 8.3 Código: la inversa

`compresion/bwt.py` → `inversa`

```python
 1 │ def inversa(ultima):
 2 │     """Inversa con la propiedad "LF" (last-to-first), en O(n log n).
 3 │ 
 4 │     La primera columna es la última ordenada. La k-ésima aparición de una
 5 │     letra en la última columna corresponde a la k-ésima aparición de esa misma
 6 │     letra en la primera columna. Siguiendo ese enlace desde la fila que
 7 │     empieza con '$' se reconstruye el texto de atrás hacia adelante.
 8 │     """
 9 │     n = len(ultima)
10 │     # Para cada posición de la última columna: (letra, cuántas veces apareció antes)
11 │     vistos = {}
12 │     rango = []
13 │     for c in ultima:
14 │         rango.append(vistos.get(c, 0))
15 │         vistos[c] = vistos.get(c, 0) + 1
16 │     # Dónde empieza cada letra en la primera columna (ordenada).
17 │     inicio = {}
18 │     acumulado = 0
19 │     for c in sorted(vistos):
20 │         inicio[c] = acumulado
21 │         acumulado += vistos[c]
22 │ 
23 │     # Empezamos en la fila cuya rotación comienza con '$' (el texto original
24 │     # rotado). Ojo: no siempre es la fila 0, porque caracteres como el espacio
25 │     # (código 32) van ANTES que '$' (código 36) al ordenar.
26 │     fila = inicio[FIN]
27 │     resultado = []
28 │     for _ in range(n):
29 │         c = ultima[fila]
30 │         resultado.append(c)
31 │         fila = inicio[c] + rango[fila]          # salto LF
32 │     # Se leyó de atrás hacia adelante y lo último leído fue '$':
33 │     # al invertir queda "$texto"; quitamos el marcador.
34 │     return "".join(reversed(resultado))[1:]
```

**La propiedad LF (last-to-first):**
- La **primera columna** de la tabla ordenada es la última columna **ordenada**.
- La k-ésima «A» de la última columna es **la misma A del texto** que la k-ésima «A» de la primera.
- En cada fila, la última letra es la que va **justo antes** de la primera letra en el texto.
  Saltando de una fila a la fila donde esa letra está en la primera columna, se recorre el texto
  **hacia atrás**.

| Líneas | Qué calcula |
|---|---|
| L11–15 | `rango[i]` = cuántas veces apareció la letra `ultima[i]` **antes** de la posición i; `vistos` = total de cada letra |
| L17–21 | `inicio[c]` = en qué fila empieza la letra c en la primera columna (las letras ordenadas, una detrás de otra) |
| L26 | Empieza en la fila que comienza con `$` (que es el texto original rotado) |
| L29–31 | Lee la última letra, y salta: `fila = inicio[c] + rango[fila]` |
| L34 | Se leyó al revés: se invierte y se quita el `$` |

**Traza con `ANNB$AA`:**
- `rango`: A→0, N→0, N→1, B→0, $→0, A→1, A→2
- `vistos`: A:3, N:2, B:1, $:1 · orden: `$ < A < B < N` · `inicio`: $:0, A:1, B:4, N:5

| fila | `ultima[fila]` | salto `inicio[c] + rango[fila]` | nueva fila |
|---|---|---|---|
| 0 | A | 1 + 0 | 1 |
| 1 | N | 5 + 0 | 5 |
| 5 | A | 1 + 1 | 2 |
| 2 | N | 5 + 1 | 6 |
| 6 | A | 1 + 2 | 3 |
| 3 | B | 4 + 0 | 4 |
| 4 | $ | 0 + 0 | 0 |

Leído: `A N A N A B $` → invertido `$BANANA` → sin `$`: **BANANA** ✔.

> **Error real que corregimos:** la primera versión usaba `fila = 0` («la fila 0 siempre empieza
> con `$`»). Es falso si el texto tiene espacios: el espacio (código ASCII 32) va **antes** que `$`
> (36). Una prueba automática con «tres tristes tigres…» lo detectó. Por eso L26 usa `inicio[FIN]`.

**Complejidad de la inversa:** O(n) más ordenar las letras distintas ⇒ O(n + k log k).

### 8.4 Código: move-to-front

`compresion/bwt.py` → `mover_al_frente`

```python
 1 │ def mover_al_frente(texto):
 2 │     """Move-to-front (MTF): cada letra se reemplaza por su posición en una lista
 3 │     que se reordena poniendo la última usada al frente. Tras la BWT, las letras
 4 │     repetidas producen muchos 0s, que Huffman/RLE comprimen muy bien."""
 5 │     lista = sorted(set(texto))
 6 │     salida = []
 7 │     for c in texto:
 8 │         i = lista.index(c)
 9 │         salida.append(i)
10 │         lista.insert(0, lista.pop(i))
11 │     return salida
```

- **L5** lista de letras distintas, ordenada.
- **L8–10** emite la posición de la letra en la lista y la **mueve al frente**.
- Una letra repetida seguida da **0**. Tras la BWT («ANNB$AA») hay muchas repeticiones ⇒ muchos 0
  ⇒ Huffman le da a 0 un código muy corto.
- En la frase «tres tristes tigres tragaban trigo en un trigal», RLE encuentra **47** rachas antes
  de la BWT y **33** después.

---

## Parte 9 · `aritmetica.py` — codificación aritmética

### 9.1 La idea

Todo el mensaje se convierte en **un solo número** dentro de [0, 1). Cada símbolo hace «zoom»
dentro de su tramo. Usa «fracciones de bit», por eso se acerca más a la entropía que Huffman. Se
usa en JPEG2000 y en H.264 (CABAC).

### 9.2 Código: el modelo

`compresion/aritmetica.py` → `modelo`

```python
 1 │ def modelo(texto):
 2 │     """Tramos acumulados: {símbolo: (inicio, fin)} con fracciones exactas."""
 3 │     conteos = Counter(texto)
 4 │     total = len(texto)
 5 │     tramos = {}
 6 │     acumulado = Fraction(0)
 7 │     for s in sorted(conteos):
 8 │         p = Fraction(conteos[s], total)
 9 │         tramos[s] = (acumulado, acumulado + p)
10 │         acumulado += p
11 │     return tramos
```

- **L6** `Fraction(0)`: fracciones **exactas** (3/5 es exactamente 3/5, no 0.6000000001). Así no
  hay errores de redondeo en la explicación.
- **L7–10** recorre los símbolos en orden y les asigna tramos consecutivos de tamaño p.
- `AABAC` → A: [0, 3/5) · B: [3/5, 4/5) · C: [4/5, 1).

### 9.3 Código: codificar

`compresion/aritmetica.py` → `codificar`

```python
 1 │ def codificar(texto, tramos=None, traza=None):
 2 │     """Devuelve (bits, tramos). `bits` es un string de '0'/'1' que representa
 3 │     el número binario 0.b1b2b3... que cae dentro del intervalo final."""
 4 │     if tramos is None:
 5 │         tramos = modelo(texto)
 6 │     bajo, alto = Fraction(0), Fraction(1)
 7 │     for s in texto:
 8 │         ancho = alto - bajo
 9 │         ini, fin = tramos[s]
10 │         bajo, alto = bajo + ancho * ini, bajo + ancho * fin     # zoom
11 │         if traza is not None:
12 │             traza.append((s, bajo, alto))
13 │     return _binario_mas_corto(bajo, alto), tramos
```

- **L6** se empieza con todo el intervalo [0, 1).
- **L8–10** el «zoom»: el tramo del símbolo, pero **dentro del intervalo actual**:
  `nuevo bajo = bajo + ancho × ini` y `nuevo alto = bajo + ancho × fin`.
- **L13** al final se busca el número con menos bits dentro del intervalo.

**Traza `AABAC`:**

| lee | tramo | ancho antes | nuevo intervalo | ancho nuevo |
|---|---|---|---|---|
| A | [0, 3/5) | 1 | [0, 3/5) | 0.6 |
| A | [0, 3/5) | 3/5 | [0, 9/25) | 0.36 |
| B | [3/5, 4/5) | 9/25 | [27/125, 36/125) | 0.072 |
| A | [0, 3/5) | 9/125 | [27/125, 162/625) | 0.0432 |
| C | [4/5, 1) | 27/625 | [783/3125, 162/625) | 0.00864 |

El ancho final = 3/5 · 3/5 · 1/5 · 3/5 · 1/5 = **producto de las probabilidades**. Los bits
necesarios ≈ −log2(ancho) = Σ −log2 p = **la entropía del mensaje** (6.86 bits).

### 9.4 Código: el número más corto

`compresion/aritmetica.py` → `_binario_mas_corto`

```python
1 │ def _binario_mas_corto(bajo, alto):
2 │     """Busca la fracción binaria con menos bits k tal que bajo <= m/2^k < alto."""
3 │     k = 0
4 │     while True:
5 │         k += 1
6 │         m = math.ceil(bajo * 2 ** k)          # el menor múltiplo de 1/2^k >= bajo
7 │         if Fraction(m, 2 ** k) < alto:
8 │             return format(m, "0%db" % k) if m > 0 else "0" * k
```

- Con k bits, los números posibles son `m / 2^k` (0.1 binario = 1/2, 0.01 = 1/4, …).
- **L6** `m = ceil(bajo × 2^k)`: el menor de esos números que es ≥ bajo.
- **L7** si además es < alto, cae dentro: se devuelve `m` en binario con k dígitos.

Traza para [0.25056, 0.25920):

| k | m = ceil(bajo · 2^k) | m / 2^k | ¿< 0.25920? |
|---|---|---|---|
| 1 | 1 | 0.5 | no |
| 2 | 2 | 0.5 | no |
| 3 | 3 | 0.375 | no |
| 4 | 5 | 0.3125 | no |
| 5 | 9 | 0.28125 | no |
| 6 | 17 | 0.265625 | no |
| 7 | 33 | **0.2578125** | **sí** → `0100001` |

**7 bits** para `AABAC` (la entropía decía 6.86).

### 9.5 Código: decodificar

`compresion/aritmetica.py` → `decodificar`

```python
 1 │ def decodificar(bits, tramos, n):
 2 │     """Reconstruye n símbolos: ver en qué tramo cae el número y hacer zoom."""
 3 │     x = Fraction(int(bits, 2), 2 ** len(bits)) if bits else Fraction(0)
 4 │     salida = []
 5 │     bajo, alto = Fraction(0), Fraction(1)
 6 │     for _ in range(n):
 7 │         ancho = alto - bajo
 8 │         pos = (x - bajo) / ancho              # dónde cae x dentro del intervalo
 9 │         for s, (ini, fin) in tramos.items():
10 │             if ini <= pos < fin:
11 │                 salida.append(s)
12 │                 bajo, alto = bajo + ancho * ini, bajo + ancho * fin
13 │                 break
14 │     return "".join(salida)
```

- **L3** convierte los bits en el número: `0100001` → 33/128.
- **L8** `pos` = dónde cae el número dentro del intervalo actual, de 0 a 1.
- **L9–13** busca el tramo que contiene `pos`, emite ese símbolo y hace el **mismo zoom** que el
  codificador.
- Necesita `n` (cuántos símbolos) para saber cuándo parar: el número solo no lo dice.

### 9.6 Por qué le gana a Huffman

Moneda cargada: `AAAAAAAAABAAAAAAAAAB` (90 % A).

| método | bits | por qué |
|---|---|---|
| Huffman | 20 | Cada símbolo necesita al menos **1 bit** entero |
| Aritmética | 8 | Una «A» cuesta solo −log2(0.9) = 0.15 bits |
| Shannon | 9.4 | Límite promedio (que salga 8 es suerte de alineación del intervalo) |

### 9.7 Complejidad

Con fracciones exactas, los números crecen con el mensaje: es lento para mensajes largos (solo
didáctico). Las implementaciones reales usan **enteros de precisión fija** y emiten bits a medida
que avanzan: O(n).

---

## Parte 10 · `jpeg_dct.py` — imágenes con pérdida

### 10.1 La idea

| Paso | Qué hace | ¿Pierde? |
|---|---|---|
| Bloques 8×8 | Divide la imagen | No |
| DCT | Pasa cada bloque a frecuencias | **No** |
| Cuantización | Divide por una tabla y redondea | **Sí** |
| Zigzag + RLE + Huffman | Comprime lo que queda | No |

### 10.2 La teoría de la DCT

Cualquier bloque 8×8 se puede escribir como **suma de 64 patrones** de coseno (desde «todo
parejo» hasta «rayas muy finas»). La DCT calcula **cuánto** de cada patrón tiene el bloque:

$$F(u,v) = \tfrac14 C(u) C(v) \sum_{x=0}^{7}\sum_{y=0}^{7} f(x,y)\cos\tfrac{(2x+1)u\pi}{16}\cos\tfrac{(2y+1)v\pi}{16}$$

con C(0) = 1/√2 y C(k>0) = 1.

- **F(0,0)** = DC = 8 × el promedio del bloque.
- Hacia abajo-derecha: patrones cada vez más finos (frecuencias altas = detalles).
- En fotos reales casi toda la «energía» está en pocas frecuencias bajas.

Constantes precalculadas (para no recalcular cosenos en cada bloque):

```python
_COS = [[math.cos((2 * x + 1) * u * math.pi / 16) for u in range(N)] for x in range(N)]
_C = [1 / math.sqrt(2)] + [1.0] * (N - 1)
```

### 10.3 Código: DCT e inversa

`compresion/jpeg_dct.py` → `dct2`

```python
 1 │ def dct2(bloque):
 2 │     """DCT-II 2D de un bloque 8×8 (valores ya centrados en 0: píxel − 128)."""
 3 │     F = [[0.0] * N for _ in range(N)]
 4 │     for u in range(N):
 5 │         for v in range(N):
 6 │             s = 0.0
 7 │             for x in range(N):
 8 │                 for y in range(N):
 9 │                     s += bloque[x][y] * _COS[x][u] * _COS[y][v]
10 │             F[u][v] = 0.25 * _C[u] * _C[v] * s
11 │     return F
```

`compresion/jpeg_dct.py` → `idct2`

```python
 1 │ def idct2(F):
 2 │     """DCT inversa (DCT-III): vuelve de frecuencias a píxeles."""
 3 │     f = [[0.0] * N for _ in range(N)]
 4 │     for x in range(N):
 5 │         for y in range(N):
 6 │             s = 0.0
 7 │             for u in range(N):
 8 │                 for v in range(N):
 9 │                     s += _C[u] * _C[v] * F[u][v] * _COS[x][u] * _COS[y][v]
10 │             f[x][y] = 0.25 * s
11 │     return f
```

- **dct2 L4–5** recorre las 64 frecuencias (u, v).
- **L7–9** suma sobre los 64 píxeles: píxel × patrón coseno horizontal × vertical.
- **L10** aplica la normalización de la fórmula.
- **idct2** hace la suma al revés (sobre las frecuencias) y devuelve los píxeles.
- 4 ciclos de 8 ⇒ 8⁴ = 4 096 multiplicaciones por bloque. (Los JPEG reales usan una DCT rápida.)
- **DCT → IDCT da el bloque original** (error ≈ 10⁻¹⁴, solo redondeo de la computadora): por eso
  la DCT no pierde nada.

### 10.4 Código: cuantización

```python
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
```

Es la tabla **oficial** del estándar JPEG (Anexo K) para luminancia a calidad 50. Números chicos
arriba-izquierda (se conservan con precisión), grandes abajo-derecha (el ojo casi no nota esos
detalles).

`compresion/jpeg_dct.py` → `tabla_calidad`

```python
1 │ def tabla_calidad(calidad):
2 │     """Escala la tabla estándar según la calidad (1-100), igual que libjpeg."""
3 │     calidad = max(1, min(100, calidad))
4 │     escala = 5000 / calidad if calidad < 50 else 200 - 2 * calidad
5 │     return [[max(1, min(255, int((q * escala + 50) // 100))) for q in fila]
6 │             for fila in TABLA_Q50]
```

`compresion/jpeg_dct.py` → `cuantizar`

```python
1 │ def cuantizar(F, Q):
2 │     """El paso con PÉRDIDA: dividir y redondear al entero más cercano."""
3 │     return [[int(round(F[u][v] / Q[u][v])) for v in range(N)] for u in range(N)]
```

`compresion/jpeg_dct.py` → `descuantizar`

```python
1 │ def descuantizar(Fq, Q):
2 │     return [[Fq[u][v] * Q[u][v] for v in range(N)] for u in range(N)]
```

- `tabla_calidad` **L4**: calidad < 50 → escala = 5000/calidad (calidad 10 → 500 %); calidad ≥ 50
  → 200 − 2·calidad (calidad 90 → 20 %). **L5** escala cada número y lo mantiene entre 1 y 255.
  Es la fórmula de libjpeg.
- `cuantizar` divide y **redondea**: aquí se pierde. Ejemplos con el bloque de la demo:
  - −55 / 11 = −5.0 → **−5** → al reconstruir −5 × 11 = −55 (casi perfecto).
  - −2 / 10 = −0.2 → **0** → al reconstruir 0: ese detalle **desapareció**.
- `descuantizar` multiplica de vuelta (no recupera lo redondeado).

### 10.5 Código: zigzag y símbolos

`compresion/jpeg_dct.py` → `orden_zigzag`

```python
1 │ def orden_zigzag():
2 │     """Posiciones (u,v) en el orden zigzag de JPEG: de bajas a altas frecuencias."""
3 │     return sorted(((u, v) for u in range(N) for v in range(N)),
4 │                   key=lambda p: (p[0] + p[1], p[0] if (p[0] + p[1]) % 2 else p[1]))
```

- Ordena las 64 posiciones por diagonal `u + v`. Dentro de una diagonal, si es impar, por fila
  `u` creciente; si es par, por columna `v` creciente. Resultado: (0,0), (0,1), (1,0), (2,0),
  (1,1), (0,2), (0,3), (1,2), … = el zigzag de JPEG, de frecuencias bajas a altas.

`compresion/jpeg_dct.py` → `simbolos_entropia`

```python
 1 │ def simbolos_entropia(Fq, dc_anterior):
 2 │     """Convierte un bloque cuantizado en símbolos para Huffman, como JPEG:
 3 │        - DC: se guarda la DIFERENCIA con el DC del bloque anterior.
 4 │        - AC: pares (ceros_antes, valor) recorriendo en zigzag; 'EOB' (fin de
 5 │          bloque) cuando todo lo que queda es 0."""
 6 │     secuencia = [Fq[u][v] for u, v in ZIGZAG]
 7 │     simbolos = [("DC", secuencia[0] - dc_anterior)]
 8 │     ac = secuencia[1:]
 9 │     ultimo_no_cero = max((i for i, c in enumerate(ac) if c != 0), default=-1)
10 │     ceros = 0
11 │     for c in ac[:ultimo_no_cero + 1]:
12 │         if c == 0:
13 │             ceros += 1
14 │         else:
15 │             simbolos.append((ceros, c))
16 │             ceros = 0
17 │     simbolos.append("EOB")
18 │     return simbolos, secuencia[0]
```

- **L6** lee el bloque en zigzag.
- **L7** el DC se guarda como **diferencia** con el bloque anterior (bloques vecinos tienen
  promedios parecidos ⇒ diferencias chicas).
- **L9** busca el último coeficiente distinto de 0 (`default=-1` si todos son 0).
- **L11–16** recorre hasta ahí: cuenta ceros seguidos y, al encontrar un no-cero, guarda
  `(ceros_antes, valor)`. Es un **RLE de ceros**.
- **L17** `"EOB"` (*end of block*): «el resto son ceros».

Bloque de ejemplo cuantizado (calidad 50):

```
  2  -5   0   0   0   0   0   0
 -9   0   0   0   0   0   0   0
  0   0   0   0   0   0   0   0
 -1   0   0   0   0   0   0   0
  0 … (todo ceros)
```

Zigzag: 2, −5, −9, 0, 0, 0, 0, 0, 0, −1, 0, 0, … → símbolos
`[('DC', 2), (0, -5), (0, -9), (6, -1), 'EOB']`: **64 números → 5 símbolos**.

### 10.6 Código: imagen completa y PSNR

`compresion/jpeg_dct.py` → `comprimir_imagen`

```python
 1 │ def comprimir_imagen(img, calidad):
 2 │     """Aplica toda la tubería JPEG (en grises) a una imagen cuyo ancho y alto
 3 │     sean múltiplos de 8. Devuelve (imagen_reconstruida, bits_estimados, ceros)."""
 4 │     alto, ancho = len(img), len(img[0])
 5 │     Q = tabla_calidad(calidad)
 6 │     salida = [[0.0] * ancho for _ in range(alto)]
 7 │     todos_simbolos = []
 8 │     dc_anterior = 0
 9 │     ceros = 0
10 │     for by in range(0, alto, N):
11 │         for bx in range(0, ancho, N):
12 │             bloque = [[img[by + i][bx + j] - 128 for j in range(N)] for i in range(N)]
13 │             Fq = cuantizar(dct2(bloque), Q)
14 │             ceros += sum(1 for fila in Fq for c in fila if c == 0)
15 │             simbolos, dc_anterior = simbolos_entropia(Fq, dc_anterior)
16 │             todos_simbolos.extend(simbolos)
17 │             rec = idct2(descuantizar(Fq, Q))
18 │             for i in range(N):
19 │                 for j in range(N):
20 │                     salida[by + i][bx + j] = max(0, min(255, rec[i][j] + 128))
21 │     bits, _ = huffman.codificar(todos_simbolos)
22 │     return salida, len(bits), ceros
```

`compresion/jpeg_dct.py` → `psnr`

```python
1 │ def psnr(a, b):
2 │     """Peak Signal-to-Noise Ratio en dB: más alto = más parecido (>35 dB ≈ excelente)."""
3 │     mse = sum((a[i][j] - b[i][j]) ** 2 for i in range(len(a)) for j in range(len(a[0])))
4 │     mse /= len(a) * len(a[0])
5 │     return float("inf") if mse == 0 else 10 * math.log10(255 ** 2 / mse)
```

- **L10–11** recorre la imagen de 8 en 8.
- **L12** recorta el bloque y resta 128.
- **L13** DCT + cuantización. **L14** cuenta ceros. **L15–16** genera los símbolos.
- **L17–20** reconstruye (como haría quien abre la foto) y limita a 0–255.
- **L21** pasa **todos** los símbolos por **nuestro Huffman** para estimar el tamaño final.
- `psnr`: error cuadrático medio (**L3–4**) y `10·log10(255²/ECM)` (**L5**). Más alto = más
  parecido. > 35 dB casi indistinguible; < 25 dB se ven los bloques.

| calidad | bits | % del original | coef. en 0 | PSNR |
|---|---|---|---|---|
| 90 | 5 272 | 16.1 % | 3 274 / 4 096 | 42.6 dB |
| 50 | 2 751 | 8.4 % | 3 631 / 4 096 | 32.2 dB |
| 10 | 1 099 | 3.4 % | 3 891 / 4 096 | 24.5 dB |
| 2 | 491 | 1.5 % | 4 017 / 4 096 | 22.0 dB |

---

## Parte 11 · `audio.py` — enmascaramiento psicoacústico

### 11.1 La idea

Un sonido fuerte **tapa** a los débiles de frecuencias cercanas: el oído no los percibe. El códec
los borra. Constantes: `FS = 8000` muestras por segundo, `TRAMA = 512` muestras por trama.

### 11.2 Código: FFT

`compresion/audio.py` → `fft`

```python
 1 │ def fft(x):
 2 │     """FFT recursiva de Cooley-Tukey (divide y vencerás): O(n log n).
 3 │     `x` debe tener longitud potencia de 2."""
 4 │     n = len(x)
 5 │     if n == 1:
 6 │         return [complex(x[0])]
 7 │     pares = fft(x[0::2])
 8 │     impares = fft(x[1::2])
 9 │     resultado = [0j] * n
10 │     for k in range(n // 2):
11 │         t = cmath.exp(-2j * math.pi * k / n) * impares[k]
12 │         resultado[k] = pares[k] + t
13 │         resultado[k + n // 2] = pares[k] - t
14 │     return resultado
```

**Teoría:** la transformada de Fourier dice cuánta energía hay en cada frecuencia. La versión
directa cuesta O(n²). La **FFT** de Cooley-Tukey usa **divide y vencerás**:

| Líneas | Qué hace |
|---|---|
| L5–6 | Caso base: 1 muestra |
| L7–8 | Resuelve **recursivamente** las posiciones pares (`x[0::2]`) y las impares (`x[1::2]`) |
| L10–13 | Combina: cada resultado de las impares se multiplica por un «factor de giro» `e^(−2πik/n)` y se suma/resta al de las pares (la «mariposa») |

Recurrencia **T(n) = 2T(n/2) + O(n) ⇒ O(n log n)**, igual que *merge sort*. Requiere que n sea
potencia de 2 (512 = 2⁹).

`compresion/audio.py` → `ifft`

```python
1 │ def ifft(X):
2 │     """Inversa: conjugar, aplicar FFT, conjugar y dividir entre n."""
3 │     n = len(X)
4 │     return [v.conjugate() / n for v in fft([v.conjugate() for v in X])]
```

`compresion/audio.py` → `db`

```python
1 │ def db(magnitud):
2 │     return 20 * math.log10(magnitud) if magnitud > 1e-12 else -240.0
```

- `ifft`: truco matemático: conjugar, aplicar la FFT, conjugar y dividir entre n da la inversa.
- `db`: convierte amplitud a decibeles (`20·log10`). Para 0 devuelve −240 (en vez de −∞).

### 11.3 Código: la curva de enmascaramiento

`compresion/audio.py` → `curva_enmascaramiento`

```python
 1 │ def curva_enmascaramiento(niveles, resolucion, caida_db_por_100hz=6.0, margen_db=20.0,
 2 │                           umbral_absoluto_db=-60.0):
 3 │     """Calcula, para cada frecuencia, el umbral por debajo del cual NO se oye.
 4 │     Devuelve (umbrales, picos)."""
 5 │     mitad = len(niveles) - 1
 6 │     # Picos = máximos locales por encima del umbral absoluto.
 7 │     picos = [k for k in range(1, mitad) if niveles[k] > umbral_absoluto_db
 8 │              and niveles[k] >= niveles[k - 1] and niveles[k] >= niveles[k + 1]]
 9 │     umbrales = []
10 │     for k in range(mitad + 1):
11 │         umbral = umbral_absoluto_db
12 │         for p in picos:
13 │             if p == k:
14 │                 continue
15 │             distancia_hz = abs(k - p) * resolucion
16 │             # La curva de enmascaramiento: margen bajo el pico, y cae al alejarse.
17 │             enmascara = niveles[p] - margen_db - caida_db_por_100hz * distancia_hz / 100
18 │             umbral = max(umbral, enmascara)
19 │         umbrales.append(umbral)
20 │     return umbrales, picos
```

| Líneas | Qué hace |
|---|---|
| L7–8 | **Picos**: frecuencias más fuertes que sus dos vecinas y audibles (> −60 dB) |
| L10–11 | Para cada frecuencia k, el umbral empieza en el **umbral absoluto** de audición (−60 dB) |
| L12–14 | Cada pico (menos el propio k) la puede tapar |
| L15 | Distancia en Hz entre k y el pico (cada casilla mide 8000/512 = 15.625 Hz) |
| L17 | Cuánto tapa ese pico: su nivel − 20 dB − 6 dB por cada 100 Hz de distancia |
| L18 | El umbral es el **máximo** de todo lo que la tapa |

### 11.4 Código: comprimir una trama y la señal

`compresion/audio.py` → `comprimir_trama`

```python
 1 │ def comprimir_trama(trama, caida_db_por_100hz=6.0, margen_db=20.0, umbral_absoluto_db=-60.0):
 2 │     """Aplica el modelo psicoacústico a una trama. Devuelve (trama_reconstruida,
 3 │     componentes_conservados, componentes_audibles_antes, lista_de_borrados_en_Hz).
 4 │     'Audibles antes' = componentes por encima del umbral absoluto de audición."""
 5 │     n = len(trama)
 6 │     X = fft(trama)
 7 │     mitad = n // 2
 8 │     resolucion = FS / n                                 # Hz por "bin"
 9 │     niveles = [db(abs(X[k]) / (n / 2)) for k in range(mitad + 1)]
10 │     umbrales, picos = curva_enmascaramiento(niveles, resolucion, caida_db_por_100hz,
11 │                                             margen_db, umbral_absoluto_db)
12 │ 
13 │     conservados = 0
14 │     borrados = []
15 │     Y = [0j] * n
16 │     for k in range(mitad + 1):
17 │         umbral = umbrales[k]
18 │         if niveles[k] > umbral:
19 │             Y[k] = X[k]
20 │             if k not in (0, mitad):
21 │                 Y[n - k] = X[n - k]                     # simetría de una señal real
22 │             conservados += 1
23 │         elif niveles[k] > -100 and k in picos:
24 │             borrados.append(round(k * resolucion))
25 │     reconstruida = [v.real for v in ifft(Y)]
26 │     audibles = sum(1 for k in range(mitad + 1) if niveles[k] > umbral_absoluto_db)
27 │     return reconstruida, conservados, audibles, borrados
```

`compresion/audio.py` → `comprimir`

```python
 1 │ def comprimir(senal, **parametros):
 2 │     salida = []
 3 │     cons_total = tot_total = 0
 4 │     borrados = set()
 5 │     for i in range(0, len(senal) - TRAMA + 1, TRAMA):
 6 │         rec, c, t, b = comprimir_trama(senal[i:i + TRAMA], **parametros)
 7 │         salida.extend(rec)
 8 │         cons_total += c
 9 │         tot_total += t
10 │         borrados.update(b)
11 │     return salida, cons_total, tot_total, sorted(borrados)
```

- **L6** pasa la trama a frecuencias. **L9** nivel en dB de cada frecuencia.
- **L16–22** conserva solo lo que está **por encima** del umbral; el resto queda en 0 (borrado).
  **L20–21**: el espectro de una señal real es **simétrico** (la casilla k y la n−k son espejo), por
  eso se copian las dos.
- **L23–24** anota qué picos se borraron (para mostrarlo).
- **L25** vuelve al tiempo con la FFT inversa.
- `comprimir` aplica lo mismo a cada trama de 512 muestras, como hace MP3.

### 11.5 Traza con los números

Tonos de prueba: 1000 Hz a −4.4 dB (fuerte), 1156 Hz a −40 dB (débil), 3000 Hz a −12 dB, 3094 Hz a
−46 dB y 2000 Hz a −40 dB.

| tono | pico más cercano | umbral que pone (L17) | umbral final | ¿nivel > umbral? |
|---|---|---|---|---|
| 1156 Hz, −40 dB | 1000 Hz (156 Hz) | −4.4 − 20 − 6·1.56 = **−33.8** | −33.8 | −40 < −33.8 → **se borra** |
| 3094 Hz, −46 dB | 3000 Hz (94 Hz) | −12 − 20 − 6·0.94 = **−37.6** | −37.6 | −46 < −37.6 → **se borra** |
| 2000 Hz, −40 dB | 1000 Hz (1000 Hz) | −4.4 − 20 − 60 = −84.4 | −60 (absoluto) | −40 > −60 → **se conserva** |

El de 1156 Hz y el de 2000 Hz tienen **el mismo volumen**; uno se borra y el otro no. Lo que decide
es si hay un sonido fuerte **cerca**.

> **Nyquist:** todas las frecuencias deben ser menores que FS/2 = 4000 Hz. Un tono de 6000 Hz se
> «disfraza» de 2000 Hz (*aliasing*). Nos pasó en una primera versión.

---

## Parte 12 · `video.py` — cuadros I/P y vectores de movimiento

### 12.1 La idea

El cuadro **I** se guarda completo. En cada cuadro **P**, por cada bloque 8×8 se busca en el cuadro
anterior el bloque más parecido y se guarda solo el **vector de movimiento** y el **residuo**.
Constantes: `BLOQUE = 8`, `BUSQUEDA = 4` (desplazamientos de −4 a +4).

### 12.2 Código: SAD

`compresion/video.py` → `sad`

```python
1 │ def sad(ref, cur, bx, by, dx, dy):
2 │     """Sum of Absolute Differences: qué tan distinto es el bloque (bx,by) del
3 │     cuadro actual respecto al bloque desplazado (dx,dy) en la referencia."""
4 │     total = 0
5 │     for y in range(BLOQUE):
6 │         for x in range(BLOQUE):
7 │             total += abs(cur[by + y][bx + x] - ref[by + y + dy][bx + x + dx])
8 │     return total
```

*Sum of Absolute Differences*: suma de |actual − referencia desplazada| sobre los 64 píxeles.
0 = idénticos. Es la medida de «parecido» que usan los códecs reales (es barata de calcular).

### 12.3 Código: estimación de movimiento

`compresion/video.py` → `estimar_movimiento`

```python
 1 │ def estimar_movimiento(ref, cur):
 2 │     """Para cada bloque busca el desplazamiento con menor SAD (búsqueda completa
 3 │     en una ventana ±BUSQUEDA). Devuelve {(bx,by): (dx,dy)}."""
 4 │     alto, ancho = len(cur), len(cur[0])
 5 │     vectores = {}
 6 │     for by in range(0, alto, BLOQUE):
 7 │         for bx in range(0, ancho, BLOQUE):
 8 │             mejor = (sad(ref, cur, bx, by, 0, 0), 0, 0)       # preferimos (0,0) si empata
 9 │             for dy in range(-BUSQUEDA, BUSQUEDA + 1):
10 │                 for dx in range(-BUSQUEDA, BUSQUEDA + 1):
11 │                     if 0 <= by + dy and by + dy + BLOQUE <= alto and \
12 │                        0 <= bx + dx and bx + dx + BLOQUE <= ancho:
13 │                         s = sad(ref, cur, bx, by, dx, dy)
14 │                         if s < mejor[0]:
15 │                             mejor = (s, dx, dy)
16 │             vectores[(bx, by)] = (mejor[1], mejor[2])
17 │     return vectores
```

- **L6–7** recorre los bloques.
- **L8** empieza suponiendo «no se movió» (0, 0). Como luego solo cambia si encuentra algo
  **estrictamente** mejor (L14), ante un empate gana (0, 0): así el fondo quieto no recibe vectores
  raros.
- **L9–10** prueba los 9 × 9 = 81 desplazamientos.
- **L11–12** solo si el bloque desplazado cabe dentro de la imagen.
- **L16** guarda el mejor vector del bloque.
- **Complejidad por cuadro:** (número de bloques) × 81 × 64. Con 48×48 px: 36 × 81 × 64 ≈ 187 000
  operaciones. Los códecs reales usan búsquedas más rápidas (diamante, jerárquica).

### 12.4 Código: predicción, codificación y costo

`compresion/video.py` → `predecir`

```python
1 │ def predecir(ref, vectores, ancho, alto):
2 │     """Arma la predicción copiando bloques de la referencia según los vectores."""
3 │     pred = [[0] * ancho for _ in range(alto)]
4 │     for (bx, by), (dx, dy) in vectores.items():
5 │         for y in range(BLOQUE):
6 │             for x in range(BLOQUE):
7 │                 pred[by + y][bx + x] = ref[by + y + dy][bx + x + dx]
8 │     return pred
```

`compresion/video.py` → `codificar`

```python
 1 │ def codificar(video):
 2 │     """Primer cuadro = I (completo). Los demás = P (vectores + residuo)."""
 3 │     alto, ancho = len(video[0]), len(video[0][0])
 4 │     flujo = [("I", [fila[:] for fila in video[0]])]
 5 │     referencia = video[0]
 6 │     for cur in video[1:]:
 7 │         vectores = estimar_movimiento(referencia, cur)
 8 │         pred = predecir(referencia, vectores, ancho, alto)
 9 │         residuo = [[cur[y][x] - pred[y][x] for x in range(ancho)] for y in range(alto)]
10 │         flujo.append(("P", vectores, residuo))
11 │         referencia = cur          # (sin pérdida aquí, la referencia es exacta)
12 │     return flujo
```

`compresion/video.py` → `decodificar`

```python
 1 │ def decodificar(flujo):
 2 │     video = []
 3 │     referencia = None
 4 │     for cuadro in flujo:
 5 │         if cuadro[0] == "I":
 6 │             img = [fila[:] for fila in cuadro[1]]
 7 │         else:
 8 │             _, vectores, residuo = cuadro
 9 │             alto, ancho = len(residuo), len(residuo[0])
10 │             pred = predecir(referencia, vectores, ancho, alto)
11 │             img = [[pred[y][x] + residuo[y][x] for x in range(ancho)] for y in range(alto)]
12 │         video.append(img)
13 │         referencia = img
14 │     return video
```

`compresion/video.py` → `costo`

```python
1 │ def costo(cuadro):
2 │     """Valores a guardar: un cuadro I guarda todos los píxeles; un P guarda
3 │     2 números por vector + solo los valores del residuo distintos de 0."""
4 │     if cuadro[0] == "I":
5 │         return sum(len(f) for f in cuadro[1])
6 │     _, vectores, residuo = cuadro
7 │     return 2 * len(vectores) + sum(1 for f in residuo for v in f if v != 0)
```

- `predecir`: arma un cuadro **copiando** cada bloque desde donde dice su vector.
- `codificar` **L4**: el primero es I (copia completa). **L7–9**: para cada P, vectores →
  predicción → residuo = real − predicción. **L11**: el cuadro actual es la referencia del siguiente.
- `decodificar` **L11**: predicción + residuo = cuadro exacto.
- `costo`: I = todos los píxeles; P = 2 números por vector + residuos ≠ 0.

**Cómo leer `(−2, −1)`:** el contenido del bloque estaba 2 px a la izquierda y 1 arriba en el
cuadro anterior ⇒ el objeto **se movió 2 a la derecha y 1 abajo**.

Resultado de la demo (6 cuadros de 32×32): **6 144** valores sin comprimir → **1 817** con
predicción (29.6 %), y el decodificador reconstruye el video exacto.

---

## Parte 13 · `archivo.py` — compresor real de archivos

### 13.1 La idea

Un programa que comprime **cualquier archivo** a un formato propio (`.edd`) y lo descomprime. Dos
métodos: **Huffman** sobre los bytes y **mini-DEFLATE** (LZ77 + Huffman, la idea del ZIP).

### 13.2 Código: escribir y leer bits

`compresion/archivo.py` → `EscritorBits`

```python
 1 │ class EscritorBits:
 2 │     def __init__(self):
 3 │         self.bytes = bytearray()
 4 │         self._acum = 0          # bits pendientes (como entero)
 5 │         self._n = 0             # cuántos bits pendientes hay
 6 │ 
 7 │     def escribir(self, valor, cantidad_bits):
 8 │         """Agrega los `cantidad_bits` bits menos significativos de `valor`."""
 9 │         self._acum = (self._acum << cantidad_bits) | valor
10 │         self._n += cantidad_bits
11 │         while self._n >= 8:
12 │             self._n -= 8
13 │             self.bytes.append((self._acum >> self._n) & 0xFF)
14 │         self._acum &= (1 << self._n) - 1
15 │ 
16 │     def terminar(self):
17 │         """Rellena con ceros el último byte incompleto."""
18 │         if self._n:
19 │             self.bytes.append((self._acum << (8 - self._n)) & 0xFF)
20 │             self._acum = self._n = 0
21 │         return bytes(self.bytes)
```

| Líneas | Qué hace |
|---|---|
| L3–5 | `bytes` (salida), `_acum` (bits pendientes guardados en un entero) y `_n` (cuántos) |
| L9 | `<<` corre lo pendiente a la izquierda para hacer espacio; `\|` (O de bits) pega los bits nuevos |
| L11–13 | Mientras haya 8 o más: los **8 de más a la izquierda** se sacan con `>> _n` y se recortan a 8 bits con `& 0xFF` (0xFF = 11111111) |
| L14 | Borra los bits ya escritos: `(1 << n) − 1` es una máscara con n unos |
| L18–20 | `terminar`: si quedan bits sueltos, rellena con ceros a la derecha hasta 8 |

**Traza:** escribir `10` (2 bits), `110` (3 bits), `1111` (4 bits):

| operación | `_acum` (binario) | `_n` | byte emitido |
|---|---|---|---|
| escribir(0b10, 2) | `10` | 2 | — |
| escribir(0b110, 3) | `10110` | 5 | — |
| escribir(0b1111, 4) | `101101111` | 9 → 1 | `10110111` (183) |
| | `1` | 1 | |
| terminar() | | | `10000000` (128) |

`compresion/archivo.py` → `LectorBits`

```python
 1 │ class LectorBits:
 2 │     def __init__(self, datos):
 3 │         self.datos = datos
 4 │         self.pos = 0            # posición en bits
 5 │ 
 6 │     def leer_bit(self):
 7 │         byte = self.datos[self.pos >> 3]
 8 │         bit = (byte >> (7 - (self.pos & 7))) & 1
 9 │         self.pos += 1
10 │         return bit
11 │ 
12 │     def leer(self, cantidad_bits):
13 │         valor = 0
14 │         for _ in range(cantidad_bits):
15 │             valor = (valor << 1) | self.leer_bit()
16 │         return valor
```

- `pos >> 3` = `pos // 8` (en qué byte está el bit). `pos & 7` = `pos % 8` (qué bit del byte).
- `byte >> (7 − …) & 1` saca ese bit (de izquierda a derecha).
- `leer(n)` arma un número con n bits seguidos.

### 13.3 Código: de frecuencias a tablas

`compresion/archivo.py` → `_longitudes`

```python
1 │ def _longitudes(frecuencias, tam_alfabeto):
2 │     """Longitud del código de cada símbolo (0 = el símbolo no aparece)."""
3 │     longitudes = [0] * tam_alfabeto
4 │     if not frecuencias:
5 │         return longitudes
6 │     raiz = huffman.construir_arbol(frecuencias)
7 │     for simbolo, codigo in huffman.generar_codigos(raiz).items():
8 │         longitudes[simbolo] = len(codigo)
9 │     return longitudes
```

`compresion/archivo.py` → `_tabla_codificacion`

```python
1 │ def _tabla_codificacion(longitudes):
2 │     """{símbolo: (código_entero, longitud)} usando la regla canónica."""
3 │     presentes = {s: l for s, l in enumerate(longitudes) if l > 0}
4 │     if not presentes:
5 │         return {}
6 │     canon = huffman.codigos_canonicos(presentes)
7 │     return {s: (int(c, 2), len(c)) for s, c in canon.items()}
```

`compresion/archivo.py` → `_tabla_decodificacion`

```python
1 │ def _tabla_decodificacion(longitudes):
2 │     """{(longitud, código_entero): símbolo}: al leer bits, vamos armando
3 │     (longitud, valor) y consultamos esta TABLA HASH en O(1)."""
4 │     return {(l, c): s for s, (c, l) in _tabla_codificacion(longitudes).items()}
```

- `_longitudes`: usa **nuestro** `huffman.construir_arbol` y `generar_codigos`, y guarda solo la
  **longitud** de cada código en una lista de tamaño fijo (0 = el símbolo no aparece).
- `_tabla_codificacion`: longitudes → **códigos canónicos** (`huffman.codigos_canonicos`) →
  `{símbolo: (código como entero, longitud)}`.
- `_tabla_decodificacion`: al revés, `{(longitud, código): símbolo}`. La longitud va en la clave
  porque `0`, `00` y `000` son el mismo número entero.

`compresion/archivo.py` → `_leer_simbolo`

```python
1 │ def _leer_simbolo(lector, tabla_dec):
2 │     codigo = longitud = 0
3 │     while True:
4 │         codigo = (codigo << 1) | lector.leer_bit()
5 │         longitud += 1
6 │         if (longitud, codigo) in tabla_dec:
7 │             return tabla_dec[(longitud, codigo)]
8 │         if longitud > 600:
9 │             raise ValueError("archivo corrupto")
```

Lee bit por bit armando `(longitud, código)` y pregunta a la **tabla hash** en cada bit. Como los
códigos son libres de prefijo, la primera coincidencia es la correcta. L8–9 evitan un ciclo infinito
si el archivo está dañado.

### 13.4 Código: método Huffman

`compresion/archivo.py` → `comprimir_huffman`

```python
1 │ def comprimir_huffman(datos: bytes) -> bytes:
2 │     longitudes = _longitudes(Counter(datos), 256)
3 │     tabla = _tabla_codificacion(longitudes)
4 │     w = EscritorBits()
5 │     for b in datos:
6 │         codigo, l = tabla[b]
7 │         w.escribir(codigo, l)
8 │     cabecera = FIRMA + struct.pack("<BI", METODO_HUFFMAN, len(datos)) + bytes(longitudes)
9 │     return cabecera + w.terminar()
```

`compresion/archivo.py` → `_descomprimir_huffman`

```python
1 │ def _descomprimir_huffman(cuerpo, tamano):
2 │     longitudes = list(cuerpo[:256])
3 │     tabla_dec = _tabla_decodificacion(longitudes)
4 │     lector = LectorBits(cuerpo[256:])
5 │     return bytes(_leer_simbolo(lector, tabla_dec) for _ in range(tamano))
```

- **L2** frecuencias de los 256 valores de byte → longitudes.
- **L5–7** escribe el código de cada byte.
- **L8** cabecera: `FIRMA` (`b"EDD2"`) + `struct.pack("<BI", método, tamaño)` (1 byte + 4 bytes,
  *little-endian*) + las 256 longitudes.
- Descomprimir: lee las 256 longitudes, reconstruye la tabla y lee `tamano` símbolos.

### 13.5 Código: método mini-DEFLATE

`compresion/archivo.py` → `comprimir_deflate`

```python
 1 │ def comprimir_deflate(datos: bytes) -> bytes:
 2 │     tokens = lz77.codificar(datos)
 3 │     simbolos = [t[1] if t[0] == "L" else 256 + t[2] - 3 for t in tokens]
 4 │     longitudes = _longitudes(Counter(simbolos), TAM_ALFABETO_DEFLATE)
 5 │     tabla = _tabla_codificacion(longitudes)
 6 │     w = EscritorBits()
 7 │     for t, s in zip(tokens, simbolos):
 8 │         codigo, l = tabla[s]
 9 │         w.escribir(codigo, l)
10 │         if t[0] == "R":
11 │             w.escribir(t[1] - 1, BITS_DISTANCIA)
12 │     cabecera = FIRMA + struct.pack("<BI", METODO_DEFLATE, len(datos)) + bytes(longitudes)
13 │     return cabecera + w.terminar()
```

`compresion/archivo.py` → `_descomprimir_deflate`

```python
 1 │ def _descomprimir_deflate(cuerpo, tamano):
 2 │     longitudes = list(cuerpo[:TAM_ALFABETO_DEFLATE])
 3 │     tabla_dec = _tabla_decodificacion(longitudes)
 4 │     lector = LectorBits(cuerpo[TAM_ALFABETO_DEFLATE:])
 5 │     salida = bytearray()
 6 │     while len(salida) < tamano:
 7 │         s = _leer_simbolo(lector, tabla_dec)
 8 │         if s < 256:
 9 │             salida.append(s)
10 │         else:
11 │             longitud = s - 256 + 3
12 │             distancia = lector.leer(BITS_DISTANCIA) + 1
13 │             inicio = len(salida) - distancia
14 │             for k in range(longitud):
15 │                 salida.append(salida[inicio + k])
16 │     return bytes(salida)
```

- **L2** primero LZ77 (Parte 6).
- **L3** convierte cada token en un símbolo de un **alfabeto de 513**: 0–255 = byte literal;
  256–511 = «copia de longitud símbolo − 256 + 3» (3 a 258).
- **L4–5** Huffman canónico sobre esos símbolos: así también aprende qué longitudes de copia son
  comunes.
- **L10–11** en las referencias, la distancia va después con **15 bits fijos** (1 a 32 768).
- Descomprimir **L8–9** literal; **L10–15** referencia: lee la distancia y copia de a un byte (como
  `lz77.decodificar`).

### 13.6 Código: descomprimir y medir

`compresion/archivo.py` → `descomprimir`

```python
 1 │ def descomprimir(comprimido: bytes) -> bytes:
 2 │     if comprimido[:4] != FIRMA:
 3 │         raise ValueError("no es un archivo .edd (firma incorrecta)")
 4 │     metodo, tamano = struct.unpack("<BI", comprimido[4:9])
 5 │     cuerpo = comprimido[9:]
 6 │     if metodo == METODO_HUFFMAN:
 7 │         return _descomprimir_huffman(cuerpo, tamano)
 8 │     if metodo == METODO_DEFLATE:
 9 │         return _descomprimir_deflate(cuerpo, tamano)
10 │     raise ValueError("método desconocido en la cabecera: %d" % metodo)
```

`compresion/archivo.py` → `medir`

```python
 1 │ def medir(datos: bytes):
 2 │     """Comprime con cada método y verifica que se recupere el original.
 3 │     Devuelve [(nombre, bytes_comprimidos, porcentaje, segundos, ok, propio), ...]."""
 4 │     resultados = []
 5 │     for etiqueta, comp, desc, propio in METODOS:
 6 │         t0 = time.perf_counter()
 7 │         c = comp(datos)
 8 │         t = time.perf_counter() - t0
 9 │         ok = desc(c) == datos
10 │         pct = 100 * len(c) / len(datos) if datos else 0
11 │         resultados.append((etiqueta, len(c), pct, t, ok, propio))
12 │     return resultados
```

- `descomprimir` **L2–3** revisa la firma; **L4** lee método y tamaño; elige el método.
- `medir` comprime con cada método de la lista `METODOS` (los nuestros y zlib, bz2, lzma), mide el
  tiempo y **verifica** que al descomprimir salga exactamente lo mismo (L9).

### 13.7 Formato `.edd`

```
┌──────┬────────┬──────────────┬────────────────────────────┬───────────────┐
│ EDD2 │ método │ tamaño orig. │ longitudes (256 ó 513 B)   │ bits de datos │
│ 4 B  │  1 B   │     4 B      │ una por símbolo            │ …             │
└──────┴────────┴──────────────┴────────────────────────────┴───────────────┘
```

### 13.8 Resultados con el guion (16 721 bytes)

| método | bytes | % del original |
|---|---|---|
| RLE (nuestro) | 33 158 | 198.3 % |
| Huffman (nuestro) | 10 148 | 60.7 % |
| mini-DEFLATE (nuestro) | 8 167 | 48.8 % |
| zlib (DEFLATE real) | 6 776 | 40.5 % |
| bz2 (BWT) | 6 277 | 37.5 % |
| lzma / xz | 6 540 | 39.1 % |

- Límite de la entropía de orden 0: 4.695 bits/byte × 16 721 / 8 = **9 812 bytes**.
- Huffman queda en 10 148 = 9 812 + 265 de cabecera + redondeo a bits enteros: **no puede bajar
  del límite**.
- mini-DEFLATE baja a 8 167: **sí lo cruza**, porque LZ77 aprovecha palabras repetidas (contexto).
- Los profesionales ganan con búsquedas más inteligentes, Huffman también para las distancias,
  bloques y (lzma) codificación aritmética con contexto.

### 13.9 Usarlo desde la terminal

```bash
python -m compresion.archivo comprimir   ejemplos/guion.txt guion.edd deflate
python -m compresion.archivo descomprimir guion.edd recuperado.txt
python -m compresion.archivo comparar    ejemplos/guion.txt
```

---

## Parte 14 · Las pruebas automáticas

Archivo `tests/test_compresion.py`. Se ejecutan con:

```bash
python -m unittest discover -s tests -v
```

| Clase de prueba | Qué verifica |
|---|---|
| `TestEntropia` | Moneda justa = 1, cargada ≈ 0.469; `"AAAA"` = 0 |
| `TestRLE` | `AAAAABBBCC` → (5,A)(3,B)(2,C); la trampa `ABC` → `1A1B1C`; bytes con rachas > 255 |
| `TestHeap` | Insertar 500 números al azar y extraerlos sale **ordenado** |
| `TestHuffman` | ABRACADABRA = 23 bits; canónicos = los de la diapositiva; ida y vuelta con tabla y con árbol; un solo símbolo |
| `TestLZ` | LZ77 termina en `(R, 7, 4)`; 30 textos aleatorios vuelven idénticos; LZW con su caso especial |
| `TestBWT` | BANANA → `ANNB$AA` y vuelta; la frase con espacios (la del error que corregimos) |
| `TestAritmetica` | Ida y vuelta; usa menos bits que los símbolos (le gana a Huffman) |
| `TestAdaptativa` | Con contenido que cambia, el adaptativo gasta menos que el estático |
| `TestConPerdida` | DCT sin cuantizar no pierde; menos calidad = menos bits; el video se reconstruye |
| `TestArchivo` | Casos borde (vacío, 1 byte, los 256 bytes, repetitivo) y el guion, con ambos métodos |
| `TestAPI` | Todas las rutas de la interfaz responden |

La idea central de las pruebas sin pérdida es siempre la misma: **`decodificar(codificar(x)) == x`**.

---

## Parte 15 · Resumen de complejidades

| Operación | Tiempo | Memoria | Estructura clave |
|---|---|---|---|
| Contar frecuencias | O(n) | O(k) | tabla hash (`Counter`) |
| Entropía | O(n) | O(k) | tabla hash |
| RLE codificar / decodificar | O(n) | O(rachas) | — |
| Heap: ver mínimo | O(1) | — | arreglo |
| Heap: insertar / extraer | O(log n) | O(n) | árbol completo en arreglo |
| Huffman: construir árbol | O(k log k) | O(k) | min-heap + árbol binario |
| Huffman: generar códigos | O(k) | O(k) | DFS recursivo |
| Huffman: codificar / decodificar | O(n) | O(n) | tabla hash |
| Códigos canónicos | O(k log k) | O(k) | ordenamiento |
| LZ77 sin tabla hash | O(n · ventana) | O(n) | — |
| LZ77 con tabla hash | ≈ O(n) | O(n) | tabla hash trío → posiciones |
| LZ77 decodificar | O(n) | O(n) | — |
| LZW | ≈ O(n) | O(entradas) | tabla hash secuencia → código |
| BWT didáctica | O(n² log n) | O(n²) | ordenamiento |
| BWT inversa | O(n + k log k) | O(n) | tablas `rango` e `inicio` |
| Move-to-front | O(n · k) | O(k) | lista |
| DCT de un bloque | O(8⁴) constante | O(64) | — |
| FFT | O(n log n) | O(n) | divide y vencerás |
| Block matching por cuadro | O(bloques · 81 · 64) | O(píxeles) | — |

---

## Parte 16 · Glosario de Python usado

| En el código | Significa |
|---|---|
| `Counter(datos)` | Diccionario que cuenta apariciones |
| `{k: v for ...}` / `[x for ...]` | Comprensión de diccionario / lista |
| `a, b = b, a` | Intercambiar dos valores |
| `(1, -4) < (1, -3)` | Las tuplas se comparan elemento por elemento → `True` |
| `x[0::2]`, `x[1::2]` | Elementos en posiciones pares / impares |
| `t[i:] + t[:i]` | Rotar un texto |
| `lista[-64:]` | Los últimos 64 elementos |
| `reversed(lista)` | Recorrer al revés sin copiar |
| `d.setdefault(k, [])` | La lista de `k`, creándola vacía si no existe |
| `deque` / `popleft()` | Cola doble; sacar del frente en O(1) |
| `Fraction(3, 5)` | Fracción exacta |
| `x << n` / `x >> n` | Correr bits a la izquierda (×2ⁿ) / derecha (÷2ⁿ) |
| `x & 0xFF`, `x \| y` | Y / O de bits |
| `format(6, "03b")` | `"110"`: binario con 3 dígitos |
| `struct.pack("<BI", 1, 500)` | Bytes: 1 byte + entero de 4 bytes, *little-endian* |
| `__slots__` | Atributos fijos de una clase |
| `isinstance(x, dict)` | ¿x es un diccionario? |
| `max(..., default=-1)` | Máximo, o −1 si no hay elementos |
| `"".join(lista)` | Pegar textos de una lista |
| `bytearray` | Bytes que se pueden modificar |

---

## Parte 17 · Preguntas que nos pueden hacer

**¿Por qué implementaron el heap en vez de usar `heapq`?**
Para mostrar cómo funciona por dentro (es tema del curso). `heapq` hace lo mismo: nuestro
`_subir`/`_bajar` son sus `_siftdown`/`_siftup`.

**¿Por qué sus códigos Huffman no son los de la diapositiva?**
El árbol da códigos con **las mismas longitudes** (ambos dan 23 bits, ambos son óptimos). Los de la
diapositiva son los **canónicos**, que el código también calcula.

**¿Huffman es siempre óptimo?**
Entre los códigos que dan un número **entero** de bits a cada símbolo por separado, sí. La
aritmética le gana con fracciones de bit, y LZ77 mirando secuencias.

**¿Por qué el desempate `-orden`?**
Para que el resultado sea siempre el mismo y para que Python nunca tenga que comparar dos nodos.

**¿Por qué la coincidencia mínima de LZ77 es 3?**
Una referencia ocupa más que un literal; con 1 o 2 símbolos no se ahorra.

**¿Para qué la tabla hash en LZ77?**
Para saber en O(1) dónde apareció antes un trío; sin ella se compara contra toda la ventana
(171 vs. 14 comparaciones con «la compresion de la compresion»).

**¿Para qué el `$` en la BWT?**
Marca el final; sin él no se sabría en qué fila empezar a reconstruir.

**¿Dónde se pierde información en JPEG?**
Solo al **cuantizar** (dividir y redondear). La DCT y Huffman son reversibles.

**¿Se puede comprimir cualquier archivo? ¿Y dos veces?**
No. Lo ya comprimido o aleatorio casi no tiene redundancia. Ningún compresor sin pérdida puede
achicar **todos** los archivos (hay menos archivos cortos que largos: principio del palomar).

**¿La IA rompe el límite de Shannon?**
No. Usa un modelo que ve más contexto; con un mejor modelo, el límite es más bajo.

**¿Por qué Python y no C?**
Por claridad. Por eso nuestro mini-DEFLATE es más lento que zlib (escrito en C), aunque la idea es
la misma.

**¿Cómo saben que funciona?**
25 pruebas automáticas: verifican los números de las diapositivas y que todo lo sin pérdida vuelva
idéntico, incluso con datos aleatorios.
