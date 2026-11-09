# ¿Cómo cabe todo? — Compresión de datos (ejemplo práctico)

Ejemplo práctico de la exposición **«¿Cómo cabe todo? Compresión de datos: menos bits, la misma
información»** — Universidad del Norte, Estructuras de Datos II.
Sebastián Blanco · Santiago Lobo · Ángel Carrillo

Cada algoritmo de la presentación está implementado **desde cero en Python**, comentado en
español y con los **mismos ejemplos de las diapositivas**.

📄 **Explicación detallada de todo: [DOCUMENTO.md](DOCUMENTO.md)**

## Cómo ejecutarlo

Solo hace falta **Python 3.8+** (no se instala nada).

```bash
python demo.py              # menú interactivo
python demo.py todo         # todo, en el orden de la presentación
python demo.py huffman      # una sección
python -m unittest discover -s tests -v    # 22 pruebas automáticas
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
├── demo.py                 # menú: ejecuta las demostraciones en orden
├── DOCUMENTO.md            # explicación detallada de todo
├── compresion/             # un módulo por tema
│   ├── entropia.py   adaptativa.py   rle.py   estructuras.py   huffman.py
│   ├── lz77.py   lzw.py   bwt.py   aritmetica.py
│   ├── jpeg_dct.py   audio.py   video.py   imagen_bmp.py
│   └── archivo.py          # compresor de archivos real
├── ejemplos/guion.txt      # texto de prueba (el guion de la exposición)
├── tests/test_compresion.py
└── salidas/                # (se crea al ejecutar jpeg/audio) imágenes y sonidos
```
