"""
3 · SIN PÉRDIDA — RLE (Run-Length Encoding, codificación por longitud de rachas)
================================================================================

Idea: en lugar de guardar cada símbolo, guardamos (cuántas veces seguidas, símbolo).

    AAAAABBBCC  ->  (5,A) (3,B) (2,C)        10 letras -> 6 símbolos

* Brilla en: datos con rachas largas (íconos, fax, imágenes BMP con bloques de color).
* La trampa: si no hay repeticiones, el archivo CRECE:  ABC -> 1A 1B 1C.

Complejidad: una sola pasada sobre los datos => O(n) en tiempo.
Es estático y sin pérdida: decodificar devuelve exactamente lo original.
"""


def codificar(datos):
    """Devuelve la lista de rachas [(cantidad, simbolo), ...]."""
    rachas = []
    i = 0
    n = len(datos)
    while i < n:
        simbolo = datos[i]
        cantidad = 1
        # Avanzamos mientras el siguiente símbolo sea igual al actual.
        while i + cantidad < n and datos[i + cantidad] == simbolo:
            cantidad += 1
        rachas.append((cantidad, simbolo))
        i += cantidad
    return rachas


def decodificar(rachas):
    """Operación inversa: expande cada (cantidad, simbolo)."""
    partes = [simbolo * cantidad for cantidad, simbolo in rachas]
    # Si los símbolos son caracteres, unimos en un string; si no, en una lista.
    if partes and isinstance(partes[0], str):
        return "".join(partes)
    resultado = []
    for cantidad, simbolo in rachas:
        resultado.extend([simbolo] * cantidad)
    return resultado


def a_texto(rachas):
    """Representación compacta tipo '5A3B2C' (solo para mostrar)."""
    return "".join("%d%s" % (cantidad, simbolo) for cantidad, simbolo in rachas)


def tamano_en_simbolos(rachas):
    """Cada racha ocupa 2 "casillas": la cantidad y el símbolo."""
    return 2 * len(rachas)


# ---------------------------------------------------------------------------
# Versión a nivel de BYTES (para archivos reales). Cada racha se guarda como
# 2 bytes: [cantidad (1..255), byte]. Las rachas de más de 255 se parten.
# ---------------------------------------------------------------------------
def codificar_bytes(datos: bytes) -> bytes:
    salida = bytearray()
    i = 0
    while i < len(datos):
        b = datos[i]
        cantidad = 1
        while i + cantidad < len(datos) and datos[i + cantidad] == b and cantidad < 255:
            cantidad += 1
        salida += bytes([cantidad, b])
        i += cantidad
    return bytes(salida)


def decodificar_bytes(datos: bytes) -> bytes:
    salida = bytearray()
    for i in range(0, len(datos), 2):
        salida += bytes([datos[i + 1]]) * datos[i]
    return bytes(salida)


def demo():
    print("=" * 70)
    print("3 · SIN PÉRDIDA — RLE: contar repeticiones")
    print("=" * 70)

    texto = "AAAAABBBCC"
    r = codificar(texto)
    print("\nOriginal:      %s  (%d letras)" % (texto, len(texto)))
    print("Rachas:        %s" % r)
    print("Compacto:      %s  (%d símbolos)" % (a_texto(r), tamano_en_simbolos(r)))
    print("Decodificado:  %s  ¿igual al original? %s" % (decodificar(r), decodificar(r) == texto))

    trampa = "ABC"
    r2 = codificar(trampa)
    print("\nLa trampa: %s -> %s  (%d -> %d símbolos: ¡CRECIÓ!)"
          % (trampa, a_texto(r2), len(trampa), tamano_en_simbolos(r2)))

    # Un "ícono" en blanco y negro de 16x8 píxeles: RLE es ideal aquí.
    icono = [
        "................",
        "......####......",
        "....########....",
        "...##########...",
        "...##########...",
        "....########....",
        "......####......",
        "................",
    ]
    print("\nÍcono de 16x8 píxeles (cada fila se codifica con RLE):")
    total_original = total_rle = 0
    for fila in icono:
        rf = codificar(fila)
        total_original += len(fila)
        total_rle += tamano_en_simbolos(rf)
        print("  %s  ->  %s" % (fila, a_texto(rf)))
    print("Píxeles originales: %d   símbolos con RLE: %d   (%.0f %% del tamaño)"
          % (total_original, total_rle, 100 * total_rle / total_original))


if __name__ == "__main__":
    demo()
