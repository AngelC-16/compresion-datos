# ¿Cómo cabe todo? — Documento explicativo del ejemplo práctico

**Compresión de datos: menos bits, la misma información**
Universidad del Norte · Estructuras de Datos II
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

---

## Índice

0. [Para qué sirve este documento y cómo ejecutar el código](#0-para-qué-sirve-este-documento-y-cómo-ejecutar-el-código)
1. [Mapa del proyecto: qué archivo explica qué diapositiva](#1-mapa-del-proyecto)
2. [Contexto: la entropía de Shannon (el límite)](#2-contexto-la-entropía-de-shannon)
3. [Clasificación: con/sin pérdida y estática/adaptativa](#3-clasificación)
4. [RLE: contar repeticiones](#4-rle-run-length-encoding)
5. [Estructuras de datos: montículo (heap), árbol binario y tabla hash](#5-estructuras-de-datos)
6. [Huffman: corto para lo frecuente](#6-huffman)
7. [LZ77: «esto ya lo vi»](#7-lz77)
8. [LZW: un diccionario que se arma solo](#8-lzw)
9. [Burrows-Wheeler (BWT)](#9-burrows-wheeler-bwt)
10. [Codificación aritmética](#10-codificación-aritmética)
11. [Con pérdida — Imágenes: JPEG y la DCT](#11-con-pérdida--imágenes-jpeg)
12. [Con pérdida — Audio: enmascaramiento](#12-con-pérdida--audio)
13. [Con pérdida — Video: cuadros I/P y vectores de movimiento](#13-con-pérdida--video)
14. [Aplicación real: un compresor de archivos (mini-DEFLATE)](#14-aplicación-real-compresor-de-archivos)
15. [Pruebas automáticas](#15-pruebas-automáticas)
16. [Guion sugerido para presentar el ejemplo práctico](#16-guion-sugerido-para-presentar-el-ejemplo-práctico)
17. [El cuestionario, respondido con el código](#17-el-cuestionario-respondido-con-el-código)
18. [Simplificaciones honestas (qué hace distinto un compresor real)](#18-simplificaciones-honestas)

---

## 0. Para qué sirve este documento y cómo ejecutar el código

La presentación explica **qué** es la compresión y **qué** algoritmos existen. Este proyecto
muestra **cómo** funcionan por dentro: cada algoritmo de las diapositivas está programado
desde cero en Python, con comentarios en español, y cada demostración imprime paso a paso lo
que ocurre, usando **los mismos ejemplos de las diapositivas** (`AAAAABBBCC`, `ABRACADABRA`,
`BANANA`, la moneda cargada, el bloque 8×8 de JPEG, los cuadros I/P/B…).

**Requisitos:** solo Python 3.8 o superior. No hay que instalar ninguna librería (todo usa la
librería estándar).

```bash
git clone <url-del-repositorio>
cd compresion-datos
python demo.py              # menú interactivo
python demo.py todo         # todas las secciones, en el orden de la presentación
python demo.py huffman      # una sola sección
python -m unittest discover -s tests -v    # pruebas automáticas
```

Secciones disponibles: `entropia`, `adaptativa`, `rle`, `heap`, `huffman`, `lz77`, `lzw`,
`bwt`, `aritmetica`, `jpeg`, `audio`, `video`, `archivo`.

Las secciones `jpeg` y `audio` además **crean archivos** en la carpeta `salidas/`
(imágenes `.bmp` y sonidos `.wav`) para ver y escuchar el efecto de la compresión con pérdida.

> Todos los números que aparecen en este documento son la salida real del programa.

---

## 1. Mapa del proyecto

| Archivo | Tema | Diapositiva | Expositor |
|---|---|---|---|
| `compresion/entropia.py` | Entropía de Shannon, redundancia | 4 · «El límite: la entropía» | Sebastián |
| `compresion/adaptativa.py` | Modelo estático vs. adaptativo | 6 · «¿Cuándo aprende el modelo?» | Santiago |
| `compresion/rle.py` | Run-Length Encoding | 7 · «RLE: contar repeticiones» | Ángel |
| `compresion/estructuras.py` | Min-heap y nodo del árbol | 14 · «Qué hay debajo» | Santiago |
| `compresion/huffman.py` | Huffman (+ códigos canónicos) | 8 · «Huffman» | Ángel |
| `compresion/lz77.py` | LZ77 con ventana y tabla hash | 9 · «Lempel-Ziv» | Ángel |
| `compresion/lzw.py` | LZW con diccionario | 9 · «LZ78 / LZW» | Ángel |
| `compresion/bwt.py` | Burrows-Wheeler + move-to-front | 10 · «Más cerca del límite» | Ángel |
| `compresion/aritmetica.py` | Codificación aritmética | 10 · «Más cerca del límite» | Ángel |
| `compresion/jpeg_dct.py` | Bloques 8×8, DCT, cuantización | 11 · «Imágenes: JPEG» | Sebastián |
| `compresion/audio.py` | FFT y enmascaramiento | 12 · «Audio» | Sebastián |
| `compresion/video.py` | Cuadros I/P, vectores de movimiento | 13 · «Video» | Sebastián |
| `compresion/archivo.py` | Compresor real (Huffman y mini-DEFLATE) | 14-15 · «Está en todas partes» / «Ejemplo práctico» | Santiago |
| `compresion/imagen_bmp.py` | Utilidad: guardar imágenes .bmp | — | — |
| `demo.py` | Menú que ejecuta todo en orden | — | — |
| `tests/test_compresion.py` | 22 pruebas automáticas | — | — |
| `ejemplos/guion.txt` | Texto del guion (archivo de prueba) | — | — |

---

## 2. Contexto: la entropía de Shannon

**Archivo:** `compresion/entropia.py` · **Ejecutar:** `python demo.py entropia`

### 2.1 La idea

Comprimir es usar **menos bits para la misma información**. Pero no se puede encoger
infinitamente: Claude Shannon (1948) demostró que existe un mínimo, la **entropía**:

$$H = -\sum_x p(x)\,\log_2 p(x)$$

- $p(x)$ es la probabilidad de que aparezca el símbolo $x$ (su frecuencia relativa).
- $-\log_2 p(x)$ es la **información** o «sorpresa» de ver $x$, en bits. Lo muy probable
  sorprende poco y necesita pocos bits; lo raro sorprende mucho y necesita más.
- $H$ es el **promedio** de esa sorpresa: el mínimo número promedio de bits por símbolo
  para guardar el mensaje **sin perder nada**. Es la «naranja exprimida».

### 2.2 El ejemplo de la diapositiva, calculado

**Moneda justa** (50 % / 50 %):
$H = -(0{,}5\log_2 0{,}5 + 0{,}5\log_2 0{,}5) = -(0{,}5\cdot(-1) + 0{,}5\cdot(-1)) = 1$ bit.

**Moneda cargada** (90 % cara / 10 % sello):
$H = -(0{,}9\log_2 0{,}9 + 0{,}1\log_2 0{,}1) = -(0{,}9\cdot(-0{,}152) + 0{,}1\cdot(-3{,}322)) = 0{,}137 + 0{,}332 = 0{,}469 ≈ 0{,}47$ bits.

Salida del programa:

```
Moneda justa   (cara 50 %, sello 50 %):  H = 1.00 bit por lanzamiento
Moneda cargada (cara 90 %, sello 10 %):  H = 0.47 bits por lanzamiento
  -> ver 'cara' en la cargada aporta solo 0.152 bits (casi no sorprende)
  -> ver 'sello' en la cargada aporta 3.322 bits (sorprende mucho)
```

**Conclusión:** lo predecible se guarda con menos bits. Comprimir = aprovechar que los datos son
predecibles.

### 2.3 El código

```python
def entropia_de_distribucion(probs):
    h = -sum(p * math.log2(p) for p in valores if p > 0)   # la fórmula, tal cual
```

Para un texto, primero se cuentan las frecuencias con `Counter`, que por dentro es una
**tabla hash** (`dict`): cada conteo cuesta O(1) en promedio, así que contar todo el texto es O(n).
Luego `probabilidades()` divide cada conteo por el total, y se aplica la fórmula.

La función `analisis()` calcula además la **redundancia**: qué porcentaje de los bits
originales sobra.

```
Texto                          H (bits/símb)  8 bits/símb -> mínimo   redundancia
  'AAAAAAAAAAAAAAAA'             0.000         128 ->    0.0 bits     100.0 %
  'ABABABABABABABAB'             1.000         128 ->   16.0 bits      87.5 %
  'ABRACADABRA'                  2.040          88 ->   22.4 bits      74.5 %
  'súbete para arriba'           3.128         144 ->   56.3 bits      60.9 %
  'q7#Lz!0pW@k9&Xr2'             4.000         128 ->   64.0 bits      50.0 %
```

Cómo leerla: `ABRACADABRA` en ASCII ocupa 88 bits (11 letras × 8), pero su entropía dice que
bastarían ~22,4 bits. El texto aleatorio de 16 símbolos distintos tiene la entropía máxima
para 16 símbolos ($\log_2 16 = 4$): es el menos compresible.

### 2.4 Detalle importante: el modelo importa

`ABABABAB…` da $H = 1$ bit porque esta fórmula solo mira **cuántas veces** aparece cada letra
(modelo de «orden 0»). Pero un humano ve que es totalmente predecible: después de A siempre viene
B. Un modelo con **contexto** (que mira el símbolo anterior) detecta esa redundancia. Por eso
Lempel-Ziv, BWT y los modelos de IA logran comprimir más que la entropía de orden 0: **no rompen
el límite de Shannon, sino que usan un modelo mejor**, cuyo límite es más bajo (diapositiva 16,
punto 04).

---

## 3. Clasificación

### 3.1 Sin pérdida vs. con pérdida

| | Sin pérdida (lossless) | Con pérdida (lossy) |
|---|---|---|
| ¿Vuelve el original? | Sí, bit por bit | No, es irreversible |
| En este proyecto | `rle`, `huffman`, `lz77`, `lzw`, `bwt`, `aritmetica`, `archivo` | `jpeg_dct`, `audio` (y la idea de `video`) |
| Cómo se comprueba | Las pruebas verifican `decodificar(codificar(x)) == x` | Se mide el error: PSNR (imágenes), error RMS (audio) |

En la sección JPEG se ve el **trade-off** con números: a menor calidad, el archivo es más
pequeño, pero la imagen se parece menos (PSNR más bajo). Y se ve también la frase de la
diapositiva 5: «muchos formatos usan ambas»: JPEG **descarta** (cuantización, con pérdida) y
luego **comprime sin pérdida** (Huffman).

### 3.2 Estática vs. adaptativa

**Archivo:** `compresion/adaptativa.py` · **Ejecutar:** `python demo.py adaptativa`

- **Estática (dos pasadas):** lee todo → cuenta frecuencias → arma la tabla → codifica todo con
  la misma tabla → guarda tabla + datos. Ejemplo: Huffman clásico.
- **Adaptativa (una pasada):** lee un símbolo → lo codifica con la tabla **actual** → actualiza la
  tabla ↺. El decodificador hace exactamente las mismas actualizaciones, así que **no hace falta
  enviar la tabla**. Ejemplo: Lempel-Ziv.

Para compararlas de forma justa, el programa calcula el **costo ideal** de cada símbolo,
$-\log_2 p$, que es lo que gastaría un codificador perfecto (el aritmético se acerca mucho).

- `costo_estatico`: usa las probabilidades de **todo** el texto + 16 bits por cada entrada de la
  tabla que hay que enviar.
- `costo_adaptativo`: empieza con todos los conteos en 1 (para que nada tenga probabilidad 0) y
  después de codificar cada símbolo le suma 1 a su conteo. Opcionalmente recuerda solo los
  últimos `memoria` símbolos (ventana deslizante), para reaccionar rápido a cambios.

Resultado con un texto que **cambia a mitad de camino** (50 A y luego 50 B):

```
  Estática:   p(A)=p(B)=0.5 fijas -> 100.0 bits de datos + 32 bits de tabla = 132.0
  Adaptativa (recuerda todo):          103.0 bits, sin tabla
  Adaptativa (recuerda los últimos 8): 27.2 bits, sin tabla
```

Y cómo «aprende» el modelo símbolo a símbolo:

```
   posición  0  lee A  p(A)=0.500  -> cuesta 1.00 bits
   posición 10  lee A  p(A)=0.917  -> cuesta 0.13 bits
   posición 49  lee A  p(A)=0.980  -> cuesta 0.03 bits
   posición 50  lee B  p(B)=0.019  -> cuesta 5.70 bits   <- ¡sorpresa!
   posición 60  lee B  p(B)=0.177  -> cuesta 2.49 bits
   posición 99  lee B  p(B)=0.495  -> cuesta 1.01 bits
```

Esto es exactamente lo que dice el guion: «si una palabra se vuelve muy común a mitad del
documento, el sistema le asigna un código más corto de inmediato». La estática no puede: para
ella A y B valen siempre 1 bit.

> Ojo (diapositiva 6): «basada en contexto» es **otra** idea: predecir según lo que vino antes.
> Puede ser estática o adaptativa.

---

## 4. RLE (Run-Length Encoding)

**Archivo:** `compresion/rle.py` · **Ejecutar:** `python demo.py rle`

### 4.1 Algoritmo

Recorrer los datos; mientras el siguiente símbolo sea igual al actual, aumentar un contador; al
cambiar, guardar `(cantidad, símbolo)`.

```python
while i < n:
    simbolo = datos[i]
    cantidad = 1
    while i + cantidad < n and datos[i + cantidad] == simbolo:
        cantidad += 1
    rachas.append((cantidad, simbolo))
    i += cantidad
```

Aunque hay dos `while` anidados, cada posición se visita **una sola vez** (el índice `i` salta
`cantidad` posiciones), así que la complejidad es **O(n)**.

### 4.2 Resultados

```
Original:      AAAAABBBCC  (10 letras)
Rachas:        [(5, 'A'), (3, 'B'), (2, 'C')]
Compacto:      5A3B2C  (6 símbolos)
La trampa: ABC -> 1A1B1C  (3 -> 6 símbolos: ¡CRECIÓ!)
```

Con el ícono de 16×8 píxeles (bloques grandes de un color) el RLE deja el **31 %** del tamaño.
Pero en la sección 14 se ve que, aplicado a un texto normal (el guion), el archivo **casi se
duplica (198 %)**: es «la trampa» de la diapositiva en un caso real.

También hay una versión por **bytes** (`codificar_bytes`) que guarda cada racha en 2 bytes
`[cantidad, byte]`, partiendo las rachas de más de 255.

---

## 5. Estructuras de datos

**Archivo:** `compresion/estructuras.py` · **Ejecutar:** `python demo.py heap`

Esta es la conexión directa con el curso (diapositiva 14, «Qué hay debajo»).

### 5.1 Cola de prioridad = montículo binario mínimo (min-heap)

Es un árbol binario **completo** guardado en una lista. Para la posición `i`:

| | Fórmula |
|---|---|
| padre | `(i - 1) // 2` |
| hijo izquierdo | `2*i + 1` |
| hijo derecho | `2*i + 2` |

**Propiedad de heap:** todo padre es ≤ que sus hijos ⇒ el mínimo siempre está en la posición 0.

| Operación | Cómo | Costo |
|---|---|---|
| `ver_minimo` | leer `lista[0]` | O(1) |
| `insertar` | poner al final y **subir** (*sift-up*) mientras sea menor que el padre | O(log n) |
| `extraer_minimo` | sacar la raíz, poner el último en su lugar y **bajar** (*sift-down*) cambiando con el hijo menor | O(log n) |

¿Por qué O(log n)? Porque un árbol completo de n nodos tiene altura ⌊log₂ n⌋, y subir o bajar
recorre como mucho un camino de la raíz a una hoja.

Traza real del programa (fíjese en `insertar(1)`):

```
insertar(9) -> arreglo interno: [3, 7, 9]
insertar(1) -> arreglo interno: [1, 3, 9, 7]
```

El 1 entra en la posición 3. Su padre es la posición (3−1)//2 = 1, que tiene un 7 → se
intercambian → `[3, 1, 9, 7]`. Ahora su padre es la posición 0 (el 3) → se intercambian →
`[1, 3, 9, 7]`. Llegó a la raíz: es el nuevo mínimo. Dos intercambios = altura del árbol.

Al extraer en orden, salen `1, 2, 3, 4, 5, 7, 9`: **ordenados** (esto es *heapsort*).

Lo implementamos a mano en vez de usar `heapq` justamente para que se vea cómo funciona.

### 5.2 Árbol binario: `NodoHuffman`

- **Hoja:** tiene `simbolo` y `frecuencia`.
- **Nodo interno:** `simbolo = None`, `frecuencia` = suma de sus hijos, y punteros `izq`, `der`.
- Convención: **izquierda = 0, derecha = 1**. El código de un símbolo es el camino desde la raíz.

### 5.3 Tabla hash

En Python es el `dict`. Se usa en:
- `entropia.py` / `huffman.py`: contar frecuencias (`Counter`).
- `lz77.py`: trío de símbolos → posiciones donde apareció (sección 7).
- `lzw.py`: secuencia → código del diccionario (sección 8).
- `huffman.decodificar` y `archivo.py`: código → símbolo al descomprimir.

Buscar en una tabla hash cuesta **O(1) en promedio**; en una lista costaría O(n).

---

## 6. Huffman

**Archivo:** `compresion/huffman.py` · **Ejecutar:** `python demo.py huffman`

### 6.1 Algoritmo

1. Contar frecuencias (tabla hash, O(n)).
2. Meter una hoja por símbolo en la **cola de prioridad**.
3. Mientras haya más de un nodo: sacar los **dos de menor frecuencia**, crear un padre con la
   suma, y meter el padre de nuevo.
4. El último nodo es la raíz. Recorrerlo (DFS) da los códigos.

```python
while len(cola) > 1:
    f1, _, a = cola.extraer_minimo()     # el menor     -> rama izquierda (0)
    f2, _, b = cola.extraer_minimo()     # el siguiente -> rama derecha  (1)
    padre = NodoHuffman(f1 + f2, izq=a, der=b)
    cola.insertar((padre.frecuencia, -orden, padre))
```

En la cola se guardan tuplas `(frecuencia, -orden, nodo)`. Python compara tuplas elemento por
elemento, así que se ordena por frecuencia; `-orden` sirve de **desempate** (sale primero el
nodo creado más recientemente) y evita que Python intente comparar dos nodos.

**Complejidad:** con k símbolos distintos hay k−1 fusiones, cada una con operaciones O(log k)
⇒ construir el árbol es **O(k log k)**. Codificar el texto es O(n).

### 6.2 ABRACADABRA, paso a paso

Frecuencias: A=5, B=2, R=2, C=1, D=1.

```
  1. fusionar D(1) + C(1) -> nodo de 2
  2. fusionar [CD](2) + R(2) -> nodo de 4
  3. fusionar B(2) + [CDR](4) -> nodo de 6
  4. fusionar A(5) + [BCDR](6) -> nodo de 11

   (11)
   ├─0─ 'A' (5)
   └─1─ (6)
        ├─0─ 'B' (2)
        └─1─ (4)
             ├─0─ (2)
             │    ├─0─ 'D' (1)
             │    └─1─ 'C' (1)
             └─1─ 'R' (2)
```

Es el mismo árbol de la diapositiva 8 (11 → A(5) y 6; 6 → B(2) y 4; 4 → R(2) y 2; 2 → C y D).

### 6.3 Códigos canónicos (por qué coinciden con la diapositiva)

El árbol da `A=0, B=10, R=111, C=1101, D=1100`. La diapositiva muestra `R=110, C=1110, D=1111`.
**Ambos son óptimos**: lo que importa son las **longitudes** (A:1, B:2, R:3, C:4, D:4), que son
iguales. Cuando hay empates de frecuencia hay varios árboles óptimos posibles.

La diapositiva usa los **códigos canónicos**, que es lo que hacen DEFLATE (ZIP, PNG, gzip) y
JPEG. La regla (`codigos_canonicos`): ordenar por (longitud, símbolo) y asignar números binarios
consecutivos, corriendo un bit a la izquierda cada vez que aumenta la longitud:

| Símbolo | Longitud | Cálculo | Código |
|---|---|---|---|
| A | 1 | empieza en 0 | `0` |
| B | 2 | (0+1) << 1 = 2 | `10` |
| R | 3 | (2+1) << 1 = 6 | `110` |
| C | 4 | (6+1) << 1 = 14 | `1110` |
| D | 4 | 14+1 = 15 | `1111` |

**Ventaja:** para descomprimir no hay que guardar el árbol; basta guardar **una longitud por
símbolo**. Así lo hace nuestro compresor de archivos (sección 14).

### 6.4 El resultado

```
ASCII:   11 letras × 8 bits = 88 bits
Huffman: 23 bits -> 01011001110011110101100
¿Libre de prefijo? True
Entropía H = 2.040 bits/símbolo -> mínimo teórico 22.4 bits
Huffman    = 2.091 bits/símbolo -> 23 bits (muy cerca del límite)
```

Cuenta: 5·1 (A) + 2·2 (B) + 2·3 (R) + 1·4 (C) + 1·4 (D) = 5 + 4 + 6 + 4 + 4 = **23 bits**.

**Libre de prefijo:** ningún código es el comienzo de otro. Por eso al leer `0 10 110 0 1110 …`
nunca hay duda de dónde termina cada letra. `es_libre_de_prefijo()` lo verifica ordenando los
códigos: si uno es prefijo de otro, al ordenar quedan juntos.

**Decodificar** se hace de dos formas en el código:
- `decodificar_con_arbol`: bajar por el árbol (0 = izquierda, 1 = derecha) hasta una hoja,
  emitir el símbolo y volver a la raíz.
- `decodificar`: acumular bits y buscar en una tabla hash `código → símbolo`.

---

## 7. LZ77

**Archivo:** `compresion/lz77.py` · **Ejecutar:** `python demo.py lz77`

### 7.1 Idea

En vez de repetir una secuencia, se **apunta** a donde ya apareció. La salida es una lista de
tokens:
- `('L', símbolo)` — literal.
- `('R', distancia, longitud)` — «retrocede `distancia` y copia `longitud` símbolos».

```
Texto:  ABRACADABRA
Tokens: A B R A C A D (←7,4)
```

Exactamente el ejemplo de la diapositiva 9: **(retrocede 7, copia 4)**.

Parámetros (los mismos de DEFLATE): ventana de 32 KB, coincidencia mínima de 3, máxima de 258.

### 7.2 La tabla hash (por qué es rápido)

Sin tabla hash, para cada posición hay que comparar contra **toda la ventana**: O(ventana) por
posición. Con tabla hash guardamos cada **trío** de símbolos → lista de posiciones donde
apareció; así solo comparamos contra posiciones que **ya empiezan igual**.

```python
clave = datos[i:i + 3]
if clave in tabla:                     # O(1) promedio
    for pos in reversed(tabla[clave][-MAX_CANDIDATOS:]):
        ...                            # medir cuánto coincide
```

El programa cuenta las comparaciones con un texto repetitivo de 656 caracteres:

```
  fuerza bruta (toda la ventana):     8961
  con tabla hash (solo candidatos):    935  (10 veces menos)
```

Con archivos grandes la diferencia es de cientos o miles de veces. zlib hace lo mismo
(«hash chains»).

### 7.3 Copias que se solapan

```
'AAAAAAAAAAAAAAAAAAAA' -> A (←1,19)
```

«Retrocede 1 y copia 19» funciona porque se copia **símbolo a símbolo**: cada A copiada sirve de
fuente para la siguiente. Así LZ77 también hace el trabajo de RLE.

### 7.4 Decodificar

El decodificador **no necesita tabla hash**: solo copia desde lo que ya reconstruyó. Por eso
descomprimir un ZIP es mucho más rápido que comprimirlo.

LZ77 es **adaptativo**: la «tabla» (la ventana) se construye mientras se lee y el decodificador la
reconstruye solo.

---

## 8. LZW

**Archivo:** `compresion/lzw.py` · **Ejecutar:** `python demo.py lzw`

En vez de apuntar hacia atrás, LZW arma un **diccionario** de secuencias y emite el **número** de
cada entrada (como escribir «ONU» en vez de «Organización de las Naciones Unidas»).

```
w = ""
para cada símbolo c:
    si w+c está en el diccionario:  w = w+c                 (seguir alargando)
    si no:  emitir código(w); agregar w+c al diccionario; w = c
al final: emitir código(w)
```

Con `TOBEORNOTTOBEORTOBEORNOT` y diccionario inicial `{B:0, E:1, N:2, O:3, R:4, T:5}`:

```
  w (reconocido)  emite   nueva entrada
  T                  5     TO       = 6
  O                  3     OB       = 7
  ...
  TO                 6     TOB      = 15     <- ya reconoce secuencias de 2
  TOB               15     TOBE     = 18     <- y de 3
Códigos emitidos: [5, 3, 0, 1, 3, 4, 2, 3, 5, 6, 8, 10, 15, 9, 11, 13]
24 letras -> 16 códigos
```

A medida que avanza, las entradas son más largas y cada código reemplaza más letras. Con un texto
tan corto la ganancia en bits es pequeña (72 → 68), pero en archivos grandes es mucho mayor.

**Caso especial** (`ABABABA`): a veces el decodificador recibe un código que **aún no existe** en
su diccionario (el que está a punto de crear). En ese caso la entrada solo puede ser `w + w[0]`.
El código lo maneja en `decodificar`.

La pregunta «¿w+c ya está en el diccionario?» es una búsqueda en **tabla hash**, O(1). Uso real:
GIF, TIFF, `compress` de Unix.

---

## 9. Burrows-Wheeler (BWT)

**Archivo:** `compresion/bwt.py` · **Ejecutar:** `python demo.py bwt`

La BWT **no comprime**: **reordena** el texto para juntar letras iguales; después RLE / Huffman
comprimen mejor. Es la base de bzip2.

1. Escribir todas las rotaciones de `BANANA$`.
2. Ordenarlas.
3. Tomar la **última columna**.

```
   $BANANA  -> A
   A$BANAN  -> N
   ANA$BAN  -> N
   ANANA$B  -> B
   BANANA$  -> $
   NA$BANA  -> A
   NANA$BA  -> A
BWT(BANANA) = ANNB$AA
```

Igual que la diapositiva 10. Con una frase real:

```
Texto: 'tres tristes tigres tragaban trigo en un trigal'
BWT:   'ossnnsnlgrgba trraiiirrtrauaegtgtttteeeis  $    '
Rachas RLE antes de la BWT: 47   después de la BWT: 33
```

Aparecen rachas como `tttt`, `eee`, `iii`, `rr`.

**¿Por qué se puede deshacer?** (función `inversa`, en O(n log n)): la primera columna es la
última ordenada, y la k-ésima aparición de una letra en la última columna corresponde a su
k-ésima aparición en la primera (propiedad «LF»). Siguiendo esos saltos desde la fila que empieza
con `$` se reconstruye el texto de atrás hacia adelante.

> Detalle que encontramos al probar: la fila que empieza con `$` **no siempre es la primera**,
> porque el espacio (código 32) va antes que `$` (código 36). Por eso el código busca esa fila
> con `inicio['$']`. Una prueba automática con la frase de los tigres detectó el error.

**Move-to-front** (`mover_al_frente`): tras la BWT, las letras repetidas se convierten en muchos
ceros, ideales para Huffman.

---

## 10. Codificación aritmética

**Archivo:** `compresion/aritmetica.py` · **Ejecutar:** `python demo.py aritmetica`

Todo el mensaje se vuelve **un solo número** en [0, 1).

1. Dividir [0, 1) en tramos proporcionales a las probabilidades.
2. Por cada símbolo, hacer **zoom** dentro de su tramo y volver a dividirlo.
3. Elegir el número con menos bits dentro del intervalo final.

Mensaje `AABAC` (A = 3/5, B = 1/5, C = 1/5):

```
   A -> [0, 3/5)    B -> [3/5, 4/5)    C -> [4/5, 1)

   lee A -> [0       , 3/5     )  ancho = 3/5 ≈ 0.60000
   lee A -> [0       , 9/25    )  ancho = 9/25 ≈ 0.36000
   lee B -> [27/125  , 36/125  )  ancho = 9/125 ≈ 0.07200
   lee A -> [27/125  , 162/625 )  ancho = 27/625 ≈ 0.04320
   lee C -> [783/3125, 162/625 )  ancho = 27/3125 ≈ 0.00864

Número elegido: 0.0100001 (binario) = 33/128
Bits usados: 7
```

El ancho final es el **producto de las probabilidades** (3/5·3/5·1/5·3/5·1/5 = 27/3125), y los
bits necesarios son ≈ $-\log_2(\text{ancho}) = \sum -\log_2 p(x)$: **exactamente la entropía**
(aquí 5 × 1,371 = 6,86 ≈ 7 bits).

Se usan fracciones exactas (`Fraction`) para que no haya errores de redondeo; los codificadores
reales usan enteros de precisión fija y emiten bits sobre la marcha.

**Por qué supera a Huffman** (moneda cargada, 90 % A / 10 % B, 20 símbolos):

```
   límite de Shannon:  9.4 bits  (0.47 bits/símbolo)
   Huffman:            20 bits  (mínimo 1 bit por símbolo, ¡no puede bajar de ahí!)
   Aritmética:         8 bits  (usa fracciones de bit)
```

Huffman asigna un número **entero** de bits por símbolo (al menos 1). La aritmética usa
«fracciones de bit». (Que aquí salga 8 < 9,4 es suerte de alineación del intervalo; en promedio
se gasta la entropía más 1 o 2 bits, y además el decodificador debe conocer el modelo y la
longitud del mensaje.) Se usa en JPEG2000 y en H.264 (CABAC).

---

## 11. Con pérdida — Imágenes: JPEG

**Archivo:** `compresion/jpeg_dct.py` · **Ejecutar:** `python demo.py jpeg`

### 11.1 La tubería

| Paso | Qué hace | ¿Pierde? |
|---|---|---|
| Bloques 8×8 | Divide la imagen en cuadritos | No |
| DCT | Pasa cada bloque a frecuencias | **No** |
| Cuantización | Divide por una tabla y redondea | **Sí — aquí se pierde** |
| Zigzag + RLE + Huffman | Comprime lo que queda | No |

### 11.2 La DCT

$$F(u,v) = \tfrac14\,C(u)\,C(v)\sum_{x=0}^{7}\sum_{y=0}^{7} f(x,y)\cos\tfrac{(2x+1)u\pi}{16}\cos\tfrac{(2y+1)v\pi}{16},\quad C(0)=\tfrac{1}{\sqrt2},\ C(k>0)=1$$

Expresa el bloque como una suma de 64 «patrones» de coseno. $F(0,0)$ (el **DC**) es el promedio
del bloque; los demás (**AC**) son detalles cada vez más finos hacia abajo a la derecha. Antes se
resta 128 a cada píxel para centrar los valores en 0.

Bloque de ejemplo (degradado suave con un píxel distinto, el 142):

```
1) Bloque original                 2) Tras la DCT
    100  103  106  109 ...             29    -55     -2     -5 ...
    106  109  112  115 ...           -109     -0     -1      0 ...
    ...                                ...
   La DCT sola no pierde nada: DCT -> DCT inversa, error máximo = 2.8e-14
```

Casi toda la «energía» queda en 3 o 4 coeficientes de arriba a la izquierda (frecuencias bajas =
cambios suaves). El error 2.8e-14 es solo redondeo de la computadora: **la DCT es reversible**.

### 11.3 La cuantización (la pérdida)

Se divide cada coeficiente por el valor de la **tabla de cuantización estándar de JPEG** y se
redondea. La tabla tiene números chicos arriba a la izquierda (16, 11, 10…) y grandes abajo a la
derecha (…103, 99), porque el ojo casi no nota los detalles finos.

```
3) Tras cuantizar con la tabla estándar (calidad 50):
      2   -5    0    0    0    0    0    0
     -9    0    0    0    0    0    0    0
      0    0    0    0    0    0    0    0
     -1    0    0    0    0    0    0    0
      0    0    0 ...
   60 de 64 coeficientes quedaron en 0
```

Ejemplo: −55 / 11 = −5 → al reconstruir, −5 × 11 = −55 (casi igual). Pero un coeficiente −2 / 10 =
−0,2 → se redondea a **0**: esa información se pierde para siempre.

La calidad (1–100) escala la tabla como lo hace libjpeg (`tabla_calidad`): calidad baja ⇒
números más grandes ⇒ más ceros.

### 11.4 Zigzag y entropía

Se recorre el bloque en **zigzag** (de bajas a altas frecuencias) para que los ceros queden juntos
al final, y se generan símbolos como en JPEG: el DC (como diferencia con el bloque anterior),
pares `(ceros_antes, valor)` y `EOB` («el resto son ceros»):

```
[('DC', 2), (0, -5), (0, -9), (6, -1), 'EOB']
```

¡64 números se convirtieron en 5 símbolos! Esos símbolos se comprimen con **nuestro Huffman**.

### 11.5 Resultado y trade-off

El bloque reconstruido difiere del original en a lo sumo 10 niveles de gris (de 256). Con una
imagen sintética de 64×64 (degradado, un círculo y una zona de textura fina):

```
  calidad   bits (estim.)   % del original   coef. en 0     PSNR
     90         5272           16.1 %        3274/4096    42.6 dB
     50         2751            8.4 %        3631/4096    32.2 dB
     10         1099            3.4 %        3891/4096    24.5 dB
      2          491            1.5 %        4017/4096    22.0 dB
```

**PSNR** (*Peak Signal-to-Noise Ratio*) mide el parecido: $10\log_{10}(255^2/\text{ECM})$, donde
ECM es el error cuadrático medio. Más de ~35 dB es casi indistinguible; menos de ~25 dB ya se ven
bloques. Las imágenes quedan en `salidas/jpeg_*.bmp` (ampliadas ×4): a calidad 2 se ven
claramente los **bloques 8×8** y la textura fina desaparece.

---

## 12. Con pérdida — Audio

**Archivo:** `compresion/audio.py` · **Ejecutar:** `python demo.py audio`

### 12.1 Cuánto pesa el audio

```
  CD: 44 100 muestras/s × 16 bits × 2 canales = 1411 kbps
  MP3 a 128 kbps = 9.1 % del CD  (≈ 9 %, como dice la diapositiva)
```

### 12.2 La simulación

1. Una señal de prueba con 5 tonos: 1000 Hz **fuerte**, 1156 Hz débil (pegado al fuerte), 3000 Hz
   medio, 3094 Hz débil (pegado al de 3000) y 2000 Hz débil pero **lejos** de todos.
2. Se parte en tramas de 512 muestras (como MP3) y cada trama pasa a frecuencias con la **FFT**
   (Transformada Rápida de Fourier). La implementamos con el algoritmo de Cooley-Tukey, que es
   **divide y vencerás**: separa posiciones pares e impares, resuelve cada mitad y combina ⇒
   O(n log n) en vez del O(n²) de la definición directa.
3. **Modelo psicoacústico:** cada pico fuerte genera una curva de enmascaramiento: 20 dB por debajo
   del pico, y bajando 6 dB por cada 100 Hz de distancia. Todo lo que quede debajo de esa curva (o
   del umbral absoluto de audición, −60 dB) se borra.
4. Se vuelve al tiempo con la FFT inversa.

```
Espectro de una trama:
     1000 Hz    -4.4 dB  ███████████████████████████
     1156 Hz   -40.0 dB  █████████
     2000 Hz   -40.0 dB  ██████████
     3000 Hz   -12.0 dB  ███████████████████████
     3094 Hz   -46.0 dB  ██████

  Tonos borrados por enmascaramiento: [1156, 3094] Hz
  (el de 2000 Hz es igual de débil pero está LEJOS de los fuertes: se conserva)
  Componentes de frecuencia a guardar: 80 antes -> 48 después (40 % menos datos)
```

**El punto clave:** el tono de 1156 Hz y el de 2000 Hz tienen **el mismo volumen** (−40 dB), pero
uno se borra y el otro no. Lo que decide no es el volumen sino si un sonido fuerte **cercano** lo
tapa. Eso es el enmascaramiento.

Se generan `salidas/audio_original.wav` y `salidas/audio_comprimido.wav`: al escucharlos suenan
prácticamente igual (el error es 35 dB más bajo que la señal).

> Nota técnica: todas las frecuencias deben estar por debajo de la mitad de la frecuencia de
> muestreo (**límite de Nyquist**, aquí 4000 Hz). Una frecuencia mayor «se disfraza» de otra
> (*aliasing*). En una primera versión pusimos un tono de 6000 Hz y apareció como 2000 Hz.

---

## 13. Con pérdida — Video

**Archivo:** `compresion/video.py` · **Ejecutar:** `python demo.py video`

### 13.1 Idea

Dos cuadros seguidos casi siempre se parecen. Por eso:
- **I** (*intra*): imagen completa, la referencia.
- **P** (*predicted*): se predice desde un cuadro **anterior**.
- **B** (*bidirectional*): usa cuadros anteriores **y posteriores**.

### 13.2 Estimación de movimiento (*block matching*)

Para cada bloque 8×8 del cuadro actual se buscan todos los desplazamientos (dx, dy) entre −4 y +4
en el cuadro anterior y se elige el que minimiza la **SAD** (*Sum of Absolute Differences*, suma
de diferencias absolutas). Se guarda:
- el **vector de movimiento** (dx, dy), y
- el **residuo**: actual − predicción (casi todo ceros).

### 13.3 Resultado

Video de prueba: un cuadrado de 8×8 que se mueve 2 px a la derecha y 1 px hacia abajo por cuadro
sobre un fondo fijo con textura.

```
  cuadro 0: I  -> guarda la imagen completa: 1024 valores
  cuadro 1: P  -> 80 valores  | bloques que se movieron: {(8, 8): (-2, -1)}
  ...
  cuadro 5: P  -> 223 valores | bloques que se movieron: {(8, 8): (-2, -1), (16, 8): (-2, -1), ...}
Total: 6144 valores sin comprimir -> 1817 con predicción (29.6 %)
¿El decodificador reconstruye el video exacto? True
```

**Cómo leer el vector (−2, −1):** «el contenido de este bloque estaba 2 px a la izquierda y 1 px
arriba en el cuadro anterior», es decir, el objeto **se movió 2 px a la derecha y 1 px hacia
abajo**. Es la frase del guion: «el fondo sigue igual y este personaje solo se movió…». Los
bloques del fondo tienen vector (0, 0) y residuo 0: casi no cuestan nada.

A veces aparece un vector raro (p. ej. (0, 4)): es un bloque donde el cuadrado **acaba de salir** y
deja ver fondo que antes estaba tapado («fondo descubierto»); el codificador simplemente elige el
bloque más parecido que encuentre.

Aquí el residuo se guarda tal cual (sin pérdida); un códec real además lo pasa por DCT +
cuantización como JPEG, y ese es el paso con pérdida.

### 13.4 El ≈ 300×

```
1080p a 30 fps sin comprimir: 1920×1080 px × 24 bits × 30 = 1.49 Gbps
En streaming ≈ 5 Mbps  ->  299× menos datos
```

(El `.mp4` es solo el **contenedor**; el códec es H.264, AV1, etc.)

---

## 14. Aplicación real: compresor de archivos

**Archivo:** `compresion/archivo.py` · **Ejecutar:** `python demo.py archivo`

Este es el ejemplo práctico «completo»: un programa que comprime y descomprime **cualquier
archivo** con dos métodos implementados por nosotros, y los compara con los profesionales que
trae Python.

### 14.1 Uso desde la terminal

```bash
python -m compresion.archivo comprimir   ejemplos/guion.txt guion.edd deflate
python -m compresion.archivo descomprimir guion.edd guion_recuperado.txt
python -m compresion.archivo comparar    ejemplos/guion.txt
```

### 14.2 Los dos métodos

- **`huffman`:** Huffman canónico sobre los bytes del archivo (alfabeto de 256 símbolos).
- **`deflate` (mini-DEFLATE):** primero LZ77 (sección 7) y luego Huffman canónico sobre los
  tokens. Es la misma idea que ZIP, gzip y PNG: **LZ77 + Huffman = DEFLATE**. El alfabeto tiene
  513 símbolos:
  - 0–255: un byte literal;
  - 256–511: una referencia de longitud `símbolo − 256 + 3` (3 a 258); la distancia se escribe
    después con 15 bits fijos (1 a 32 768).

### 14.3 Formato del archivo `.edd`

| Bytes | Contenido |
|---|---|
| 4 | Firma `EDD2` («número mágico», para reconocer el formato) |
| 1 | Método (1 = huffman, 2 = deflate) |
| 4 | Tamaño original |
| 256 ó 513 | **Longitud del código** de cada símbolo (gracias a los códigos canónicos no hace falta guardar el árbol) |
| resto | Los bits de datos empaquetados en bytes |

### 14.4 Escribir bits

Los archivos se guardan en bytes, pero Huffman produce códigos de longitud variable. La clase
`EscritorBits` acumula bits en un entero y, cada vez que junta 8, escribe un byte; al final
rellena con ceros. `LectorBits` hace lo contrario. Para decodificar se arma una tabla hash
`(longitud, código) → símbolo` y se lee bit a bit hasta encontrar una coincidencia (como los
códigos son libres de prefijo, la primera coincidencia es la correcta).

### 14.5 Resultados con el guion de la exposición (16 721 bytes)

```
Entropía (orden 0): 4.695 bits/byte -> límite para un compresor que solo mira frecuencias de bytes: 9812 bytes

  método                                  bytes   % orig.    tiempo  ¿idéntico?
  RLE por bytes (nuestro)                 33158    198.3%    0.008s  sí
  Huffman (nuestro)                       10148     60.7%    0.007s  sí
  mini-DEFLATE LZ77+Huffman (nuestro)       8167     48.8%    0.059s  sí
  zlib nivel 9 (DEFLATE real)              6776     40.5%    0.001s  sí
  bz2 (BWT + Huffman)                      6277     37.5%    0.003s  sí
  lzma / xz (LZ77 + aritmética)            6540     39.1%    0.042s  sí
```

(Los tiempos cambian según el computador.)

**Lectura:**
1. **RLE agranda el texto** (198 %): no hay rachas. Es «la trampa».
2. **Huffman** queda en 10 148 bytes, muy cerca de su límite teórico de 9 812 (la diferencia es la
   cabecera de 265 bytes y el redondeo a bits enteros). **No puede bajar de la entropía de
   orden 0.**
3. **LZ77 + Huffman sí baja de ese límite** (8 167 < 9 812), porque aprovecha palabras y frases
   repetidas («compresión», «de datos», «Sebastián Blanco:»…): usa un modelo con contexto
   (sección 2.4).
4. Los profesionales comprimen un poco más gracias a búsquedas más inteligentes, códigos
   Huffman también para las distancias, bloques, y (lzma) codificación aritmética con contexto.
   **bz2**, basado en la BWT, es el mejor con este texto.
5. Todos responden **«sí»**: son sin pérdida, el archivo vuelve idéntico bit por bit.

---

## 15. Pruebas automáticas

**Archivo:** `tests/test_compresion.py` · **Ejecutar:** `python -m unittest discover -s tests -v`

22 pruebas que verifican, entre otras cosas:
- Las cifras de las diapositivas: H(moneda justa) = 1, H(cargada) ≈ 0,469; `AAAAABBBCC` →
  `(5,A)(3,B)(2,C)`; `ABC` → `1A1B1C`; ABRACADABRA en 23 bits y con los códigos canónicos de la
  diapositiva; LZ77 termina en `(←7,4)`; BWT(BANANA) = `ANNB$AA`.
- Que **todos** los algoritmos sin pérdida devuelven exactamente el original (incluidos casos
  borde: archivo vacío, un solo byte, todos los bytes 0–255, y datos aleatorios).
- Que el heap extrae en orden.
- Que la DCT sin cuantizar no pierde nada y que menos calidad JPEG da menos bits.
- Que la aritmética usa menos bits que Huffman en la moneda cargada.
- Que el modelo adaptativo gana cuando el contenido cambia.

---

## 16. Guion sugerido para presentar el ejemplo práctico

La diapositiva 15 («Ejemplo práctico») va justo después de «Qué hay debajo». Propuesta de
**5–7 minutos** con la terminal abierta (fuente grande):

1. **Huffman y sus estructuras** — `python demo.py huffman`
   *«Aquí está la cola de prioridad funcionando: en cada paso saca los dos menores — eso cuesta
   O(log n) gracias al heap. Fusionando así sale el árbol de la diapositiva. De 88 bits pasamos a
   23, y la entropía dice que el mínimo era 22,4: Huffman casi llega al límite.»*
2. **LZ77 y la tabla hash** — `python demo.py lz77`
   *«Este es el (retrocede 7, copia 4) de la diapositiva. Y miren esta comparación: buscando con
   tabla hash hacemos 10 veces menos comparaciones que buscando en toda la ventana.»*
3. **El compresor real** — `python demo.py archivo`
   *«Comprimimos el guion de esta misma exposición. RLE lo duplica: la trampa. Huffman lo deja en
   61 %. Nuestro mini-DEFLATE, que es LZ77 + Huffman como el ZIP, en 49 %. Y zlib, el de verdad,
   en 40 %. Todos recuperan el archivo idéntico: sin pérdida.»*
4. *(Opcional, si hay tiempo)* **Con pérdida** — `python demo.py jpeg` y mostrar las imágenes de
   `salidas/` a calidad 90 y 2. *«Aquí sí se pierde: miren los bloques 8×8.»*

Si algo falla en vivo, toda la salida está copiada en este documento.

---

## 17. El cuestionario, respondido con el código

1. **¿Qué es la entropía?** El límite teórico de compresión sin pérdida → `entropia.py`
   (respuesta b).
2. **Software financiero → sin pérdida** → todos los métodos de `archivo.py` responden «sí,
   idéntico»; un JPEG nunca lo haría (respuesta b).
3. **Huffman usa árboles binarios y colas de prioridad** → `estructuras.py` (`MinHeap`,
   `NodoHuffman`) y `huffman.construir_arbol` (respuesta c).
4. **Vectores de predicción en cuadros P/B** → `video.py`: se guardan desplazamientos (dx, dy)
   respecto al cuadro de referencia en vez de la imagen entera (respuesta b).
5. **Huffman vs. Lempel-Ziv** → `huffman.py` asigna códigos según la frecuencia de **símbolos
   sueltos**; `lz77.py`/`lzw.py` reemplazan **secuencias** repetidas con ventana deslizante o
   diccionario. Se ve en la sección 14: Huffman no baja de la entropía de orden 0 y LZ77+Huffman
   sí (respuesta b).

---

## 18. Simplificaciones honestas

Para que el código sea legible, hicimos algunas simplificaciones respecto a los formatos reales:

- **Huffman y LZW** trabajan con strings de `'0'`/`'1'` en las demos (es más claro). El compresor
  de archivos sí empaqueta bits reales.
- **Mini-DEFLATE** guarda las distancias con 15 bits fijos y una cabecera de 513 bytes sin
  comprimir; DEFLATE real codifica distancias con Huffman, comprime la propia cabecera y divide
  en bloques.
- **BWT** ordena las rotaciones directamente (O(n² log n)); bzip2 usa arreglos de sufijos (O(n)).
- **Codificación aritmética** usa fracciones exactas (lenta para mensajes largos); las reales usan
  enteros de precisión fija.
- **JPEG** trabaja en escala de grises y estima el tamaño con nuestro Huffman; el real convierte
  de RGB a YCbCr, submuestrea el color y usa tablas Huffman estándar.
- **Audio**: el modelo psicoacústico es una curva sencilla; MP3/AAC usan bandas críticas, MDCT y
  asignación de bits por banda.
- **Video**: solo cuadros I y P, búsqueda exhaustiva y residuo sin cuantizar; H.264/AV1 usan
  cuadros B, bloques de tamaño variable, búsquedas rápidas y DCT del residuo.

Ninguna de estas simplificaciones cambia **la idea** de cada algoritmo, que es lo que el
ejemplo busca mostrar.
