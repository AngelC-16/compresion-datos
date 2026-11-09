"""
Pruebas automáticas: verifican que cada algoritmo SIN pérdida devuelve
exactamente lo original y que los resultados coinciden con la presentación.

    python -m unittest discover -s tests -v
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compresion import (adaptativa, archivo, aritmetica, bwt, entropia, estructuras,
                        huffman, jpeg_dct, lz77, lzw, rle, video)


class TestEntropia(unittest.TestCase):
    def test_monedas_de_la_diapositiva(self):
        self.assertAlmostEqual(entropia.entropia_de_distribucion([0.5, 0.5]), 1.0)
        self.assertAlmostEqual(entropia.entropia_de_distribucion([0.9, 0.1]), 0.469, places=3)

    def test_texto_sin_variedad(self):
        self.assertEqual(entropia.entropia("AAAA"), 0.0)


class TestRLE(unittest.TestCase):
    def test_ejemplo_diapositiva(self):
        r = rle.codificar("AAAAABBBCC")
        self.assertEqual(r, [(5, "A"), (3, "B"), (2, "C")])
        self.assertEqual(rle.tamano_en_simbolos(r), 6)
        self.assertEqual(rle.decodificar(r), "AAAAABBBCC")

    def test_la_trampa(self):
        self.assertEqual(rle.a_texto(rle.codificar("ABC")), "1A1B1C")

    def test_bytes(self):
        datos = bytes([7] * 600 + [1, 2, 3])
        self.assertEqual(rle.decodificar_bytes(rle.codificar_bytes(datos)), datos)


class TestHeap(unittest.TestCase):
    def test_ordena(self):
        valores = [random.randint(0, 1000) for _ in range(500)]
        h = estructuras.MinHeap()
        for v in valores:
            h.insertar(v)
        self.assertEqual([h.extraer_minimo() for _ in valores], sorted(valores))


class TestHuffman(unittest.TestCase):
    def test_abracadabra_23_bits(self):
        bits, codigos = huffman.codificar("ABRACADABRA")
        self.assertEqual(len(bits), 23)
        self.assertTrue(huffman.es_libre_de_prefijo(codigos))

    def test_codigos_canonicos_como_la_diapositiva(self):
        raiz = huffman.construir_arbol({"A": 5, "B": 2, "R": 2, "C": 1, "D": 1})
        longitudes = {s: len(c) for s, c in huffman.generar_codigos(raiz).items()}
        self.assertEqual(huffman.codigos_canonicos(longitudes),
                         {"A": "0", "B": "10", "R": "110", "C": "1110", "D": "1111"})

    def test_ida_y_vuelta(self):
        texto = "la compresión de datos usa estructuras de datos"
        bits, codigos = huffman.codificar(texto)
        self.assertEqual("".join(huffman.decodificar(bits, codigos)), texto)
        raiz = huffman.construir_arbol(__import__("collections").Counter(texto))
        b2 = "".join(huffman.generar_codigos(raiz)[c] for c in texto)
        self.assertEqual("".join(huffman.decodificar_con_arbol(b2, raiz)), texto)

    def test_un_solo_simbolo(self):
        bits, codigos = huffman.codificar("AAAA")
        self.assertEqual(bits, "0000")


class TestLZ(unittest.TestCase):
    def test_lz77_diapositiva(self):
        tokens = lz77.codificar("ABRACADABRA")
        self.assertEqual(tokens[-1], ("R", 7, 4))
        self.assertEqual(lz77.decodificar(tokens), "ABRACADABRA")

    def test_lz77_aleatorio(self):
        rnd = random.Random(1)
        for _ in range(30):
            d = bytes(rnd.choice(b"ab") for _ in range(rnd.randint(0, 300)))
            self.assertEqual(lz77.decodificar(lz77.codificar(d), como_bytes=True), d)

    def test_lzw(self):
        for t in ["TOBEORNOTTOBEORTOBEORNOT", "ABABABA", "", "a"]:
            c, _, _ = lzw.codificar(t)
            self.assertEqual(lzw.decodificar(c), t)


class TestBWT(unittest.TestCase):
    def test_banana(self):
        self.assertEqual(bwt.transformar("BANANA"), "ANNB$AA")
        self.assertEqual(bwt.inversa("ANNB$AA"), "BANANA")

    def test_inversa(self):
        t = "tres tristes tigres tragaban trigo en un trigal"
        self.assertEqual(bwt.inversa(bwt.transformar(t)), t)


class TestAritmetica(unittest.TestCase):
    def test_ida_y_vuelta_y_mejor_que_huffman(self):
        texto = "AAAAAAAAABAAAAAAAAAB"
        bits, tramos = aritmetica.codificar(texto)
        self.assertEqual(aritmetica.decodificar(bits, tramos, len(texto)), texto)
        self.assertLess(len(bits), len(texto))       # Huffman necesitaría 20 bits


class TestAdaptativa(unittest.TestCase):
    def test_adaptativa_gana_si_el_contenido_cambia(self):
        texto = "A" * 50 + "B" * 50
        datos, tabla = adaptativa.costo_estatico(texto)
        self.assertLess(adaptativa.costo_adaptativo(texto, "AB", memoria=8), datos + tabla)


class TestConPerdida(unittest.TestCase):
    def test_dct_sin_cuantizar_no_pierde(self):
        bloque = [[(x * 8 + y) % 50 - 25 for y in range(8)] for x in range(8)]
        vuelta = jpeg_dct.idct2(jpeg_dct.dct2(bloque))
        for i in range(8):
            for j in range(8):
                self.assertAlmostEqual(vuelta[i][j], bloque[i][j], places=9)

    def test_menos_calidad_menos_bits(self):
        img = jpeg_dct.imagen_sintetica()
        _, bits_alta, _ = jpeg_dct.comprimir_imagen(img, 90)
        _, bits_baja, _ = jpeg_dct.comprimir_imagen(img, 10)
        self.assertLess(bits_baja, bits_alta)

    def test_video_reconstruye(self):
        v = video.generar_video(4)
        self.assertEqual(video.decodificar(video.codificar(v)), v)


class TestArchivo(unittest.TestCase):
    def _ida_y_vuelta(self, datos):
        for metodo in ("huffman", "deflate"):
            self.assertEqual(archivo.descomprimir(archivo.comprimir(datos, metodo)), datos)

    def test_casos_borde(self):
        for datos in [b"", b"a", b"aaaa", bytes(range(256)), b"ABRACADABRA" * 50]:
            self._ida_y_vuelta(datos)

    def test_guion(self):
        ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ejemplos", "guion.txt")
        with open(ruta, "rb") as f:
            datos = f.read()
        self._ida_y_vuelta(datos)
        self.assertLess(len(archivo.comprimir(datos, "deflate")), len(datos) * 0.7)


class TestAPI(unittest.TestCase):
    """La interfaz visual depende de que cada ruta responda sin errores."""

    def test_todas_las_rutas(self):
        import json
        from compresion.api import RUTAS
        for nombre, funcion in RUTAS.items():
            if nombre == "codigo":
                continue
            with self.subTest(ruta=nombre):
                json.dumps(funcion({}))           # debe poder enviarse como JSON

    def test_codigo_fuente(self):
        from compresion.api import api_codigo
        self.assertIn("def construir_arbol", api_codigo({"modulo": "huffman", "funcion": "construir_arbol"})["codigo"])

    def test_heap_animado(self):
        from compresion.api import api_heap
        d = api_heap({"arreglo": [1, 3, 9, 7], "op": "insertar", "valor": 0})
        self.assertEqual(d["arreglo"][0], 0)
        self.assertTrue(any(p["accion"] == "intercambiar" for p in d["pasos"]))


if __name__ == "__main__":
    unittest.main()
