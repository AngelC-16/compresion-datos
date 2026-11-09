/* 1 · Contexto y 2 · Clasificación */

// ======================= ENTROPÍA =======================
SECCIONES.push({
  id: "entropia", grupo: 0, titulo: "El límite: la entropía",
  bajada: "Claude Shannon (1948): la entropía H es el mínimo promedio de bits por símbolo para guardar un mensaje sin perder nada. Escriba un texto y vea de dónde sale cada bit.",
  codigo: [["entropia", "entropia_de_distribucion"], ["entropia", "analisis"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("entropia", { texto });
      reiniciarColores(d.simbolos.map((x) => x.s).join(""));
      const maxC = Math.max(...d.simbolos.map((x) => x.p * x.info), 1e-9);
      const filas = d.simbolos.map((x) => h("tr", {},
        h("td", {}, h("span", { clase: "token", estilo: { background: tenue(colorDe(x.s), .25), borderColor: colorDe(x.s) } }, vis(x.s))),
        h("td", { clase: "num" }, x.veces),
        h("td", { clase: "num" }, fmt(x.p, 3)),
        h("td", { clase: "num" }, fmt(x.info, 3)),
        h("td", { clase: "num" }, fmt(x.p * x.info, 3)),
        h("td", { estilo: { width: "30%" } }, h("div", { estilo: { height: "12px", borderRadius: "6px", width: (100 * x.p * x.info / maxC) + "%", background: colorDe(x.s) } }))));
      // barra apilada: H como suma de contribuciones
      const apilada = h("div", { estilo: { display: "flex", height: "34px", borderRadius: "8px", overflow: "hidden", border: "1px solid var(--borde)" } },
        d.simbolos.map((x) => h("div", { title: `${vis(x.s)}: ${fmt(x.p * x.info, 3)} bits`, estilo: { width: (100 * x.p * x.info / Math.max(d.entropia, 1e-9)) + "%", background: colorDe(x.s), color: "#fff", display: "grid", placeItems: "center", fontSize: "12px", fontWeight: 700 } }, x.p * x.info / Math.max(d.entropia, 1e-9) > 0.06 ? vis(x.s) : "")));
      vaciar(res,
        h("div", { clase: "indicadores" },
          indicador("Entropía H (bits por símbolo)", fmt(d.entropia, 3), "acento"),
          indicador("Bits con ASCII (8 por símbolo)", ent(d.bits_originales)),
          indicador("Mínimo teórico n·H", fmt(d.bits_minimos, 1) + " bits", "ok"),
          indicador("Redundancia (lo que sobra)", fmt(100 * d.redundancia, 1) + " %", "mal")),
        tarjeta([h("span", { clase: "paso-n" }, "1"), "Contar y calcular la sorpresa de cada símbolo"],
          h("p", { clase: "nota" }, "p(x) = veces / total. La «sorpresa» −log₂ p(x) dice cuántos bits merece: lo frecuente sorprende poco (pocos bits) y lo raro mucho."),
          h("div", { clase: "desplazable" }, h("table", { clase: "datos" },
            h("thead", {}, h("tr", {}, h("th", {}, "símbolo"), h("th", {}, "veces"), h("th", {}, "p(x)"), h("th", {}, "−log₂ p(x)"), h("th", {}, "p·(−log₂ p)"), h("th", {}, "aporte a H"))),
            h("tbody", {}, filas)))),
        tarjeta([h("span", { clase: "paso-n" }, "2"), "Sumar: H = Σ p(x) · (−log₂ p(x))"],
          apilada,
          h("p", {}, "H = ", d.simbolos.map((x, k) => [k ? " + " : "", h("b", { estilo: { color: colorDe(x.s) } }, fmt(x.p * x.info, 3))]), " = ", h("b", {}, fmt(d.entropia, 3) + " bits/símbolo")),
          barrasH([
            { etiqueta: "Guardado en ASCII", valor: d.bits_originales, texto: ent(d.bits_originales) + " bits", color: css("--suave") },
            { etiqueta: "Límite de Shannon", valor: d.bits_minimos, texto: fmt(d.bits_minimos, 1) + " bits", color: css("--ok") },
          ], { ancho: 640 }),
          idea(`Ningún compresor sin pérdida que mire solo la frecuencia de cada símbolo puede bajar de <b>${fmt(d.bits_minimos, 1)} bits</b>. Es «la naranja exprimida».`, "ok")));
    });
    const moneda = h("div");
    const dibujarMoneda = async (p) => {
      const d = await api("entropia", { texto: "x", p });
      const W = 520, H = 220, m = 36;
      const X = (v) => m + v * (W - 2 * m), Y = (v) => H - m - v * (H - 2 * m);
      let path = "";
      for (let k = 0; k <= 100; k++) { const q = k / 100; const e = q <= 0 || q >= 1 ? 0 : -(q * Math.log2(q) + (1 - q) * Math.log2(1 - q)); path += `${k ? "L" : "M"}${X(q)},${Y(e)}`; }
      const g = s("svg", { viewBox: `0 0 ${W} ${H}`, width: W },
        s("line", { x1: m, x2: W - m, y1: Y(0), y2: Y(0), stroke: css("--borde") }),
        s("line", { x1: m, x2: W - m, y1: Y(1), y2: Y(1), stroke: css("--borde"), "stroke-dasharray": "4 4" }),
        s("path", { d: path, fill: "none", stroke: css("--acento"), "stroke-width": 3 }),
        s("line", { x1: X(p), x2: X(p), y1: Y(0), y2: Y(d.moneda.H), stroke: css("--mal"), "stroke-dasharray": "4 3" }),
        s("circle", { cx: X(p), cy: Y(d.moneda.H), r: 7, fill: css("--mal") }),
        s("text", { x: X(p) + 10, y: Y(d.moneda.H) - 8, "font-size": 14, "font-weight": 700, texto: fmt(d.moneda.H, 2) + " bits" }),
        s("text", { x: m, y: H - 10, "font-size": 11, fill: css("--suave"), texto: "p(cara) = 0" }),
        s("text", { x: W - m, y: H - 10, "font-size": 11, "text-anchor": "end", fill: css("--suave"), texto: "1" }),
        s("text", { x: X(.5), y: H - 10, "font-size": 11, "text-anchor": "middle", fill: css("--suave"), texto: "0,5" }),
        s("text", { x: 4, y: Y(1) + 4, "font-size": 11, fill: css("--suave"), texto: "1 bit" }));
      const tipo = Math.abs(p - .5) < .03 ? "Impredecible: cada lanzamiento aporta información nueva (1 bit)." : p > .97 || p < .03 ? "Casi siempre sale lo mismo: casi no hay información que guardar." : "Predecible: se necesitan menos de 1 bit por lanzamiento.";
      vaciar(moneda, h("div", { clase: "fila" }, g, h("div", { estilo: { flex: "1 1 220px" } },
        h("div", { clase: "indicadores" }, indicador("cara", fmt(100 * p, 0) + " %"), indicador("sello", fmt(100 * (1 - p), 0) + " %"), indicador("H por lanzamiento", fmt(d.moneda.H, 2) + " bits", "acento")),
        h("p", {}, tipo))));
    };
    vaciar(raiz,
      tarjeta("Texto a analizar", campoTexto("ABRACADABRA", ["AAAAAAAAAAAAAAAA", "ABABABABABABABAB", "ABRACADABRA", "súbete para arriba", "q7#Lz!0pW@k9&Xr2"], cargar)),
      res,
      tarjeta("La moneda de la diapositiva: justa vs. cargada",
        deslizador("Probabilidad de cara", { min: 0.01, max: 0.99, paso: 0.01, valor: 0.9, formato: (v) => fmt(100 * v, 0) + " %", alCambiar: dibujarMoneda }),
        moneda),
      idea("Ojo: «ABABAB…» da H = 1 bit porque esta fórmula solo mira cuántas veces aparece cada letra. Un modelo con <b>contexto</b> (que mira lo anterior) ve que es totalmente predecible: así trabajan Lempel-Ziv, BWT y la IA."));
    cargar("ABRACADABRA"); dibujarMoneda(0.9);
  },
});

// ======================= ESTÁTICA VS ADAPTATIVA =======================
SECCIONES.push({
  id: "adaptativa", grupo: 1, titulo: "¿Cuándo aprende el modelo?",
  bajada: "Estática: lee todo, arma una tabla fija y la envía con el archivo. Adaptativa: aprende mientras lee y no envía tabla. Mueva el cursor y vea cuánto cuesta cada símbolo en cada modelo.",
  codigo: [["adaptativa", "costo_estatico"], ["adaptativa", "costo_adaptativo"]],
  render(raiz) {
    const res = h("div");
    let memoria = 8, texto = "A".repeat(50) + "B".repeat(50);
    const cargar = () => conCarga(res, async () => {
      const d = await api("adaptativa", { texto, memoria });
      reiniciarColores(d.texto);
      const vista = h("div"), grafica = h("div", { clase: "desplazable" });
      const colE = css("--suave"), colA = "#4c6ef5", colV = css("--ok");
      const pintar = (i) => {
        vaciar(grafica, lineas([
          { nombre: "Estática", valores: d.estatico.costos, color: colE },
          { nombre: "Adaptativa (recuerda todo)", valores: d.adaptativo.costos, color: colA },
          { nombre: `Adaptativa (recuerda ${d.memoria})`, valores: d.ventana.costos, color: colV },
        ], { etiquetaY: "bits que cuesta cada símbolo", marcaX: i }));
        const c = d.texto[i];
        const celdas = h("div", { clase: "celdas" }, [...d.texto].map((ch, k) => h("div", { clase: "celda" + (k === i ? " actual" : k > i ? " atenuada" : ""), estilo: { minWidth: "18px", height: "26px", fontSize: "13px", background: tenue(colorDe(ch), k <= i ? .3 : .1) } }, vis(ch))));
        vaciar(vista, celdas,
          h("div", { clase: "explicacion", estilo: { marginTop: "12px" } },
            h("b", {}, `Posición ${i}: llega «${vis(c)}». `),
            `La estática le cobra siempre ${fmt(d.estatico.costos[i], 2)} bits. `,
            `La adaptativa estima p(${vis(c)}) = ${fmt(d.adaptativo.probs[i], 3)} con lo visto hasta ahora → ${fmt(d.adaptativo.costos[i], 2)} bits. `,
            `Con memoria corta: p = ${fmt(d.ventana.probs[i], 3)} → ${fmt(d.ventana.costos[i], 2)} bits.`));
      };
      vaciar(res,
        tarjeta("Recorrer el texto símbolo a símbolo", reproductor(d.texto.length, pintar, { intervalo: 120 }), vista, grafica),
        tarjeta("Total de bits",
          barrasH([
            { etiqueta: "Estática (datos + tabla)", valor: d.estatico.total, texto: `${fmt(d.estatico.datos, 1)} + ${d.estatico.tabla} tabla = ${fmt(d.estatico.total, 1)}`, color: colE },
            { etiqueta: "Adaptativa (todo)", valor: d.adaptativo.total, texto: fmt(d.adaptativo.total, 1) + " bits", color: colA },
            { etiqueta: `Adaptativa (últimos ${d.memoria})`, valor: d.ventana.total, texto: fmt(d.ventana.total, 1) + " bits", color: colV },
          ], { ancho: 760 }),
          idea("La adaptativa no envía tabla y, cuando el contenido cambia, <b>reacciona</b>: el símbolo nuevo es caro al principio pero rápidamente se abarata. La estática cobra lo mismo de principio a fin.", "ok")));
    });
    vaciar(raiz,
      tarjeta("Entrada",
        campoTexto(texto, ["A".repeat(50) + "B".repeat(50), "ABRACADABRA".repeat(3), "AAAAAAAAAABBBBBBBBBBAAAAAAAAAABBBBBBBBBB", "el perro y el gato y el perro y el gato"], (t) => { texto = t; cargar(); }),
        h("div", { estilo: { marginTop: "12px" } }, deslizador("Memoria (ventana)", { min: 2, max: 64, valor: 8, formato: (v) => v + " símbolos", alCambiar: (v) => { memoria = v; cargar(); }, retardo: 250 }))),
      res,
      idea("Ojo (diapositiva 6): «basada en contexto» es otra idea —predecir según lo que vino antes— y puede ser estática o adaptativa."));
    cargar();
  },
});
