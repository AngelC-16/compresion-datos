"""
4 · CON PÉRDIDA — Video: guardar solo lo que cambia (H.264 · AV1)
==================================================================

Un video es una secuencia rápida de imágenes (fotogramas). Dos fotogramas
seguidos casi siempre se parecen muchísimo: guardarlos completos sería tirar
espacio. Los códecs agrupan los cuadros así:

    I  B  B  P  B  B  P ...
    I = Imagen completa: la referencia (se comprime como un JPEG).
    P = Predice desde cuadros ANTERIORES.
    B = Usa cuadros anteriores Y posteriores.

Para un cuadro P, el codificador divide la imagen en BLOQUES (aquí 8×8) y,
para cada uno, busca en el cuadro de referencia el bloque más parecido
(«block matching»). Guarda:
    * el VECTOR DE MOVIMIENTO (dx, dy): «este bloque es el de allá, movido»
    * el RESIDUO: la pequeña diferencia que queda (casi todo ceros)
"El fondo sigue igual y este personaje solo se movió 2 píxeles a la derecha".

Dato de la diapositiva: 1080p a 30 fps sin comprimir ≈ 1,5 Gbps; en streaming
unos 5 Mbps  =>  ≈ 300× menos datos. (El .mp4 es solo el CONTENEDOR.)
"""

BLOQUE = 8
BUSQUEDA = 4         # se buscan desplazamientos de −4 a +4 píxeles


def fondo(ancho, alto):
    """Fondo fijo con textura pseudoaleatoria (siempre la misma, semilla 42),
    para que no sea trivial y para que ningún bloque "se parezca" por azar a otro."""
    import random
    rnd = random.Random(42)
    return [[rnd.randint(40, 90) for _ in range(ancho)] for _ in range(alto)]


def generar_video(cuadros=6, ancho=32, alto=32, dx=2, dy=1, inicio=(4, 6)):
    """Un cuadrado brillante de 8×8 que se mueve (dx, dy) píxeles por cuadro
    (por defecto 2 a la derecha y 1 hacia abajo), sobre un fondo fijo."""
    video = []
    for t in range(cuadros):
        img = fondo(ancho, alto)
        x0 = max(0, min(ancho - 8, inicio[0] + dx * t))
        y0 = max(0, min(alto - 8, inicio[1] + dy * t))
        for y in range(y0, y0 + 8):
            for x in range(x0, x0 + 8):
                img[y][x] = 230
        video.append(img)
    return video


def sad(ref, cur, bx, by, dx, dy):
    """Sum of Absolute Differences: qué tan distinto es el bloque (bx,by) del
    cuadro actual respecto al bloque desplazado (dx,dy) en la referencia."""
    total = 0
    for y in range(BLOQUE):
        for x in range(BLOQUE):
            total += abs(cur[by + y][bx + x] - ref[by + y + dy][bx + x + dx])
    return total


def estimar_movimiento(ref, cur):
    """Para cada bloque busca el desplazamiento con menor SAD (búsqueda completa
    en una ventana ±BUSQUEDA). Devuelve {(bx,by): (dx,dy)}."""
    alto, ancho = len(cur), len(cur[0])
    vectores = {}
    for by in range(0, alto, BLOQUE):
        for bx in range(0, ancho, BLOQUE):
            mejor = (sad(ref, cur, bx, by, 0, 0), 0, 0)       # preferimos (0,0) si empata
            for dy in range(-BUSQUEDA, BUSQUEDA + 1):
                for dx in range(-BUSQUEDA, BUSQUEDA + 1):
                    if 0 <= by + dy and by + dy + BLOQUE <= alto and \
                       0 <= bx + dx and bx + dx + BLOQUE <= ancho:
                        s = sad(ref, cur, bx, by, dx, dy)
                        if s < mejor[0]:
                            mejor = (s, dx, dy)
            vectores[(bx, by)] = (mejor[1], mejor[2])
    return vectores


def predecir(ref, vectores, ancho, alto):
    """Arma la predicción copiando bloques de la referencia según los vectores."""
    pred = [[0] * ancho for _ in range(alto)]
    for (bx, by), (dx, dy) in vectores.items():
        for y in range(BLOQUE):
            for x in range(BLOQUE):
                pred[by + y][bx + x] = ref[by + y + dy][bx + x + dx]
    return pred


def codificar(video):
    """Primer cuadro = I (completo). Los demás = P (vectores + residuo)."""
    alto, ancho = len(video[0]), len(video[0][0])
    flujo = [("I", [fila[:] for fila in video[0]])]
    referencia = video[0]
    for cur in video[1:]:
        vectores = estimar_movimiento(referencia, cur)
        pred = predecir(referencia, vectores, ancho, alto)
        residuo = [[cur[y][x] - pred[y][x] for x in range(ancho)] for y in range(alto)]
        flujo.append(("P", vectores, residuo))
        referencia = cur          # (sin pérdida aquí, la referencia es exacta)
    return flujo


def decodificar(flujo):
    video = []
    referencia = None
    for cuadro in flujo:
        if cuadro[0] == "I":
            img = [fila[:] for fila in cuadro[1]]
        else:
            _, vectores, residuo = cuadro
            alto, ancho = len(residuo), len(residuo[0])
            pred = predecir(referencia, vectores, ancho, alto)
            img = [[pred[y][x] + residuo[y][x] for x in range(ancho)] for y in range(alto)]
        video.append(img)
        referencia = img
    return video


def costo(cuadro):
    """Valores a guardar: un cuadro I guarda todos los píxeles; un P guarda
    2 números por vector + solo los valores del residuo distintos de 0."""
    if cuadro[0] == "I":
        return sum(len(f) for f in cuadro[1])
    _, vectores, residuo = cuadro
    return 2 * len(vectores) + sum(1 for f in residuo for v in f if v != 0)


def demo():
    print("=" * 70)
    print("4 · CON PÉRDIDA — Video: cuadros I y P con vectores de movimiento")
    print("=" * 70)

    sin_comprimir = 1920 * 1080 * 24 * 30
    print("\n1080p a 30 fps sin comprimir: 1920×1080 px × 24 bits × 30 = %.2f Gbps"
          % (sin_comprimir / 1e9))
    print("En streaming ≈ 5 Mbps  ->  %.0f× menos datos" % (sin_comprimir / 5e6))

    video = generar_video()
    flujo = codificar(video)
    print("\nVideo de prueba: %d cuadros de 32×32 (un cuadrado que se mueve)" % len(video))
    total_crudo = total_cod = 0
    for i, cuadro in enumerate(flujo):
        crudo = 32 * 32
        c = costo(cuadro)
        total_crudo += crudo
        total_cod += c
        if cuadro[0] == "I":
            print("  cuadro %d: I  -> guarda la imagen completa: %d valores" % (i, c))
        else:
            movidos = {k: v for k, v in cuadro[1].items() if v != (0, 0)}
            print("  cuadro %d: P  -> %d valores  | bloques que se movieron: %s"
                  % (i, c, movidos))
    print("Total: %d valores sin comprimir -> %d con predicción (%.1f %%)"
          % (total_crudo, total_cod, 100 * total_cod / total_crudo))
    print("¿El decodificador reconstruye el video exacto? %s" % (decodificar(flujo) == video))
    print("\nNota: aquí el residuo se guarda tal cual. Un códec real además lo pasa")
    print("por DCT + cuantización (como JPEG) — ese es el paso CON PÉRDIDA.")


if __name__ == "__main__":
    demo()
