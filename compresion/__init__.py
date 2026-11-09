"""
Paquete `compresion`: ejemplo práctico de la presentación
«¿Cómo cabe todo? Compresión de datos: menos bits, la misma información».

Cada módulo implementa, desde cero y solo con la librería estándar de Python,
un tema de la presentación:

    entropia.py      -> 1 · Contexto: entropía de Shannon y redundancia
    adaptativa.py    -> 2 · Clasificación: modelo estático vs. adaptativo
    rle.py           -> 3 · Sin pérdida: Run-Length Encoding
    estructuras.py   -> 5 · Estructuras: cola de prioridad (heap) y árbol binario
    huffman.py       -> 3 · Sin pérdida: codificación Huffman
    lz77.py          -> 3 · Sin pérdida: LZ77 con ventana deslizante + tabla hash
    lzw.py           -> 3 · Sin pérdida: LZW con diccionario (tabla hash)
    bwt.py           -> 3 · Sin pérdida: Transformada de Burrows-Wheeler
    aritmetica.py    -> 3 · Sin pérdida: codificación aritmética
    jpeg_dct.py      -> 4 · Con pérdida: imágenes (bloques 8x8, DCT, cuantización)
    audio.py         -> 4 · Con pérdida: audio (enmascaramiento psicoacústico)
    video.py         -> 4 · Con pérdida: video (cuadros I/P, vectores de movimiento)
    archivo.py       -> 5 · Aplicaciones: compresor real de archivos con Huffman
"""
