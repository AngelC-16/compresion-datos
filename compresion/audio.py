"""
4 · CON PÉRDIDA — Audio: lo que no se oye, se borra (MP3 · AAC · Opus)
=======================================================================

Modelo PSICOACÚSTICO = reglas basadas en cómo funciona el oído humano:

  * Umbral de audición: sonidos por debajo de cierto volumen no se oyen.
  * ENMASCARAMIENTO: un sonido fuerte «tapa» a los más débiles de frecuencias
    cercanas. El códec los elimina: de todos modos no los oiríamos.

Simulación (versión muy simplificada de lo que hace un códec real):
  1. Partimos el audio en tramas (como MP3) y pasamos cada trama a
     FRECUENCIAS con la FFT (Transformada Rápida de Fourier, O(n log n)).
  2. Por cada pico fuerte calculamos una "curva de enmascaramiento": cerca
     del pico el umbral es alto y va bajando a medida que nos alejamos.
  3. Todo componente por debajo del umbral se pone en CERO (se borra).
  4. Volvemos al dominio del tiempo con la FFT inversa.

Cuántos coeficientes sobreviven ≈ cuántos datos hay que guardar.

Dato de la diapositiva: un MP3 a 128 kbps pesa ≈ 9 % del audio de un CD
(44 100 muestras/s × 16 bits × 2 canales = 1411 kbps).
"""

import cmath
import math
import os
import struct
import wave

FS = 8000            # muestras por segundo (frecuencia de muestreo)
TRAMA = 512          # muestras por trama (potencia de 2 para la FFT)


def fft(x):
    """FFT recursiva de Cooley-Tukey (divide y vencerás): O(n log n).
    `x` debe tener longitud potencia de 2."""
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


def ifft(X):
    """Inversa: conjugar, aplicar FFT, conjugar y dividir entre n."""
    n = len(X)
    return [v.conjugate() / n for v in fft([v.conjugate() for v in X])]


def db(magnitud):
    return 20 * math.log10(magnitud) if magnitud > 1e-12 else -240.0


def senal_de_prueba(segundos=1.0):
    """Mezcla de tonos (frecuencias elegidas para caer justo en un 'bin' de la FFT):
       - 1000 Hz FUERTE   (amplitud 0.60)
       - 1156 Hz débil    (0.010) -> cerca del fuerte: quedará ENMASCARADO
       - 3000 Hz medio    (0.25)
       - 3094 Hz débil    (0.005) -> cerca del de 3000 Hz: ENMASCARADO
       - 2000 Hz débil    (0.010) -> lejos de todo: SE OYE, se conserva
    Todas deben ser menores que FS/2 = 4000 Hz (límite de Nyquist): una
    frecuencia mayor no se puede representar y "se disfraza" de otra (aliasing).
    """
    tonos = [(1000.0, 0.60), (1156.25, 0.010), (3000.0, 0.25),
             (3093.75, 0.005), (2000.0, 0.010)]
    n = int(FS * segundos)
    return [sum(a * math.sin(2 * math.pi * f * t / FS) for f, a in tonos) for t in range(n)]


def comprimir_trama(trama, caida_db_por_100hz=6.0, margen_db=20.0, umbral_absoluto_db=-60.0):
    """Aplica el modelo psicoacústico a una trama. Devuelve (trama_reconstruida,
    componentes_conservados, componentes_audibles_antes, lista_de_borrados_en_Hz).
    'Audibles antes' = componentes por encima del umbral absoluto de audición."""
    n = len(trama)
    X = fft(trama)
    mitad = n // 2
    resolucion = FS / n                                 # Hz por "bin"
    niveles = [db(abs(X[k]) / (n / 2)) for k in range(mitad + 1)]

    # Picos = máximos locales por encima del umbral absoluto.
    picos = [k for k in range(1, mitad) if niveles[k] > umbral_absoluto_db
             and niveles[k] >= niveles[k - 1] and niveles[k] >= niveles[k + 1]]

    conservados = 0
    borrados = []
    Y = [0j] * n
    for k in range(mitad + 1):
        umbral = umbral_absoluto_db
        for p in picos:
            if p == k:
                continue
            distancia_hz = abs(k - p) * resolucion
            # La curva de enmascaramiento: margen bajo el pico, y cae al alejarse.
            enmascara = niveles[p] - margen_db - caida_db_por_100hz * distancia_hz / 100
            umbral = max(umbral, enmascara)
        if niveles[k] > umbral:
            Y[k] = X[k]
            if k not in (0, mitad):
                Y[n - k] = X[n - k]                     # simetría de una señal real
            conservados += 1
        elif niveles[k] > -100 and k in picos:
            borrados.append(round(k * resolucion))
    reconstruida = [v.real for v in ifft(Y)]
    audibles = sum(1 for k in range(mitad + 1) if niveles[k] > umbral_absoluto_db)
    return reconstruida, conservados, audibles, borrados


def comprimir(senal):
    salida = []
    cons_total = tot_total = 0
    borrados = set()
    for i in range(0, len(senal) - TRAMA + 1, TRAMA):
        rec, c, t, b = comprimir_trama(senal[i:i + TRAMA])
        salida.extend(rec)
        cons_total += c
        tot_total += t
        borrados.update(b)
    return salida, cons_total, tot_total, sorted(borrados)


def guardar_wav(ruta, senal):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767))
                               for s in senal))


def demo(carpeta_salida=None):
    print("=" * 70)
    print("4 · CON PÉRDIDA — Audio: enmascaramiento psicoacústico")
    print("=" * 70)

    print("\nCuánto pesa el audio:")
    cd = 44100 * 16 * 2 / 1000
    print("  CD: 44 100 muestras/s × 16 bits × 2 canales = %.0f kbps" % cd)
    print("  MP3 a 128 kbps = %.1f %% del CD  (≈ 9 %%, como dice la diapositiva)" % (100 * 128 / cd))

    senal = senal_de_prueba(1.024)          # 1,024 s = 16 tramas de 512 muestras
    trama = senal[:TRAMA]
    X = fft(trama)
    res = FS / TRAMA
    print("\nEspectro de una trama (solo componentes con energía apreciable):")
    for k in range(TRAMA // 2):
        nivel = db(abs(X[k]) / (TRAMA / 2))
        if nivel > -60:
            print("   %6.0f Hz  %6.1f dB  %s" % (k * res, nivel, "█" * max(1, int((nivel + 60) / 2))))

    rec, conservados, total, borrados = comprimir(senal)
    print("\nTras aplicar el modelo psicoacústico:")
    print("  Tonos borrados por enmascaramiento: %s Hz" % borrados)
    print("  (el de 2000 Hz es igual de débil pero está LEJOS de los fuertes: se conserva)")
    print("  Componentes de frecuencia a guardar: %d antes -> %d después (%.0f %% menos datos)"
          % (total, conservados, 100 * (1 - conservados / total)))
    print("  (un códec real además asigna menos bits a cada componente según qué")
    print("   tan audible es; aquí solo mostramos la parte de 'borrar lo que no se oye')")
    err = math.sqrt(sum((a - b) ** 2 for a, b in zip(senal, rec)) / len(rec))
    energia = math.sqrt(sum(a * a for a in senal[:len(rec)]) / len(rec))
    print("  Error (RMS) respecto al original: %.4f  (= %.1f dB por debajo de la señal)"
          % (err, 20 * math.log10(energia / err)))

    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
        guardar_wav(os.path.join(carpeta_salida, "audio_original.wav"), senal)
        guardar_wav(os.path.join(carpeta_salida, "audio_comprimido.wav"), rec)
        print("  WAV guardados en '%s': escúchelos, suenan prácticamente igual." % carpeta_salida)


if __name__ == "__main__":
    demo("salidas")
