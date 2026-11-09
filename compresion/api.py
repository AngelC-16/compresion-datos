"""
API para la interfaz visual (web/).

Cada función recibe un diccionario con los parámetros que manda la página web,
ejecuta EL MISMO código de los módulos de compresión y devuelve un diccionario
(JSON) con todos los pasos intermedios, para que la página los dibuje y se
pueda VER lo que hace cada algoritmo.

Aquí no hay algoritmos nuevos: solo se llaman los de los otros módulos y se
"empaquetan" sus resultados.
"""

import base64
import math
from collections import Counter
from fractions import Fraction

from . import (adaptativa, archivo, aritmetica, audio, bwt, entropia, estructuras,
               huffman, jpeg_dct, lz77, lzw, rle, video)

MAX_TEXTO = 400


def _texto(p, defecto, limite=MAX_TEXTO):
    t = p.get("texto")
    if t is None or t == "":
        t = defecto
    return str(t)[:limite]


# ---------------------------------------------------------------------------
# 1 · Contexto
# ---------------------------------------------------------------------------
def api_entropia(p):
    texto = _texto(p, "ABRACADABRA")
    a = entropia.analisis(texto)
    freqs = Counter(texto)
    n = len(texto)
    simbolos = [{"s": s, "veces": v, "p": v / n, "info": -math.log2(v / n)}
                for s, v in sorted(freqs.items(), key=lambda x: (-x[1], x[0]))]
    pm = float(p.get("p", 0.9))
    return {**a, "texto": texto, "simbolos": simbolos,
            "moneda": {"p": pm, "H": entropia.entropia_de_distribucion([pm, 1 - pm])}}


# ---------------------------------------------------------------------------
# 2 · Clasificación
# ---------------------------------------------------------------------------
def api_adaptativa(p):
    texto = _texto(p, "A" * 50 + "B" * 50)
    memoria = int(p.get("memoria", 8)) or None
    alfabeto = sorted(set(texto))
    conteos = Counter(texto)
    n = len(texto)
    est = [-math.log2(conteos[s] / n) for s in texto]
    datos_e, tabla_e = adaptativa.costo_estatico(texto)
    det_todo, det_vent = [], []
    total_todo = adaptativa.costo_adaptativo(texto, alfabeto, detalle=det_todo)
    total_vent = adaptativa.costo_adaptativo(texto, alfabeto, memoria=memoria, detalle=det_vent)
    return {
        "texto": texto, "memoria": memoria,
        "estatico": {"costos": est, "datos": datos_e, "tabla": tabla_e, "total": datos_e + tabla_e},
        "adaptativo": {"costos": [d[3] for d in det_todo], "probs": [d[2] for d in det_todo],
                       "total": total_todo},
        "ventana": {"costos": [d[3] for d in det_vent], "probs": [d[2] for d in det_vent],
                    "total": total_vent},
    }


# ---------------------------------------------------------------------------
# 3 · Sin pérdida
# ---------------------------------------------------------------------------
def api_rle(p):
    if "filas" in p:
        filas = [str(f)[:64] for f in p["filas"][:32]]
        res = [{"fila": f, "rachas": rle.codificar(f)} for f in filas]
        orig = sum(len(f) for f in filas)
        cod = sum(rle.tamano_en_simbolos(r["rachas"]) for r in res)
        return {"filas": res, "original": orig, "codificado": cod}
    texto = _texto(p, "AAAAABBBCC")
    r = rle.codificar(texto)
    return {"texto": texto, "rachas": r, "compacto": rle.a_texto(r),
            "original": len(texto), "codificado": rle.tamano_en_simbolos(r),
            "ok": rle.decodificar(r) == texto}


def api_heap(p):
    """Ejecuta una operación sobre el heap y devuelve cada comparación e
    intercambio, para animarlos."""
    pasos = []

    def observar(accion, i, j, estado):
        pasos.append({"accion": accion, "i": i, "j": j, "arreglo": estado})

    h = estructuras.MinHeap(observador=observar)
    h._datos = [int(x) for x in p.get("arreglo", [])][:31]
    op = p.get("op", "insertar")
    resultado = None
    if op == "insertar":
        valor = int(p.get("valor", 0))
        h._datos.append(valor)
        pasos.append({"accion": "agregar", "i": len(h._datos) - 1, "j": None,
                      "arreglo": list(h._datos)})
        h._subir(len(h._datos) - 1)
    elif op == "extraer" and h._datos:
        resultado = h._datos[0]
        ultimo = h._datos.pop()
        if h._datos:
            h._datos[0] = ultimo
            pasos.append({"accion": "mover_ultimo", "i": 0, "j": None,
                          "arreglo": list(h._datos)})
            h._bajar(0)
        else:
            pasos.append({"accion": "mover_ultimo", "i": None, "j": None, "arreglo": []})
    pasos.append({"accion": "fin", "i": None, "j": None, "arreglo": list(h._datos)})
    return {"pasos": pasos, "arreglo": list(h._datos), "extraido": resultado}


def _arbol_a_dict(raiz):
    """Convierte el árbol en {nodos: {id: {...}}, raiz: id} para dibujarlo."""
    ids = {}
    nodos = {}

    def visitar(n):
        if n is None:
            return None
        if id(n) in ids:
            return ids[id(n)]
        nid = len(ids)
        ids[id(n)] = nid
        izq = visitar(n.izq)
        der = visitar(n.der)
        nodos[nid] = {"f": n.frecuencia, "s": n.simbolo, "izq": izq, "der": der}
        return nid

    return nodos, visitar(raiz), ids


def api_huffman(p):
    texto = _texto(p, "ABRACADABRA", 300)
    freqs = Counter(texto)
    fusiones = []
    raiz = huffman.construir_arbol(freqs, fusiones=fusiones)
    nodos, raiz_id, ids = _arbol_a_dict(raiz)

    # El "bosque" (contenido de la cola de prioridad) en cada paso.
    hojas = {}
    for nid, n in nodos.items():
        if n["s"] is not None:
            hojas[n["s"]] = nid
    bosque = [hojas[s] for s in freqs]
    pasos = [{"bosque": list(bosque), "fusion": None}]
    for a, b, padre in fusiones:
        ia, ib, ip = ids[id(a)], ids[id(b)], ids[id(padre)]
        bosque = [x for x in bosque if x not in (ia, ib)] + [ip]
        pasos.append({"bosque": list(bosque), "fusion": [ia, ib, ip]})
    if not fusiones:
        pasos.append({"bosque": [raiz_id], "fusion": None})

    codigos = huffman.generar_codigos(raiz)
    canon = huffman.codigos_canonicos({s: len(c) for s, c in codigos.items()})
    bits, _ = huffman.codificar(texto, canon)
    return {
        "texto": texto, "nodos": nodos, "raiz": raiz_id, "pasos": pasos,
        "tabla": [{"s": s, "veces": freqs[s], "arbol": codigos[s], "canonico": canon[s]}
                  for s in sorted(freqs, key=lambda x: (-freqs[x], x))],
        "segmentos": [{"s": s, "c": canon[s]} for s in texto],
        "bits": len(bits), "ascii": 8 * len(texto),
        "entropia": entropia.entropia(texto),
        "prefijo_ok": huffman.es_libre_de_prefijo(canon),
        "ok": "".join(huffman.decodificar(bits, canon)) == texto,
    }


def api_lz77(p):
    texto = _texto(p, "ABRACADABRA")
    ventana = max(1, min(lz77.VENTANA, int(p.get("ventana", 64))))
    traza = []
    e_hash, e_bruta = {}, {}
    tokens = lz77.codificar(texto, ventana=ventana, estadisticas=e_hash, traza=traza)
    lz77.codificar_fuerza_bruta(texto, ventana=ventana, estadisticas=e_bruta)
    salida = []
    pos = 0
    for t, paso in zip(tokens, traza):
        if t[0] == "L":
            salida.append({"tipo": "L", "i": pos, "s": t[1], "long": 1,
                           "clave": paso["clave"], "candidatos": paso["candidatos"]})
            pos += 1
        else:
            salida.append({"tipo": "R", "i": pos, "dist": t[1], "long": t[2],
                           "origen": pos - t[1], "clave": paso["clave"],
                           "candidatos": paso["candidatos"]})
            pos += t[2]
    return {"texto": texto, "ventana": ventana, "tokens": salida,
            "comparaciones_hash": e_hash["comparaciones"],
            "comparaciones_bruta": e_bruta["comparaciones"],
            "ok": lz77.decodificar(tokens) == texto}


def api_lzw(p):
    texto = _texto(p, "TOBEORNOTTOBEORTOBEORNOT")
    alfabeto = sorted(set(texto))
    codigos, dic, pasos = lzw.codificar(texto, alfabeto)
    ancho = max(1, math.ceil(math.log2(max(2, len(alfabeto)))))
    return {"texto": texto, "alfabeto": alfabeto, "codigos": codigos,
            "pasos": [{"w": w, "emite": c, "nueva": nv, "numero": num} for w, c, nv, num in pasos],
            "bits_fijos": len(texto) * ancho,
            "bits_lzw": lzw.bits_necesarios(codigos, len(alfabeto)),
            "ok": lzw.decodificar(codigos, alfabeto) == texto}


def api_bwt(p):
    texto = _texto(p, "BANANA", 60).replace(bwt.FIN, "")
    if not texto:
        texto = "BANANA"
    rot = bwt.rotaciones_ordenadas(texto)
    t = texto + bwt.FIN
    originales = [t[i:] + t[:i] for i in range(len(t))]
    salida = bwt.transformar(texto)
    return {"texto": texto, "rotaciones": originales, "ordenadas": rot, "salida": salida,
            "fila_original": rot.index(t),
            "mtf": bwt.mover_al_frente(salida),
            "rachas_antes": len(rle.codificar(texto)),
            "rachas_despues": len(rle.codificar(salida)),
            "ok": bwt.inversa(salida) == texto}


def _fr(x):
    return {"v": float(x), "t": str(x)}


def api_aritmetica(p):
    texto = _texto(p, "AABAC", 24)
    tramos = aritmetica.modelo(texto)
    traza = []
    bits, _ = aritmetica.codificar(texto, tramos, traza)
    pasos = []
    bajo, alto = Fraction(0), Fraction(1)
    for s, nb, na in traza:
        pasos.append({"s": s, "antes": [_fr(bajo), _fr(alto)], "despues": [_fr(nb), _fr(na)]})
        bajo, alto = nb, na
    x = Fraction(int(bits, 2), 2 ** len(bits))
    n = len(texto)
    huff_bits = len(huffman.codificar(texto)[0])
    return {"texto": texto,
            "tramos": [{"s": s, "ini": _fr(a), "fin": _fr(b)} for s, (a, b) in tramos.items()],
            "pasos": pasos, "bits": bits, "numero": _fr(x),
            "entropia_bits": entropia.entropia(texto) * n,
            "huffman_bits": max(huff_bits, n if len(set(texto)) > 1 else n),
            "ok": aritmetica.decodificar(bits, tramos, n) == texto}


# ---------------------------------------------------------------------------
# 4 · Con pérdida
# ---------------------------------------------------------------------------
BLOQUE_EJEMPLO = [[100 + 6 * x + 3 * y + (12 if (x, y) == (3, 4) else 0)
                   for y in range(8)] for x in range(8)]


def _r(M, d=1):
    return [[round(v, d) for v in fila] for fila in M]


def api_jpeg_bloque(p):
    bloque = p.get("bloque") or BLOQUE_EJEMPLO
    bloque = [[float(v) for v in fila[:8]] for fila in bloque[:8]]
    calidad = int(p.get("calidad", 50))
    Q = jpeg_dct.tabla_calidad(calidad)
    F = jpeg_dct.dct2([[v - 128 for v in fila] for fila in bloque])
    Fq = jpeg_dct.cuantizar(F, Q)
    rec = [[max(0, min(255, round(v + 128))) for v in fila]
           for fila in jpeg_dct.idct2(jpeg_dct.descuantizar(Fq, Q))]
    simbolos, _ = jpeg_dct.simbolos_entropia(Fq, 0)
    return {"original": _r(bloque, 0), "dct": _r(F), "tabla": Q, "cuantizado": Fq,
            "reconstruido": rec,
            "error": [[rec[i][j] - round(bloque[i][j]) for j in range(8)] for i in range(8)],
            "zigzag": jpeg_dct.ZIGZAG, "simbolos": [str(s) for s in simbolos],
            "ceros": sum(1 for f in Fq for c in f if c == 0), "calidad": calidad}


def api_jpeg_imagen(p):
    img = p.get("pixeles") or jpeg_dct.imagen_sintetica(64)
    alto = (min(len(img), 128) // 8) * 8
    ancho = (min(len(img[0]), 128) // 8) * 8
    img = [[float(v) for v in fila[:ancho]] for fila in img[:alto]]
    calidad = int(p.get("calidad", 50))
    rec, bits, ceros = jpeg_dct.comprimir_imagen(img, calidad)
    return {"ancho": ancho, "alto": alto, "original": _r(img, 0), "reconstruida": _r(rec, 0),
            "bits": bits, "bits_original": ancho * alto * 8, "ceros": ceros,
            "coeficientes": ancho * alto, "psnr": jpeg_dct.psnr(img, rec), "calidad": calidad}


def api_audio(p):
    margen = float(p.get("margen", 20))
    caida = float(p.get("caida", 6))
    res = audio.FS / audio.TRAMA
    f_debil = round(float(p.get("frecuencia", 1156.25)) / res) * res
    a_debil = 10 ** (float(p.get("nivel", -40)) / 20)
    tonos = [(1000.0, 0.60), (3000.0, 0.25), (3093.75, 0.005), (f_debil, a_debil)]
    senal = audio.senal_de_prueba(1.024, tonos)
    trama = senal[:audio.TRAMA]
    X = audio.fft(trama)
    mitad = audio.TRAMA // 2
    niveles = [audio.db(abs(X[k]) / (audio.TRAMA / 2)) for k in range(mitad + 1)]
    umbrales, picos = audio.curva_enmascaramiento(niveles, res, caida, margen)
    rec, conservados, audibles, borrados = audio.comprimir(senal, caida_db_por_100hz=caida,
                                                           margen_db=margen)
    err = math.sqrt(sum((a - b) ** 2 for a, b in zip(senal, rec)) / len(rec)) or 1e-12
    energia = math.sqrt(sum(a * a for a in senal) / len(senal))
    return {
        "resolucion": res, "frecuencias": [k * res for k in range(mitad + 1)],
        "niveles": [max(-100, round(v, 2)) for v in niveles],
        "umbrales": [round(v, 2) for v in umbrales], "picos": [k * res for k in picos],
        "tonos": [{"f": f, "db": round(audio.db(a), 1)} for f, a in tonos],
        "borrados": borrados, "conservados": conservados, "audibles": audibles,
        "snr": 20 * math.log10(energia / err), "debil": {"f": f_debil, "db": round(audio.db(a_debil), 1)},
        "muestras": [round(v, 4) for v in trama[:256]],
        "muestras_rec": [round(v, 4) for v in rec[:256]],
        "wav_original": base64.b64encode(audio.wav_en_bytes(senal)).decode(),
        "wav_comprimido": base64.b64encode(audio.wav_en_bytes(rec)).decode(),
    }


def api_video(p):
    dx = max(-3, min(3, int(p.get("dx", 2))))
    dy = max(-3, min(3, int(p.get("dy", 1))))
    cuadros = max(2, min(8, int(p.get("cuadros", 6))))
    ancho = alto = 48
    v = video.generar_video(cuadros, ancho, alto, dx, dy, inicio=(20 - 2 * dx, 20 - 2 * dy))
    flujo = video.codificar(v)
    salida = []
    referencia = v[0]
    for t, cuadro in enumerate(flujo):
        if cuadro[0] == "I":
            salida.append({"tipo": "I", "costo": video.costo(cuadro)})
        else:
            _, vect, residuo = cuadro
            pred = video.predecir(referencia, vect, ancho, alto)
            salida.append({"tipo": "P", "costo": video.costo(cuadro),
                           "vectores": [{"bx": bx, "by": by, "dx": a, "dy": b}
                                        for (bx, by), (a, b) in vect.items()],
                           "residuo": residuo, "prediccion": pred})
            referencia = v[t]
    return {"ancho": ancho, "alto": alto, "bloque": video.BLOQUE, "cuadros": v,
            "flujo": salida, "crudo": ancho * alto * len(v),
            "codificado": sum(c["costo"] for c in salida),
            "ok": video.decodificar(flujo) == v}


# ---------------------------------------------------------------------------
# 5 · Aplicaciones
# ---------------------------------------------------------------------------
MAX_ARCHIVO = 400 * 1024


def api_archivo(p):
    import os
    if p.get("datos"):
        datos = base64.b64decode(p["datos"])
        nombre = p.get("nombre", "archivo")
    else:
        ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ejemplos", "guion.txt")
        with open(ruta, "rb") as f:
            datos = f.read()
        nombre = "guion.txt"
    if len(datos) > MAX_ARCHIVO:
        raise ValueError("El archivo pesa %d KB; el máximo para esta demo es %d KB "
                         "(el código es Python puro y sería lento)."
                         % (len(datos) // 1024, MAX_ARCHIVO // 1024))
    h = entropia.entropia(datos) if datos else 0
    filas = [{"metodo": e, "bytes": b, "pct": pct, "segundos": t, "ok": ok, "propio": propio}
             for e, b, pct, t, ok, propio in archivo.medir(datos)]
    comprimido = archivo.comprimir(datos, "deflate")
    freqs = Counter(datos)
    longitudes = archivo._longitudes(freqs, 256)
    top = sorted(freqs.items(), key=lambda x: -x[1])[:16]
    return {"nombre": nombre, "tamano": len(datos), "entropia": h,
            "limite": int(len(datos) * h / 8), "filas": filas,
            "top": [{"byte": b, "car": chr(b) if 32 <= b < 127 else None, "veces": v,
                     "bits": longitudes[b]} for b, v in top],
            "edd": base64.b64encode(comprimido).decode()}


MODULOS_VISIBLES = {"entropia": entropia, "adaptativa": adaptativa, "rle": rle,
                    "estructuras": estructuras, "huffman": huffman, "lz77": lz77, "lzw": lzw,
                    "bwt": bwt, "aritmetica": aritmetica, "jpeg_dct": jpeg_dct,
                    "audio": audio, "video": video, "archivo": archivo}


def api_codigo(p):
    """Devuelve el código fuente REAL de una función, para mostrarlo en la página."""
    import inspect
    modulo = MODULOS_VISIBLES.get(p.get("modulo"))
    if modulo is None:
        raise ValueError("módulo desconocido")
    objeto = getattr(modulo, p.get("funcion", ""), None)
    if objeto is None or not (inspect.isfunction(objeto) or inspect.isclass(objeto)):
        raise ValueError("función desconocida")
    return {"codigo": inspect.getsource(objeto),
            "archivo": "compresion/%s.py" % p["modulo"]}


RUTAS = {
    "codigo": api_codigo,
    "entropia": api_entropia, "adaptativa": api_adaptativa, "rle": api_rle,
    "heap": api_heap, "huffman": api_huffman, "lz77": api_lz77, "lzw": api_lzw,
    "bwt": api_bwt, "aritmetica": api_aritmetica, "jpeg_bloque": api_jpeg_bloque,
    "jpeg_imagen": api_jpeg_imagen, "audio": api_audio, "video": api_video,
    "archivo": api_archivo,
}
