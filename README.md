# ¿Cómo cabe todo? — Compresión de datos (ejemplo práctico)

Ejemplo práctico de la exposición **«¿Cómo cabe todo? Compresión de datos: menos bits, la misma
información»** — Universidad del Norte, Estructuras de Datos II.
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

Cada algoritmo de la presentación está implementado **desde cero en Python**, comentado en
español y con los **mismos ejemplos de las diapositivas**.

📄 **Explicación detallada de todo: [DOCUMENTO.md](DOCUMENTO.md)**
🧠 **El código, función por función y línea por línea: [EXPLICACION_DEL_CODIGO.md](EXPLICACION_DEL_CODIGO.md)**

## Cómo ejecutarlo

Solo hace falta **Python 3.8+** (no se instala nada, no necesita internet).

### Interfaz visual (recomendada para presentar)

**1. Descargar el proyecto** (una sola vez): con `git clone https://github.com/AngelC-16/compresion-datos.git`
o, en GitHub, botón verde **Code → Download ZIP** y descomprimir.

**2. Abrir la interfaz**, de cualquiera de estas formas:

| Forma | Cómo |
|---|---|
| Doble clic (Windows) | Doble clic en **`abrir_interfaz.bat`** |
| VS Code | *File → Open Folder* → la carpeta **`compresion-datos`** (no una carpeta de más arriba) → **F5** → «Interfaz visual (app.py)». También sirve abrir `app.py` y darle ▶ |
| Terminal | Dentro de la carpeta: `python app.py` |

Se abre sola en el navegador en `http://127.0.0.1:8000` (si no, copie la dirección que aparece en
la terminal). **No cierre la terminal o ventana negra mientras la usa**; para cerrarla: `Ctrl + C`.

> ⚠ **No abra `web/index.html` con doble clic ni con la vista previa de VS Code / Live Server**:
> la página necesita el servidor de Python para calcular. Si lo hace, verá un aviso rojo con
> estas mismas instrucciones.

Cada tema tiene un **reproductor paso a paso**
(⏮ ◀ ▶ ⏭) que muestra lo que hace el algoritmo: el árbol de Huffman armándose con la cola de
prioridad, la ventana de LZ77 resaltando de dónde copia, el zoom de la codificación aritmética,
lo que le pasa a un bloque 8×8 de JPEG, el espectro de audio con la curva de enmascaramiento (y
se puede escuchar), los vectores de movimiento del video, y la comparación con ZIP/bz2/xz
arrastrando cualquier archivo. Al final de cada sección, «Ver el código Python» muestra la función
real que hace el cálculo. Para cerrarla: `Ctrl + C` en la terminal.

### En la consola

```bash
python demo.py              # menú interactivo
python demo.py todo         # todo, en el orden de la presentación
python demo.py huffman      # una sección
python -m unittest discover -s tests -v    # 25 pruebas automáticas
```

Comprimir un archivo propio:

```bash
python -m compresion.archivo comprimir    mi_archivo.txt mi_archivo.edd deflate
python -m compresion.archivo descomprimir mi_archivo.edd recuperado.txt
python -m compresion.archivo comparar     mi_archivo.txt
```

## Contenido

| Sección (`python demo.py …`) | Qué muestra | Diapositiva |
|---|---|---|
| `entropia` | Entropía de Shannon, moneda justa (1 bit) vs. cargada (0,47 bits) | 4 |
| `adaptativa` | Modelo estático (dos pasadas) vs. adaptativo (una pasada) | 6 |
| `rle` | `AAAAABBBCC → 5A3B2C` y la trampa `ABC → 1A1B1C` | 7 |
| `heap` | Cola de prioridad (min-heap) implementada a mano | 14 |
| `huffman` | Árbol de ABRACADABRA, 88 → 23 bits, códigos canónicos | 8 |
| `lz77` | Ventana deslizante + tabla hash, `(retrocede 7, copia 4)` | 9 |
| `lzw` | Diccionario que se construye mientras se lee | 9 |
| `bwt` | `BANANA → ANNB$AA` y su inversa | 10 |
| `aritmetica` | Un mensaje = un número; supera a Huffman | 10 |
| `jpeg` | Bloques 8×8 → DCT → cuantización → Huffman (+ imágenes .bmp) | 11 |
| `audio` | FFT y enmascaramiento psicoacústico (+ archivos .wav) | 12 |
| `video` | Cuadros I/P, vectores de movimiento, ≈ 300× | 13 |
| `archivo` | Compresor real (Huffman y mini-DEFLATE) vs. zlib, bz2 y lzma | 14–15 |

## Estructura

```
compresion-datos/
├── app.py                  # interfaz visual: servidor local + navegador
├── web/                    # la página (HTML, CSS y JS que solo DIBUJA)
├── demo.py                 # versión de consola: ejecuta las demostraciones en orden
├── DOCUMENTO.md            # explicación detallada de todo
├── compresion/             # un módulo por tema
│   ├── entropia.py   adaptativa.py   rle.py   estructuras.py   huffman.py
│   ├── lz77.py   lzw.py   bwt.py   aritmetica.py
│   ├── jpeg_dct.py   audio.py   video.py   imagen_bmp.py
│   ├── archivo.py          # compresor de archivos real
│   └── api.py              # empaqueta los pasos de cada algoritmo para la interfaz
├── ejemplos/guion.txt      # texto de prueba (el guion de la exposición)
├── tests/test_compresion.py
└── salidas/                # (se crea al ejecutar jpeg/audio) imágenes y sonidos
```
