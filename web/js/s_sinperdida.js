/* 3 · Sin pérdida (y la estructura «heap» de la sección 5) */

// ======================= RLE =======================
SECCIONES.push({
  id: "rle", grupo: 2, titulo: "RLE: contar repeticiones",
  bajada: "Run-Length Encoding: en lugar de guardar cada símbolo, guarda (cuántas veces seguidas, símbolo). Brilla con rachas largas… y falla sin ellas.",
  codigo: [["rle", "codificar"], ["rle", "decodificar"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("rle", { texto });
      reiniciarColores(d.texto);
      const inicios = []; let p = 0;
      d.rachas.forEach(([n]) => { inicios.push(p); p += n; });
      const vista = h("div");
      const pintar = (k) => {
        const [n, c] = d.rachas[k], ini = inicios[k];
        const celdas = h("div", { clase: "celdas con-indices" }, [...d.texto].map((ch, i) => {
          const r = inicios.findIndex((x, j) => i >= x && i < x + d.rachas[j][0]);
          const cls = r === k ? " actual" : r > k ? " atenuada" : "";
          return h("div", { clase: "celda" + cls, estilo: { background: tenue(colorDe(ch), r <= k ? .3 : .08) } }, h("small", {}, i), vis(ch));
        }));
        const salida = h("div", { clase: "tokens" }, d.rachas.slice(0, k + 1).map(([n2, c2], j) =>
          h("span", { clase: "token" + (j === k ? " actual" : ""), estilo: { background: tenue(colorDe(c2), .25), borderColor: colorDe(c2) } }, h("b", {}, n2), vis(c2))));
        vaciar(vista,
          h("div", { clase: "explicacion" }, h("b", {}, `Paso ${k + 1}: `), `desde la posición ${ini} se lee «${vis(c)}» y se cuenta cuántas veces se repite seguido: `, h("b", {}, n), ` → se guarda (${n}, ${vis(c)}).`),
          h("div", { clase: "nota" }, "Original"), celdas,
          h("div", { clase: "nota", estilo: { marginTop: "12px" } }, "Comprimido"), salida);
      };
      const crecio = d.codificado > d.original;
      vaciar(res,
        tarjeta("Paso a paso", reproductor(d.rachas.length, pintar, { intervalo: 900 }), vista),
        h("div", { clase: "indicadores" },
          indicador("Símbolos originales", d.original),
          indicador("Símbolos tras RLE (2 por racha)", d.codificado, crecio ? "mal" : "ok"),
          indicador("Tamaño", fmt(100 * d.codificado / Math.max(1, d.original), 0) + " %", crecio ? "mal" : "ok"),
          indicador("¿Se recupera igual?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")),
        crecio ? idea("<b>¡La trampa!</b> Sin repeticiones el archivo <b>crece</b>: cada símbolo suelto pasa a ocupar dos casillas (1 y el símbolo).", "mal") : idea("Con rachas largas RLE ahorra mucho: es ideal para íconos, fax o BMP con bloques de un solo color.", "ok"));
    });

    // Editor de píxeles: cada fila se comprime con RLE
    const W = 16, Hh = 8;
    let px = ["................", "......####......", "....########....", "...##########...", "...##########...", "....########....", "......####......", "................"].map((f) => [...f].map((c) => c === "#"));
    const rejilla = h("div", { clase: "lienzo-pixeles", estilo: { gridTemplateColumns: `repeat(${W}, 20px)` } });
    const filasRLE = h("div", { clase: "mono", estilo: { fontSize: "14px", lineHeight: "22px" } });
    const resumen = h("div");
    const actualizar = async () => {
      vaciar(rejilla, px.flatMap((fila, y) => fila.map((on, x) => h("div", { clase: on ? "on" : "", onclick: () => { px[y][x] = !px[y][x]; actualizar(); } }))));
      const d = await api("rle", { filas: px.map((f) => f.map((on) => (on ? "#" : ".")).join("")) });
      vaciar(filasRLE, d.filas.map((f) => h("div", {}, f.rachas.map(([n, c]) => h("span", { estilo: { color: c === "#" ? css("--acento") : css("--suave"), marginRight: "6px" } }, `${n}${c === "#" ? "■" : "□"}`)))));
      vaciar(resumen, h("div", { clase: "indicadores" }, indicador("Píxeles", d.original), indicador("Símbolos con RLE", d.codificado, d.codificado > d.original ? "mal" : "ok"), indicador("Tamaño", fmt(100 * d.codificado / d.original, 0) + " %", d.codificado > d.original ? "mal" : "ok")));
    };
    vaciar(raiz,
      tarjeta("Texto", campoTexto("AAAAABBBCC", ["AAAAABBBCC", "ABC", "WWWWWWWWWWWWBWWWWWWWWWWWWBBBWWWWWWWW", "hola mundo"], cargar, 80)),
      res,
      tarjeta("Pruébelo con una imagen: haga clic en los píxeles",
        h("div", { clase: "fila", estilo: { alignItems: "flex-start", gap: "28px" } }, rejilla, filasRLE),
        resumen, h("p", { clase: "nota" }, "Dibuje algo con bloques grandes (comprime) o un tablero de ajedrez (crece) y compare.")));
    cargar("AAAAABBBCC"); actualizar();
  },
});

// ======================= HEAP =======================
SECCIONES.push({
  id: "heap", grupo: 4, titulo: "Cola de prioridad (montículo binario)",
  bajada: "La estructura que usa Huffman para sacar siempre los dos nodos de menor frecuencia. Es un árbol binario completo guardado en un arreglo: insertar y extraer cuestan O(log n).",
  codigo: [["estructuras", "MinHeap"]],
  render(raiz) {
    let arreglo = [];
    const vista = h("div"), controles = h("div");
    const entrada = h("input", { type: "number", value: 5, estilo: { width: "90px" } });
    const ejecutar = async (ops) => {
      let pasos = [];
      let estado = arreglo;
      for (const op of ops) {
        const d = await api("heap", { arreglo: estado, ...op });
        pasos = pasos.concat(d.pasos.map((p) => ({ ...p, op, extraido: d.extraido })));
        estado = d.arreglo;
      }
      arreglo = estado;
      mostrar(pasos);
    };
    const texto = (p, previo) => {
      const A = p.arreglo;
      switch (p.accion) {
        case "agregar": return [h("b", {}, `Insertar ${A[p.i]}: `), `se coloca al final del arreglo (posición ${p.i}). Ahora debe «subir» mientras sea menor que su padre.`];
        case "comparar": {
          if (p.j < p.i) return [h("b", {}, "Comparar con el padre: "), `posición ${p.i} (${A[p.i]}) vs. su padre en (${p.i}−1)//2 = ${p.j} (${A[p.j]}). `, A[p.i] < A[p.j] ? "Es menor → hay que intercambiar." : "No es menor → ya está en su lugar."];
          return [h("b", {}, "Comparar con el hijo menor: "), `posición ${p.i} (${A[p.i]}) vs. hijo en ${p.j} (${A[p.j]}). `, A[p.j] < A[p.i] ? "El hijo es menor → hay que intercambiar." : "El padre ya es menor → ya está en su lugar."];
        }
        case "intercambiar": return [h("b", {}, "Intercambiar "), `posiciones ${p.i} y ${p.j}.`];
        case "mover_ultimo": return [h("b", {}, `Extraer el mínimo (${p.extraido}): `), "se saca la raíz y el último elemento pasa a la raíz. Ahora debe «bajar» cambiándose con su hijo menor."];
        default: return [h("b", {}, "Listo. "), p.op.op === "extraer" ? `Se extrajo ${p.extraido}. ` : "", "La raíz (posición 0) vuelve a ser el menor de todos."];
      }
    };
    const mostrar = (pasos) => {
      const zona = h("div");
      const pintar = (k) => {
        const p = pasos[k];
        const marcar = {};
        const amarillo = css("--aviso"), verde = css("--ok"), azul = css("--acento");
        if (p.accion === "comparar") { marcar[p.i] = amarillo; marcar[p.j] = amarillo; }
        if (p.accion === "intercambiar") { marcar[p.i] = verde; marcar[p.j] = verde; }
        if (p.accion === "agregar" || p.accion === "mover_ultimo") marcar[p.i] = azul;
        if (p.accion === "fin" && p.arreglo.length) marcar[0] = verde;
        const celdas = h("div", { clase: "celdas con-indices" }, p.arreglo.map((v, i) => h("div", { clase: "celda", estilo: marcar[i] ? { background: tenue(marcar[i], .3), borderColor: marcar[i], borderWidth: "2px" } : {} }, h("small", {}, i), v)));
        vaciar(zona, h("div", { clase: "explicacion" }, texto(p)),
          h("div", { clase: "desplazable" }, p.arreglo.length ? dibujarHeap(p.arreglo, { marcar, ancho: Math.max(420, Math.min(900, 2 ** Math.floor(Math.log2(p.arreglo.length)) * 70)) }) : h("p", { clase: "nota" }, "(heap vacío)")),
          h("div", { clase: "nota", estilo: { marginTop: "10px" } }, "Así se guarda en memoria (arreglo): padre = (i−1)//2 · hijos = 2i+1 y 2i+2"), celdas);
      };
      vaciar(vista, tarjeta("Paso a paso", reproductor(pasos.length, pintar, { intervalo: 1000 }), zona));
    };
    vaciar(controles, h("div", { clase: "fila" },
      entrada,
      h("button", { clase: "boton primario", onclick: () => ejecutar([{ op: "insertar", valor: Number(entrada.value) }]) }, "Insertar"),
      h("button", { clase: "boton", onclick: () => ejecutar([{ op: "extraer" }]) }, "Extraer mínimo"),
      h("button", { clase: "boton", onclick: () => { arreglo = []; ejecutar([{ op: "insertar", valor: 7 }, ...[3, 9, 1, 4, 5, 2].map((v) => ({ op: "insertar", valor: v }))]); } }, "Ejemplo: insertar 7, 3, 9, 1, 4, 5, 2"),
      h("button", { clase: "boton", onclick: () => { arreglo = []; vaciar(vista); } }, "Vaciar")));
    vaciar(raiz,
      tarjeta("Operaciones", controles,
        h("div", { clase: "indicadores", estilo: { marginTop: "12px" } }, indicador("ver mínimo", "O(1)"), indicador("insertar", "O(log n)"), indicador("extraer mínimo", "O(log n)"))),
      vista,
      idea("¿Por qué O(log n)? Un árbol completo con n nodos tiene altura ⌊log₂ n⌋: subir o bajar recorre como máximo un camino de la raíz a una hoja."));
    ejecutar([{ op: "insertar", valor: 7 }, ...[3, 9, 1, 4, 5, 2].map((v) => ({ op: "insertar", valor: v }))]);
  },
});

// ======================= HUFFMAN =======================
SECCIONES.push({
  id: "huffman", grupo: 2, titulo: "Huffman: corto para lo frecuente",
  bajada: "David Huffman (1952). La cola de prioridad entrega siempre los dos nodos de menor frecuencia; se unen en un árbol binario. El camino hasta cada hoja es su código: izquierda = 0, derecha = 1.",
  codigo: [["huffman", "construir_arbol"], ["huffman", "generar_codigos"], ["huffman", "codigos_canonicos"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("huffman", { texto });
      reiniciarColores(d.tabla.map((x) => x.s).join(""));
      const N = d.nodos;
      const nombre = (id) => N[id].s !== null ? `«${vis(N[id].s)}»(${N[id].f})` : `nodo(${N[id].f})`;

      // --- construcción ---
      const zona = h("div");
      const pintar = (k) => {
        const p = d.pasos[k];
        const cola = [...p.bosque].sort((a, b) => N[a].f - N[b].f);
        let exp;
        if (k === 0) exp = [h("b", {}, "Inicio: "), "se cuenta la frecuencia de cada símbolo (tabla hash) y se mete una hoja por símbolo en la cola de prioridad."];
        else {
          const [a, b, pa] = p.fusion;
          exp = [h("b", {}, `Fusión ${k}: `), "la cola entrega los dos menores, ", h("b", {}, nombre(a)), " y ", h("b", {}, nombre(b)), `. Se crea un padre con ${N[a].f} + ${N[b].f} = `, h("b", {}, N[pa].f), " (izquierda = 0, derecha = 1) y vuelve a la cola."];
          if (k === d.pasos.length - 1) exp.push(h("div", {}, "Queda un solo árbol: ¡es el árbol de Huffman!"));
        }
        const res2 = p.fusion ? new Set([p.fusion[0], p.fusion[1]]) : new Set();
        vaciar(zona,
          h("div", { clase: "explicacion" }, exp),
          h("div", { clase: "fila", estilo: { marginBottom: "10px" } }, h("span", { clase: "nota" }, "Cola de prioridad (de menor a mayor):"),
            cola.map((id) => h("span", { clase: "token" + (id === (p.fusion || [])[2] ? " ref" : ""), estilo: N[id].s !== null ? { borderColor: colorDe(N[id].s) } : {} }, N[id].s !== null ? vis(N[id].s) : "●", " ", h("b", {}, N[id].f)))),
          h("div", { clase: "desplazable" }, dibujarBosque(N, p.bosque, { resaltar: res2, nuevo: p.fusion ? p.fusion[2] : null })));
      };

      // --- decodificación recorriendo el árbol (códigos del árbol) ---
      const codArbol = Object.fromEntries(d.tabla.map((x) => [x.s, x.arbol]));
      const bitsArbol = [...d.texto].map((c) => codArbol[c]).join("").slice(0, 60);
      const pasosDec = [];
      let nodo = d.raiz, salida = "", camino = [d.raiz];
      for (let i = 0; i < bitsArbol.length; i++) {
        const b = bitsArbol[i];
        nodo = b === "0" ? N[nodo].izq : N[nodo].der;
        camino.push(nodo);
        let emitido = null;
        if (N[nodo].s !== null) { emitido = N[nodo].s; salida += emitido; }
        pasosDec.push({ i, b, camino: [...camino], salida, emitido });
        if (emitido !== null) { nodo = d.raiz; camino = [d.raiz]; }
      }
      const zonaDec = h("div");
      const pintarDec = (k) => {
        const p = pasosDec[k];
        vaciar(zonaDec,
          h("div", { clase: "explicacion" }, h("b", {}, `Bit ${p.i + 1} = ${p.b}: `), p.b === "0" ? "bajar a la izquierda. " : "bajar a la derecha. ",
            p.emitido !== null ? [h("b", {}, `¡Hoja «${vis(p.emitido)}»!`), " Se escribe y se vuelve a la raíz."] : "Todavía no es una hoja: seguir leyendo."),
          h("div", { clase: "bits" }, [...bitsArbol].map((b, i) => h("span", { estilo: { background: i === p.i ? css("--acento") : i < p.i ? css("--panel-2") : "transparent", color: i === p.i ? "#fff" : null } }, b))),
          h("div", { clase: "fila" }, h("span", { clase: "nota" }, "Texto recuperado:"), h("span", { clase: "mono", estilo: { fontSize: "20px", fontWeight: 700 } }, p.salida || "…")),
          h("div", { clase: "desplazable" }, dibujarBosque(N, [d.raiz], { resaltar: new Set(p.camino), nuevo: p.emitido !== null ? p.camino[p.camino.length - 1] : null })));
      };

      const filas = d.tabla.map((x) => h("tr", {},
        h("td", {}, h("span", { clase: "token", estilo: { background: tenue(colorDe(x.s), .25), borderColor: colorDe(x.s) } }, vis(x.s))),
        h("td", { clase: "num" }, x.veces), h("td", { clase: "mono" }, x.arbol), h("td", { clase: "mono" }, h("b", {}, x.canonico)),
        h("td", { clase: "num" }, x.veces * x.canonico.length)));
      vaciar(res,
        tarjeta([h("span", { clase: "paso-n" }, "1"), "Construir el árbol con la cola de prioridad"], reproductor(d.pasos.length, pintar, { intervalo: 1600 }), zona),
        tarjeta([h("span", { clase: "paso-n" }, "2"), "Leer los códigos del árbol"],
          h("div", { clase: "desplazable" }, h("table", { clase: "datos" },
            h("thead", {}, h("tr", {}, h("th", {}, "símbolo"), h("th", {}, "veces"), h("th", {}, "código (árbol)"), h("th", {}, "código canónico"), h("th", {}, "bits usados"))),
            h("tbody", {}, filas))),
          idea("Los dos códigos tienen las <b>mismas longitudes</b> (ambos son óptimos). El <b>canónico</b> se reconstruye solo con las longitudes; es el que usan ZIP, PNG y JPEG, y el de la diapositiva.")),
        tarjeta([h("span", { clase: "paso-n" }, "3"), "Codificar el texto"],
          h("div", { clase: "bits" }, d.segmentos.map((x) => h("span", { title: vis(x.s), estilo: { background: tenue(colorDe(x.s), .28), borderBottom: `3px solid ${colorDe(x.s)}` } }, x.c))),
          h("div", { clase: "indicadores" },
            indicador("ASCII (8 bits × " + d.texto.length + ")", d.ascii + " bits"),
            indicador("Huffman", d.bits + " bits", "acento"),
            indicador("Límite de Shannon", fmt(d.entropia * d.texto.length, 1) + " bits", "ok"),
            indicador("Libre de prefijo", d.prefijo_ok ? "Sí ✓" : "No", "ok")),
          barrasH([
            { etiqueta: "ASCII", valor: d.ascii, texto: d.ascii + " bits", color: css("--suave") },
            { etiqueta: "Huffman", valor: d.bits, texto: d.bits + " bits", color: css("--acento") },
            { etiqueta: "Entropía (mínimo)", valor: d.entropia * d.texto.length, texto: fmt(d.entropia * d.texto.length, 1) + " bits", color: css("--ok") },
          ])),
        tarjeta([h("span", { clase: "paso-n" }, "4"), "Decodificar: bajar por el árbol bit a bit"],
          bitsArbol.length ? [reproductor(pasosDec.length, pintarDec, { intervalo: 700 }), zonaDec] : h("p", {}, "—"),
          h("p", { clase: "nota" }, "Ningún código es prefijo de otro, así que al llegar a una hoja no hay duda: el símbolo terminó.")));
    });
    vaciar(raiz, tarjeta("Texto", campoTexto("ABRACADABRA", ["ABRACADABRA", "AAAAAAAAAB", "la compresion de datos", "mississippi"], cargar, 300)), res);
    cargar("ABRACADABRA");
  },
});

// ======================= LZ77 =======================
SECCIONES.push({
  id: "lz77", grupo: 2, titulo: "LZ77: «esto ya lo vi»",
  bajada: "En vez de repetir una secuencia, apunta a donde apareció antes: (retrocede, copia). Para encontrar rápido las repeticiones usa una tabla hash con los tríos de símbolos ya vistos.",
  codigo: [["lz77", "codificar"], ["lz77", "decodificar"]],
  render(raiz) {
    const res = h("div");
    let texto = "ABRACADABRA", ventana = 64;
    const cargar = () => conCarga(res, async () => {
      const d = await api("lz77", { texto, ventana });
      reiniciarColores(d.texto);
      const zona = h("div");
      const pintar = (k) => {
        const t = d.tokens[k];
        const ini = Math.max(0, t.i - d.ventana);
        const cand = new Set(); t.candidatos.forEach((p) => { for (let q = p; q < p + 3; q++) cand.add(q); });
        const celdas = h("div", { clase: "celdas con-indices" }, [...d.texto].map((ch, i) => {
          let cls = "";
          if (i >= ini && i < t.i) cls += " ventana";
          if (cand.has(i) && i < t.i) cls += " candidato";
          if (t.tipo === "R" && i >= t.origen && i < t.origen + t.long) cls += " fuente";
          if (i >= t.i && i < t.i + t.long) cls += t.tipo === "R" ? " destino" : " actual";
          if (i >= t.i + t.long) cls += " atenuada";
          return h("div", { clase: "celda" + cls }, h("small", {}, i), vis(ch));
        }));
        const clave = t.clave.length === 3 ? `«${[...t.clave].map(vis).join("")}»` : "(menos de 3 símbolos)";
        const exp = [h("b", {}, `Posición ${t.i}: `), `se busca la clave ${clave} en la tabla hash → `,
          t.candidatos.length ? h("b", {}, `candidatos en ${t.candidatos.join(", ")}. `) : "no aparece todavía. "];
        if (t.tipo === "R") exp.push("La mejor coincidencia mide ", h("b", {}, t.long), " → se guarda ", h("b", {}, `(retrocede ${t.dist}, copia ${t.long})`), " en vez de " + t.long + " símbolos.");
        else exp.push("No hay coincidencia de al menos 3 → se guarda el literal ", h("b", {}, `«${vis(t.s)}»`), ".");
        vaciar(zona, h("div", { clase: "explicacion" }, exp),
          h("div", { clase: "fila nota", estilo: { marginBottom: "6px" } }, h("span", { clase: "celda ventana", estilo: { height: "18px", minWidth: "18px" } }, ""), "ventana (lo ya leído)",
            h("span", { clase: "celda fuente", estilo: { height: "18px", minWidth: "18px" } }, ""), "de dónde se copia",
            h("span", { clase: "celda destino", estilo: { height: "18px", minWidth: "18px" } }, ""), "lo que se reemplaza"),
          celdas,
          h("div", { clase: "nota", estilo: { marginTop: "14px" } }, "Salida (tokens):"),
          h("div", { clase: "tokens" }, d.tokens.slice(0, k + 1).map((x, j) => h("span", { clase: "token" + (x.tipo === "R" ? " ref" : "") + (j === k ? " actual" : "") }, x.tipo === "R" ? `(←${x.dist}, ${x.long})` : vis(x.s)))));
      };
      const refs = d.tokens.filter((t) => t.tipo === "R").length;
      vaciar(res,
        tarjeta("Paso a paso", reproductor(d.tokens.length, pintar, { intervalo: 1300 }), zona),
        h("div", { clase: "indicadores" },
          indicador("Símbolos del texto", d.texto.length),
          indicador("Tokens emitidos", d.tokens.length, "acento"),
          indicador("Literales / referencias", `${d.tokens.length - refs} / ${refs}`),
          indicador("¿Se recupera igual?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")),
        tarjeta("¿Para qué la tabla hash?",
          barrasH([
            { etiqueta: "Fuerza bruta (toda la ventana)", valor: d.comparaciones_bruta, texto: ent(d.comparaciones_bruta) + " comparaciones", color: css("--mal") },
            { etiqueta: "Con tabla hash (candidatos)", valor: d.comparaciones_hash, texto: ent(d.comparaciones_hash) + " comparaciones", color: css("--ok") },
          ], { ancho: 760 }),
          idea("La tabla hash responde en O(1) «¿dónde apareció antes este trío?», así solo se compara contra posiciones que ya empiezan igual. LZ77 + Huffman = DEFLATE (ZIP, gzip, PNG).")));
    });
    vaciar(raiz, tarjeta("Entrada",
      campoTexto(texto, ["ABRACADABRA", "AAAAAAAAAAAAAAAAAAAA", "la compresion de la compresion", "TOBEORNOTTOBEORTOBEORNOT"], (t) => { texto = t; cargar(); }, 120),
      h("div", { estilo: { marginTop: "12px" } }, deslizador("Tamaño de la ventana", { min: 3, max: 64, valor: 64, formato: (v) => v + " símbolos", alCambiar: (v) => { ventana = v; cargar(); }, retardo: 250 }))), res);
    cargar();
  },
});

// ======================= LZW =======================
SECCIONES.push({
  id: "lzw", grupo: 2, titulo: "LZW: un diccionario que se arma solo",
  bajada: "Lee la secuencia más larga que ya está en el diccionario, emite su número y agrega esa secuencia + la siguiente letra como entrada nueva. Como escribir «ONU» en vez del nombre completo.",
  codigo: [["lzw", "codificar"], ["lzw", "decodificar"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("lzw", { texto });
      reiniciarColores(d.texto);
      const posiciones = []; let p = 0;
      d.pasos.forEach((x) => { posiciones.push(p); p += x.w.length; });
      const zona = h("div");
      const pintar = (k) => {
        const x = d.pasos[k], ini = posiciones[k];
        const celdas = h("div", { clase: "celdas con-indices" }, [...d.texto].map((ch, i) => {
          let cls = i < ini ? "" : i < ini + x.w.length ? " destino" : i === ini + x.w.length && x.nueva ? " fuente" : " atenuada";
          return h("div", { clase: "celda" + cls }, h("small", {}, i), vis(ch));
        }));
        const entradas = d.alfabeto.map((s2, i) => ({ s: s2, n: i, nueva: false })).concat(d.pasos.slice(0, k + 1).filter((y) => y.nueva).map((y, j, arr) => ({ s: y.nueva, n: y.numero, nueva: y === x })));
        vaciar(zona,
          h("div", { clase: "explicacion" }, h("b", {}, `Paso ${k + 1}: `), "la secuencia más larga que ya está en el diccionario es ", h("b", {}, `«${x.w}»`), ` (código ${x.emite}) → se emite `, h("b", {}, x.emite), ". ",
            x.nueva ? ["Se agrega ", h("b", {}, `«${x.nueva}» = ${x.numero}`), " para la próxima vez."] : "Fin del texto."),
          celdas,
          h("div", { clase: "rejilla", estilo: { marginTop: "14px" } },
            h("div", {}, h("div", { clase: "nota" }, "Códigos emitidos"), h("div", { clase: "tokens" }, d.pasos.slice(0, k + 1).map((y, j) => h("span", { clase: "token" + (j === k ? " actual" : "") }, y.emite)))),
            h("div", {}, h("div", { clase: "nota" }, "Diccionario (tabla hash)"),
              h("div", { clase: "tokens" }, entradas.map((e) => h("span", { clase: "token" + (e.nueva ? " ref actual" : "") }, h("b", {}, e.n), " = ", e.s))))));
      };
      vaciar(res,
        tarjeta("Paso a paso", reproductor(d.pasos.length, pintar, { intervalo: 1300 }), zona),
        h("div", { clase: "indicadores" },
          indicador("Letras", d.texto.length), indicador("Códigos emitidos", d.codigos.length, "acento"),
          indicador("Bits sin comprimir", d.bits_fijos), indicador("Bits con LZW", d.bits_lzw, d.bits_lzw < d.bits_fijos ? "ok" : "mal"),
          indicador("¿Se recupera igual?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")),
        idea("El diccionario <b>nunca se envía</b>: el decodificador lo reconstruye igual a partir de los códigos (compresión adaptativa). Se usa en GIF y TIFF."));
    });
    vaciar(raiz, tarjeta("Texto", campoTexto("TOBEORNOTTOBEORTOBEORNOT", ["TOBEORNOTTOBEORTOBEORNOT", "ABABABA", "abracadabra abracadabra"], cargar, 80)), res);
    cargar("TOBEORNOTTOBEORTOBEORNOT");
  },
});

// ======================= BWT =======================
SECCIONES.push({
  id: "bwt", grupo: 2, titulo: "Burrows-Wheeler: reordenar para juntar",
  bajada: "La BWT no comprime sola: reordena el texto para que las letras iguales queden juntas, y así RLE + Huffman comprimen mejor. Es la base de bzip2. Y se puede deshacer.",
  codigo: [["bwt", "transformar"], ["bwt", "inversa"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("bwt", { texto });
      reiniciarColores([...new Set(d.texto + "$")].sort().join(""));
      const grande = d.texto.length > 30;
      const tablaRot = (filas, { marcarFila = -1, ultima = false } = {}) => h("div", { clase: "desplazable" },
        h("table", { clase: "mono", estilo: { borderCollapse: "separate", borderSpacing: "2px", fontSize: grande ? "11px" : "15px" } },
          filas.map((r, i) => h("tr", {}, [...r].map((c, j) => h("td", {
            estilo: {
              width: grande ? "14px" : "24px", height: grande ? "16px" : "26px", textAlign: "center", borderRadius: "4px",
              background: ultima && j === r.length - 1 ? colorDe(c) : i === marcarFila ? css("--acento-suave") : css("--panel-2"),
              color: ultima && j === r.length - 1 ? "#fff" : null, fontWeight: ultima && j === r.length - 1 ? 700 : null,
            },
          }, vis(c)))))));
      const etapas = ["Agregar $", "Rotaciones", "Ordenar", "Última columna", "Resultado"];
      const zona = h("div");
      const pintar = (k) => {
        let cuerpo, exp;
        if (k === 0) { exp = "Se agrega «$» al final para marcar dónde termina el texto (así se podrá deshacer)."; cuerpo = h("div", { clase: "celdas" }, [...(d.texto + "$")].map((c) => h("div", { clase: "celda" }, vis(c)))); }
        if (k === 1) { exp = "Se escriben TODAS las rotaciones: cada fila es el texto empezando en otra posición."; cuerpo = tablaRot(d.rotaciones); }
        if (k === 2) { exp = "Se ordenan alfabéticamente. Las rotaciones que empiezan igual (mismo contexto) quedan juntas. La fila azul es el texto original."; cuerpo = tablaRot(d.ordenadas, { marcarFila: d.fila_original }); }
        if (k === 3) { exp = "La salida es la ÚLTIMA COLUMNA: la letra que va justo antes de cada contexto. Como los contextos iguales quedaron juntos, las letras de esta columna tienden a repetirse."; cuerpo = tablaRot(d.ordenadas, { marcarFila: d.fila_original, ultima: true }); }
        if (k === 4) {
          exp = "¡Las letras iguales quedaron juntas! Ahora RLE encuentra menos rachas y move-to-front produce muchos ceros, que Huffman comprime muy bien.";
          cuerpo = h("div", {},
            h("div", { clase: "nota" }, "Original:"), h("div", { clase: "celdas" }, [...d.texto].map((c) => h("div", { clase: "celda", estilo: { background: tenue(colorDe(c), .3) } }, vis(c)))),
            h("div", { clase: "nota", estilo: { marginTop: "10px" } }, "BWT:"), h("div", { clase: "celdas" }, [...d.salida].map((c) => h("div", { clase: "celda", estilo: { background: tenue(colorDe(c), .3) } }, vis(c)))),
            h("div", { clase: "nota", estilo: { marginTop: "10px" } }, "Move-to-front de la BWT (los 0 = «la misma letra que antes»):"),
            h("div", { clase: "tokens" }, d.mtf.map((v) => h("span", { clase: "token" + (v === 0 ? " ref" : "") }, v))),
            h("div", { clase: "indicadores", estilo: { marginTop: "10px" } }, indicador("Rachas RLE antes", d.rachas_antes), indicador("Rachas RLE después", d.rachas_despues, "ok"), indicador("¿La inversa recupera el texto?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")));
        }
        vaciar(zona, h("div", { clase: "etapas" }, etapas.map((e, i) => h("span", { clase: i === k ? "activa" : "" }, `${i + 1}. ${e}`))),
          h("div", { clase: "explicacion" }, exp), cuerpo);
      };
      vaciar(res, tarjeta("Paso a paso", reproductor(etapas.length, pintar, { intervalo: 2200 }), zona),
        idea(`BWT(«${d.texto}») = <b>${d.salida}</b>`));
    });
    vaciar(raiz, tarjeta("Texto", campoTexto("BANANA", ["BANANA", "MISSISSIPPI", "tres tristes tigres", "abracadabra"], cargar, 60)), res);
    cargar("BANANA");
  },
});

// ======================= ARITMÉTICA =======================
SECCIONES.push({
  id: "aritmetica", grupo: 2, titulo: "Codificación aritmética: un mensaje = un número",
  bajada: "Se parte del intervalo [0, 1), dividido según la probabilidad de cada símbolo. Cada símbolo hace «zoom» dentro de su tramo. Al final, cualquier número dentro del intervalo identifica todo el mensaje.",
  codigo: [["aritmetica", "codificar"], ["aritmetica", "decodificar"]],
  render(raiz) {
    const res = h("div");
    const cargar = (texto) => conCarga(res, async () => {
      const d = await api("aritmetica", { texto });
      reiniciarColores(d.tramos.map((t) => t.s).join(""));
      const zona = h("div");
      const W = 820, fila = 74, m = 20;
      const pintar = (k) => {
        const n = k + 1;
        const g = s("svg", { viewBox: `0 0 ${W} ${n * fila + 30}`, width: W });
        for (let r = 0; r < n; r++) {
          const p = d.pasos[r], y = 10 + r * fila, alto = 30;
          const a = p.antes[0].v, b = p.antes[1].v, ancho = b - a;
          for (const t of d.tramos) {
            const x1 = m + t.ini.v * (W - 2 * m), x2 = m + t.fin.v * (W - 2 * m);
            const elegido = t.s === p.s;
            g.appendChild(s("rect", { x: x1, y, width: Math.max(1, x2 - x1 - 1), height: alto, rx: 4, fill: elegido ? colorDe(t.s) : tenue(colorDe(t.s), .2), stroke: elegido ? css("--texto") : "none", "stroke-width": elegido ? 2 : 0 }));
            if (x2 - x1 > 18) g.appendChild(s("text", { x: (x1 + x2) / 2, y: y + 20, "text-anchor": "middle", "font-size": 14, "font-weight": 700, fill: elegido ? "#fff" : null, texto: vis(t.s) }));
          }
          g.appendChild(s("text", { x: m, y: y + alto + 13, "font-size": 11, fill: css("--suave"), texto: p.antes[0].t }));
          g.appendChild(s("text", { x: W - m, y: y + alto + 13, "font-size": 11, "text-anchor": "end", fill: css("--suave"), texto: p.antes[1].t }));
          if (r < n - 1 || true) {
            const t = d.tramos.find((x) => x.s === p.s);
            const x1 = m + t.ini.v * (W - 2 * m), x2 = m + t.fin.v * (W - 2 * m);
            if (r < n - 1) g.appendChild(s("path", { d: `M${x1},${y + alto} L${m},${y + fila} L${W - m},${y + fila} L${x2},${y + alto} Z`, fill: tenue(colorDe(p.s), .12) }));
          }
        }
        const p = d.pasos[k];
        vaciar(zona,
          h("div", { clase: "explicacion" }, h("b", {}, `Lee «${vis(p.s)}»: `), `el intervalo [${p.antes[0].t}, ${p.antes[1].t}) se divide en las mismas proporciones y se hace zoom en el tramo de «${vis(p.s)}» → `, h("b", {}, `[${p.despues[0].t}, ${p.despues[1].t})`), ` (ancho ≈ ${(p.despues[1].v - p.despues[0].v).toPrecision(3)}).`),
          h("div", { clase: "nota" }, "Cada fila es el intervalo actual ampliado a todo el ancho:"),
          h("div", { clase: "desplazable" }, g));
      };
      vaciar(res,
        tarjeta("Tramos iniciales (según la probabilidad de cada símbolo)",
          h("div", { clase: "tokens" }, d.tramos.map((t) => h("span", { clase: "token", estilo: { borderColor: colorDe(t.s), background: tenue(colorDe(t.s), .2) } }, h("b", {}, vis(t.s)), ` → [${t.ini.t}, ${t.fin.t})`)))),
        tarjeta("Zoom símbolo a símbolo", reproductor(d.pasos.length, pintar, { intervalo: 1500 }), zona),
        tarjeta("Resultado",
          idea(`Número elegido: <b class="mono">0.${d.bits}</b> en binario = <b>${d.numero.t}</b> — es el número con menos dígitos binarios dentro del intervalo final.`),
          h("div", { clase: "indicadores" },
            indicador("Aritmética", d.bits.length + " bits", "acento"),
            indicador("Huffman", d.huffman_bits + " bits"),
            indicador("Límite de Shannon", fmt(d.entropia_bits, 1) + " bits", "ok"),
            indicador("¿Se decodifica bien?", d.ok ? "Sí ✓" : "No", d.ok ? "ok" : "mal")),
          idea("Huffman usa un número <b>entero</b> de bits por símbolo (mínimo 1). La aritmética usa «fracciones de bit» y se acerca más al límite. Pruebe «AAAAAAAAAB»: Huffman necesita 10 bits.", "ok")));
    });
    vaciar(raiz, tarjeta("Mensaje (corto)", campoTexto("AABAC", ["AABAC", "AAAAAAAAAB", "ABRACADABRA", "HOLA"], cargar, 24)), res);
    cargar("AABAC");
  },
});
