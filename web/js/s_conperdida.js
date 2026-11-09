/* 4 · Con pérdida: imágenes, audio y video */

// ======================= JPEG =======================
SECCIONES.push({
  id: "jpeg", grupo: 3, titulo: "Imágenes: JPEG",
  bajada: "Bloques 8×8 → DCT (pasar a frecuencias) → cuantización (AQUÍ se pierde) → Huffman. Mueva la calidad, haga clic en cualquier bloque de la imagen para ver su recorrido, o cargue su propia foto.",
  codigo: [["jpeg_dct", "dct2"], ["jpeg_dct", "cuantizar"], ["jpeg_dct", "simbolos_entropia"], ["jpeg_dct", "comprimir_imagen"]],
  render(raiz) {
    let calidad = 50, pixeles = null, bloqueSel = null, ultimaImagen = null;
    const zonaImg = h("div"), zonaBloque = h("div");
    const extraerBloque = (bx, by) => ultimaImagen.original.slice(by * 8, by * 8 + 8).map((f) => f.slice(bx * 8, bx * 8 + 8));

    const cargarImagen = () => conCarga(zonaImg, async () => {
      const d = await api("jpeg_imagen", { pixeles, calidad });
      ultimaImagen = d;
      const escala = Math.max(2, Math.floor(320 / d.ancho));
      const clic = (x, y) => { bloqueSel = [Math.floor(x / 8), Math.floor(y / 8)]; cargarBloque(); };
      const marco = (titulo, canv) => h("div", {}, h("div", { clase: "nota" }, titulo), canv);
      vaciar(zonaImg,
        h("div", { clase: "fila", estilo: { alignItems: "flex-start", gap: "22px" } },
          marco("Original", lienzoGris(d.original, escala, { cuadricula: 8, alClic: clic })),
          marco(`Comprimida (calidad ${d.calidad})`, lienzoGris(d.reconstruida, escala, { cuadricula: 8, alClic: clic }))),
        h("div", { clase: "indicadores", estilo: { marginTop: "12px" } },
          indicador("Bits sin comprimir", ent(d.bits_original)),
          indicador("Bits estimados (Huffman)", ent(d.bits), "acento"),
          indicador("Tamaño", fmt(100 * d.bits / d.bits_original, 1) + " %", "ok"),
          indicador("Coeficientes en 0", fmt(100 * d.ceros / d.coeficientes, 0) + " %"),
          indicador("PSNR (parecido)", fmt(d.psnr, 1) + " dB", d.psnr > 35 ? "ok" : d.psnr < 26 ? "mal" : "")),
        h("p", { clase: "nota" }, "PSNR > 35 dB ≈ indistinguible · < 25 dB se ven los bloques. 👆 Haga clic en un bloque para ver qué le pasa."));
      if (!bloqueSel) cargarBloque(true);
      else cargarBloque();
    });

    const cargarBloque = (ejemplo = false) => conCarga(zonaBloque, async () => {
      const bloque = ejemplo || !bloqueSel ? null : extraerBloque(...bloqueSel);
      const d = await api("jpeg_bloque", { bloque, calidad });
      const titulo = bloque ? `Bloque (${bloqueSel[0]}, ${bloqueSel[1]}) de la imagen` : "Bloque de ejemplo (degradado con un píxel distinto)";
      const par = (a, ta, b, tb) => h("div", { clase: "fila", estilo: { alignItems: "flex-start", gap: "24px" } },
        h("div", { estilo: { flex: "1 1 280px" } }, h("div", { clase: "nota" }, ta), a),
        h("div", { estilo: { flex: "1 1 280px" } }, h("div", { clase: "nota" }, tb), b));
      const etapas = [
        { n: "1. Bloque 8×8", exp: "La imagen se divide en cuadritos de 8×8 píxeles (0 = negro, 255 = blanco). Cada bloque se procesa por separado.",
          v: () => par(matriz8(d.original, { grande: true }), "Píxeles del bloque", h("div", { clase: "nota", html: "A cada píxel se le resta 128 para centrar los valores en 0 antes de la DCT." }), "") },
        { n: "2. DCT", exp: "La DCT expresa el bloque como suma de 64 patrones de coseno. Arriba-izquierda = cambios suaves (frecuencias bajas); abajo-derecha = detalles finos. La energía se concentra en pocas casillas. ¡Todavía no se ha perdido nada!",
          v: () => par(matriz8(d.original), "Píxeles", matriz8(d.dct, { modo: "div" }), "Coeficientes DCT (naranja +, azul −)") },
        { n: "3. Tabla de cuantización", exp: `Tabla estándar de JPEG escalada a calidad ${d.calidad}. Números chicos arriba-izquierda (se conservan con precisión) y grandes abajo-derecha (el ojo casi no nota esos detalles).`,
          v: () => par(matriz8(d.dct, { modo: "div" }), "Coeficientes DCT", matriz8(d.tabla, { modo: "div", max: 255 }), "Tabla Q: se divide entre esto") },
        { n: "4. Cuantizar (pérdida)", perdida: true, exp: `Cada coeficiente se divide por la tabla y se REDONDEA. Aquí se pierde información: ${d.ceros} de 64 quedaron en 0 (marcados en rojo los que no eran 0 y se borraron).`,
          v: () => par(matriz8(d.dct, { modo: "div" }), "Antes (DCT)", matriz8(d.cuantizado, { modo: "cero", marcar: (i, j) => d.cuantizado[i][j] === 0 && Math.abs(d.dct[i][j]) >= 0.5 }), "Después: redondeo(DCT / Q)") },
        { n: "5. Zigzag + Huffman", exp: "Se recorre en zigzag (de bajas a altas frecuencias) para que los ceros queden juntos; se agrupan las rachas de ceros y «EOB» = «el resto son ceros». Esos pocos símbolos van a Huffman (sin pérdida).",
          v: () => h("div", {},
            h("div", { clase: "tokens" }, d.zigzag.map(([u, v], k) => h("span", { clase: "token" + (d.cuantizado[u][v] ? " ref" : ""), estilo: d.cuantizado[u][v] ? {} : { opacity: .35 }, title: `posición zigzag ${k}: (${u},${v})` }, d.cuantizado[u][v]))),
            h("div", { clase: "nota", estilo: { margin: "12px 0 4px" } }, `64 números → ${d.simbolos.length} símbolos para Huffman:`),
            h("div", { clase: "tokens" }, d.simbolos.map((x) => h("span", { clase: "token ref" }, x)))) },
        { n: "6. Reconstruir", exp: "Al descomprimir: multiplicar por la tabla, DCT inversa y sumar 128. Queda muy parecido, pero no idéntico: la diferencia es lo que se perdió al redondear.",
          v: () => h("div", {}, par(matriz8(d.original), "Original", matriz8(d.reconstruido), "Reconstruido"),
            h("div", { clase: "nota", estilo: { marginTop: "10px" } }, `Error por píxel (máximo ${Math.max(...d.error.flat().map(Math.abs))} niveles de 255):`), matriz8(d.error, { modo: "div", max: 30 })) },
      ];
      const zona = h("div");
      const pintar = (k) => vaciar(zona,
        h("div", { clase: "etapas" }, etapas.map((e, i) => h("span", { clase: (i === k ? "activa" : "") + (e.perdida ? " perdida" : "") }, e.n))),
        h("div", { clase: "explicacion" }, etapas[k].exp), etapas[k].v());
      vaciar(zonaBloque, h("div", { clase: "nota", estilo: { marginBottom: "8px" } }, titulo), reproductor(etapas.length, pintar, { intervalo: 2600 }), zona);
    });

    const archivo = h("input", { type: "file", accept: "image/*", estilo: { display: "none" } });
    archivo.addEventListener("change", () => {
      const f = archivo.files[0]; if (!f) return;
      const img = new Image();
      img.onload = () => {
        const lado = 128;
        const esc = Math.min(lado / img.width, lado / img.height, 1);
        const w = Math.max(8, Math.floor(img.width * esc / 8) * 8), hh = Math.max(8, Math.floor(img.height * esc / 8) * 8);
        const c = document.createElement("canvas"); c.width = w; c.height = hh;
        const ctx = c.getContext("2d"); ctx.drawImage(img, 0, 0, w, hh);
        const datos = ctx.getImageData(0, 0, w, hh).data;
        pixeles = [];
        for (let y = 0; y < hh; y++) { const fila = []; for (let x = 0; x < w; x++) { const k = 4 * (y * w + x); fila.push(Math.round(0.299 * datos[k] + 0.587 * datos[k + 1] + 0.114 * datos[k + 2])); } pixeles.push(fila); }
        bloqueSel = null; cargarImagen();
      };
      img.src = URL.createObjectURL(f);
    });
    vaciar(raiz,
      tarjeta("Calidad",
        deslizador("Calidad JPEG", { min: 1, max: 100, valor: 50, formato: (v) => v, alCambiar: (v) => { calidad = v; cargarImagen(); }, retardo: 300 }),
        h("div", { clase: "fila", estilo: { marginTop: "10px" } },
          h("button", { clase: "boton", onclick: () => archivo.click() }, "📷 Usar mi propia imagen"),
          h("button", { clase: "boton", onclick: () => { pixeles = null; bloqueSel = null; cargarImagen(); } }, "Imagen de ejemplo"), archivo,
          h("span", { clase: "nota" }, "Se convierte a grises y se reduce a máx. 128×128 (el código es Python puro)."))),
      tarjeta("La imagen completa", zonaImg),
      tarjeta("Qué le pasa a un bloque 8×8, paso a paso", zonaBloque));
    cargarImagen();
  },
});

// ======================= AUDIO =======================
SECCIONES.push({
  id: "audio", grupo: 3, titulo: "Audio: lo que no se oye, se borra",
  bajada: "Enmascaramiento: un sonido fuerte «tapa» a los débiles de frecuencias cercanas. El códec los elimina porque de todos modos no los oiríamos. Mueva el tono débil y vea cuándo desaparece.",
  codigo: [["audio", "curva_enmascaramiento"], ["audio", "comprimir_trama"], ["audio", "fft"]],
  render(raiz) {
    let frecuencia = 1156.25, nivel = -40, margen = 20;
    const res = h("div");
    const cargar = () => conCarga(res, async () => {
      const d = await api("audio", { frecuencia, nivel, margen });
      const W = 820, H = 320, m = { i: 48, d: 16, a: 14, b: 36 };
      const X = (f) => m.i + (f / 4000) * (W - m.i - m.d), Y = (v) => m.a + ((0 - Math.max(-90, v)) / 90) * (H - m.a - m.b);
      const g = s("svg", { viewBox: `0 0 ${W} ${H}`, width: W });
      for (let v = 0; v >= -90; v -= 15) {
        g.appendChild(s("line", { x1: m.i, x2: W - m.d, y1: Y(v), y2: Y(v), stroke: css("--borde") }));
        g.appendChild(s("text", { x: m.i - 6, y: Y(v) + 4, "text-anchor": "end", "font-size": 11, fill: css("--suave"), texto: v + " dB" }));
      }
      for (let f = 0; f <= 4000; f += 500) g.appendChild(s("text", { x: X(f), y: H - 14, "text-anchor": "middle", "font-size": 11, fill: css("--suave"), texto: f + " Hz" }));
      // zona "no se oye"
      let area = `M${X(0)},${Y(-90)}`;
      d.frecuencias.forEach((f, k) => { area += ` L${X(f)},${Y(d.umbrales[k])}`; });
      area += ` L${X(4000)},${Y(-90)} Z`;
      g.appendChild(s("path", { d: area, fill: tenue("#d64545", .12) }));
      let curva = "";
      d.frecuencias.forEach((f, k) => { curva += `${k ? "L" : "M"}${X(f)},${Y(d.umbrales[k])}`; });
      g.appendChild(s("path", { d: curva, fill: "none", stroke: css("--mal"), "stroke-width": 2, "stroke-dasharray": "6 4" }));
      d.frecuencias.forEach((f, k) => {
        if (d.niveles[k] <= -90) return;
        const oye = d.niveles[k] > d.umbrales[k];
        g.appendChild(s("line", { x1: X(f), x2: X(f), y1: Y(-90), y2: Y(d.niveles[k]), stroke: oye ? css("--ok") : css("--mal"), "stroke-width": 5, "stroke-linecap": "round", opacity: oye ? 1 : .55 }));
        g.appendChild(s("text", { x: X(f), y: Y(d.niveles[k]) - 8, "text-anchor": "middle", "font-size": 11, "font-weight": 700, fill: oye ? css("--ok") : css("--mal"), texto: (oye ? "" : "✕ ") + Math.round(f) }));
      });
      g.appendChild(s("text", { x: W - m.d - 4, y: Y(-80), "text-anchor": "end", "font-size": 12, fill: css("--mal"), texto: "zona roja: por debajo del umbral → no se oye → se borra" }));
      const borrado = d.borrados.some((f) => Math.abs(f - d.debil.f) < 8);
      const reproductorAudio = (b64) => h("audio", { controls: true, src: "data:audio/wav;base64," + b64, estilo: { width: "100%" } });
      vaciar(res,
        tarjeta("Espectro de una trama (FFT) y curva de enmascaramiento",
          h("div", { clase: "desplazable" }, g),
          idea(borrado ? `El tono débil de <b>${Math.round(d.debil.f)} Hz</b> (${d.debil.db} dB) quedó <b>debajo de la curva</b>: un tono fuerte cercano lo tapa → el códec lo <b>borra</b>.`
            : `El tono débil de <b>${Math.round(d.debil.f)} Hz</b> (${d.debil.db} dB) está <b>por encima de la curva</b>: sí se oye → se <b>conserva</b>. Acérquelo a 1000 Hz o 3000 Hz, o bájele el volumen.`, borrado ? "mal" : "ok")),
        h("div", { clase: "indicadores" },
          indicador("Componentes antes", d.audibles),
          indicador("Componentes guardados", d.conservados, "acento"),
          indicador("Ahorro", fmt(100 * (1 - d.conservados / d.audibles), 0) + " %", "ok"),
          indicador("Ruido añadido: dB por debajo de la señal", fmt(d.snr, 1) + " dB")),
        h("div", { clase: "rejilla", estilo: { marginTop: "18px" } },
          tarjeta("🔊 Escuche: original", reproductorAudio(d.wav_original)),
          tarjeta("🔊 Escuche: comprimido", reproductorAudio(d.wav_comprimido))),
        tarjeta("Forma de onda (primeras 256 muestras)", h("div", { clase: "desplazable" }, lineas([
          { nombre: "original", valores: d.muestras, color: css("--suave"), grosor: 3.5 },
          { nombre: "comprimido", valores: d.muestras_rec, color: css("--acento"), grosor: 1.6 },
        ], { ymin: -1, ymax: 1, alto: 200 }))),
        idea("Cuánto pesa: un CD = 44 100 muestras/s × 16 bits × 2 canales = <b>1411 kbps</b>. Un MP3 a 128 kbps es ≈ <b>9 %</b> de eso."));
    });
    vaciar(raiz,
      tarjeta("Señal de prueba: tonos de 1000 Hz (fuerte), 3000 Hz (medio), 3094 Hz (débil) y un tono débil que usted controla",
        deslizador("Frecuencia del tono débil", { min: 100, max: 3900, paso: 15.625, valor: frecuencia, formato: (v) => Math.round(v) + " Hz", alCambiar: (v) => { frecuencia = v; cargar(); }, retardo: 250 }),
        deslizador("Volumen del tono débil", { min: -70, max: -5, valor: nivel, formato: (v) => v + " dB", alCambiar: (v) => { nivel = v; cargar(); }, retardo: 250 }),
        deslizador("Margen del enmascaramiento", { min: 5, max: 40, valor: margen, formato: (v) => v + " dB", alCambiar: (v) => { margen = v; cargar(); }, retardo: 250 })),
      res);
    cargar();
  },
});

// ======================= VIDEO =======================
SECCIONES.push({
  id: "video", grupo: 3, titulo: "Video: guardar solo lo que cambia",
  bajada: "El cuadro I se guarda completo. En cada cuadro P, por cada bloque 8×8 se busca en el cuadro anterior el bloque más parecido y solo se guarda el vector de movimiento y la pequeña diferencia (residuo).",
  codigo: [["video", "estimar_movimiento"], ["video", "sad"], ["video", "codificar"]],
  render(raiz) {
    let dx = 2, dy = 1, cuadros = 6;
    const res = h("div");
    const cargar = () => conCarga(res, async () => {
      const d = await api("video", { dx, dy, cuadros });
      const esc = 6, B = d.bloque;
      const conFlechas = (M, vectores) => {
        const c = lienzoGris(M, esc, { cuadricula: B });
        if (!vectores) return c;
        const ctx = c.getContext("2d");
        ctx.strokeStyle = "#ff3b3b"; ctx.fillStyle = "#ff3b3b"; ctx.lineWidth = 2.5;
        for (const v of vectores) {
          if (!v.dx && !v.dy) continue;
          const x2 = (v.bx + B / 2) * esc, y2 = (v.by + B / 2) * esc, x1 = x2 + v.dx * esc * 2.5, y1 = y2 + v.dy * esc * 2.5;
          ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
          const a = Math.atan2(y2 - y1, x2 - x1);
          ctx.beginPath(); ctx.moveTo(x2, y2); ctx.lineTo(x2 - 9 * Math.cos(a - .5), y2 - 9 * Math.sin(a - .5)); ctx.lineTo(x2 - 9 * Math.cos(a + .5), y2 - 9 * Math.sin(a + .5)); ctx.fill();
        }
        return c;
      };
      const zona = h("div");
      const pintar = (t) => {
        const f = d.flujo[t];
        const marco = (titulo, el, nota) => h("div", {}, h("div", { clase: "nota" }, titulo), el, nota ? h("div", { clase: "nota", estilo: { maxWidth: "290px" } }, nota) : null);
        let cuerpo, exp;
        if (f.tipo === "I") {
          exp = [h("b", {}, "Cuadro 0 = I (imagen completa): "), `se guardan los ${d.ancho * d.alto} píxeles. Es la referencia para los siguientes.`];
          cuerpo = marco("Cuadro I", lienzoGris(d.cuadros[0], esc, { cuadricula: B }));
        } else {
          const movidos = f.vectores.filter((v) => v.dx || v.dy);
          const resAbs = f.residuo.map((fila) => fila.map((v) => Math.min(255, Math.abs(v) * 3)));
          exp = [h("b", {}, `Cuadro ${t} = P: `), `de ${f.vectores.length} bloques, ${f.vectores.length - movidos.length} son iguales al cuadro anterior (vector (0,0)) y ${movidos.length} se movieron`,
            movidos.length ? [" con vector ", h("b", {}, `(${movidos[0].dx}, ${movidos[0].dy})`), ": «este bloque es el de allá, movido»."] : ".",
            ` Se guardan ${f.costo} valores en vez de ${d.ancho * d.alto}.`];
          cuerpo = h("div", { clase: "fila", estilo: { alignItems: "flex-start", gap: "18px" } },
            marco("Cuadro real + vectores de movimiento", conFlechas(d.cuadros[t], f.vectores), "Flecha roja: de dónde vino el contenido del bloque."),
            marco("Predicción (copiando bloques del cuadro anterior)", lienzoGris(f.prediccion, esc, { cuadricula: B })),
            marco("Residuo = real − predicción", lienzoGris(resAbs, esc, { cuadricula: B }), "Negro = 0: no hay nada que guardar."));
        }
        vaciar(zona, h("div", { clase: "explicacion" }, exp), cuerpo);
      };
      vaciar(res,
        tarjeta("Cuadro a cuadro", reproductor(d.flujo.length, pintar, { intervalo: 1600 }), zona),
        tarjeta("Cuánto se guarda en cada cuadro",
          barrasH(d.flujo.map((f, t) => ({ etiqueta: `Cuadro ${t} (${f.tipo})`, valor: f.costo, texto: f.costo + " valores", color: f.tipo === "I" ? css("--aviso") : css("--acento") })), { ancho: 760, max: d.ancho * d.alto }),
          h("div", { clase: "indicadores" },
            indicador("Sin comprimir", ent(d.crudo) + " valores"),
            indicador("Con predicción", ent(d.codificado) + " valores", "acento"),
            indicador("Tamaño", fmt(100 * d.codificado / d.crudo, 1) + " %", "ok"),
            indicador("¿Video idéntico al decodificar?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")),
          idea("1080p a 30 fps sin comprimir ≈ <b>1,5 Gbps</b>; en streaming ≈ 5 Mbps → <b>≈ 300× menos</b>. Un códec real además pasa el residuo por DCT + cuantización (como JPEG): ese es el paso con pérdida. El .mp4 es solo el contenedor.")));
    });
    vaciar(raiz,
      tarjeta("Movimiento del cuadrado",
        deslizador("Velocidad horizontal (dx)", { min: -3, max: 3, valor: dx, formato: (v) => v + " px/cuadro", alCambiar: (v) => { dx = v; cargar(); } }),
        deslizador("Velocidad vertical (dy)", { min: -3, max: 3, valor: dy, formato: (v) => v + " px/cuadro", alCambiar: (v) => { dy = v; cargar(); } }),
        deslizador("Número de cuadros", { min: 2, max: 8, valor: cuadros, formato: (v) => v, alCambiar: (v) => { cuadros = v; cargar(); } })),
      res);
    cargar();
  },
});
