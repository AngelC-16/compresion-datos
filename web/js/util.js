/* ============================================================
   Utilidades de la interfaz: llamadas al servidor Python,
   creación de elementos, gráficas SVG, árboles y reproductor
   de pasos. (Los algoritmos NO están aquí: los ejecuta Python.)
   ============================================================ */

// ---------- llamar a la API de Python ----------
async function api(ruta, parametros = {}) {
  const r = await fetch("/api/" + ruta, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(parametros),
  });
  const datos = await r.json();
  if (!r.ok) throw new Error(datos.error || "Error en el servidor");
  return datos;
}

// ---------- crear elementos HTML ----------
function h(etiqueta, atributos = {}, ...hijos) {
  const el = document.createElement(etiqueta);
  for (const [k, v] of Object.entries(atributos || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "clase") el.className = v;
    else if (k === "estilo") Object.assign(el.style, v);
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  agregar(el, hijos);
  return el;
}
function agregar(el, hijos) {
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo === null || hijo === undefined || hijo === false) continue;
    el.appendChild(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
}
function vaciar(el, ...hijos) { el.innerHTML = ""; return agregar(el, hijos); }

const NS = "http://www.w3.org/2000/svg";
function s(etiqueta, atributos = {}, ...hijos) {
  const el = document.createElementNS(NS, etiqueta);
  for (const [k, v] of Object.entries(atributos || {})) {
    if (v === undefined || v === null) continue;
    if (k === "texto") el.textContent = v;
    else el.setAttribute(k, v);
  }
  for (const hijo of hijos.flat(Infinity)) if (hijo) el.appendChild(hijo);
  return el;
}

// ---------- formato ----------
const fmt = (x, d = 2) => Number(x).toLocaleString("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d });
const ent = (x) => Number(x).toLocaleString("es-CO", { maximumFractionDigits: 0 });
const vis = (c) => (c === " " ? "␣" : c === "\n" ? "↵" : c === "\t" ? "⇥" : c);
const css = (nombre) => getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();

// Color fijo por símbolo (el mismo en todas las secciones)
const PALETA = ["#4c6ef5", "#f08c00", "#2b9348", "#d6336c", "#7048e8", "#0c8599", "#e8590c",
  "#5c940d", "#c2255c", "#1971c2", "#ae3ec9", "#087f5b", "#f59f00", "#495057"];
const _colores = new Map();
function colorDe(simbolo) {
  if (!_colores.has(simbolo)) _colores.set(simbolo, PALETA[_colores.size % PALETA.length]);
  return _colores.get(simbolo);
}
function reiniciarColores(textoOrden) {
  _colores.clear();
  for (const c of textoOrden) colorDe(c);
}
const tenue = (hex, a = 0.18) => {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
};

// ---------- piezas de interfaz ----------
function tarjeta(titulo, ...contenido) {
  return h("div", { clase: "tarjeta" }, titulo ? h("h3", {}, titulo) : null, ...contenido);
}
function indicador(nombre, valor, tipo = "") {
  return h("div", { clase: "indicador " + tipo }, h("div", { clase: "valor" }, valor), h("div", { clase: "nombre" }, nombre));
}
function idea(texto, tipo = "") { return h("div", { clase: "idea " + tipo, html: texto }); }

function deslizador(etiqueta, { min, max, paso = 1, valor, formato = (v) => v, alCambiar, retardo = 0 }) {
  const salida = h("output", {}, formato(valor));
  let reloj;
  const entrada = h("input", { type: "range", min, max, step: paso, value: valor });
  entrada.addEventListener("input", () => {
    salida.textContent = formato(Number(entrada.value));
    clearTimeout(reloj);
    reloj = setTimeout(() => alCambiar(Number(entrada.value)), retardo);
  });
  return h("div", { clase: "deslizador" }, h("label", {}, etiqueta), entrada, salida);
}

/** Campo de texto + ejemplos rápidos. Llama a alCambiar(texto) (con pausa). */
function campoTexto(valor, ejemplos, alCambiar, max = 400) {
  const entrada = h("input", { type: "text", value: valor, maxlength: max, spellcheck: "false" });
  let reloj;
  entrada.addEventListener("input", () => { clearTimeout(reloj); reloj = setTimeout(() => alCambiar(entrada.value), 350); });
  const chips = ejemplos.map((e) => h("button", { clase: "chip", onclick: () => { entrada.value = e; alCambiar(e); } },
    e.length > 26 ? e.slice(0, 24) + "…" : e));
  return h("div", {}, h("div", { clase: "fila" }, entrada), h("div", { clase: "fila", estilo: { marginTop: "8px" } }, h("span", { clase: "nota" }, "Ejemplos:"), chips));
}

/** Reproductor de pasos: ⏮ ◀ ▶/⏸ ▶ ⏭ + barra. dibujar(i) pinta el paso i. */
function reproductor(total, dibujar, { intervalo = 1100, inicial = 0 } = {}) {
  let i = inicial, reloj = null;
  const contador = h("span", { clase: "contador" });
  const barra = h("input", { type: "range", min: 0, max: Math.max(0, total - 1), value: i });
  const bPlay = h("button", { clase: "boton primario", title: "Reproducir / pausar" }, "▶ Reproducir");
  const ir = (n) => {
    i = Math.max(0, Math.min(total - 1, n));
    barra.value = i;
    contador.textContent = `paso ${i + 1} / ${total}`;
    dibujar(i);
  };
  const parar = () => { clearInterval(reloj); reloj = null; bPlay.textContent = "▶ Reproducir"; };
  bPlay.onclick = () => {
    if (reloj) return parar();
    if (i >= total - 1) ir(0);
    bPlay.textContent = "⏸ Pausar";
    reloj = setInterval(() => { if (i >= total - 1) parar(); else ir(i + 1); }, intervalo);
  };
  barra.oninput = () => { parar(); ir(Number(barra.value)); };
  const el = h("div", { clase: "reproductor" },
    h("button", { clase: "boton", title: "Primer paso", onclick: () => { parar(); ir(0); } }, "⏮"),
    h("button", { clase: "boton", title: "Paso anterior", onclick: () => { parar(); ir(i - 1); } }, "◀"),
    bPlay,
    h("button", { clase: "boton", title: "Paso siguiente", onclick: () => { parar(); ir(i + 1); } }, "▶"),
    h("button", { clase: "boton", title: "Último paso", onclick: () => { parar(); ir(total - 1); } }, "⏭"),
    barra, contador);
  el._ir = ir; el._parar = parar;
  setTimeout(() => ir(i), 0);
  return el;
}

/** Botón «Ver el código Python» que trae el código REAL desde el servidor. */
function verCodigo(lista) {
  const cont = h("div");
  const det = h("details", { clase: "codigo" }, h("summary", {}, "🐍 Ver el código Python que hace esto"), cont);
  det.addEventListener("toggle", async () => {
    if (!det.open || cont.childNodes.length) return;
    for (const [modulo, funcion] of lista) {
      try {
        const r = await api("codigo", { modulo, funcion });
        agregar(cont, [h("div", { clase: "fuente-titulo" }, `${r.archivo} → ${funcion}`), h("pre", { clase: "fuente", html: resaltar(r.codigo) })]);
      } catch (e) { agregar(cont, [h("div", { clase: "error" }, e.message)]); }
    }
  });
  return det;
}
function resaltar(codigo) {
  const esc = codigo.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return esc.replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(#.*)|\b(def|class|return|for|while|if|elif|else|in|not|and|or|import|from|as|with|try|except|raise|break|continue|None|True|False|lambda|yield|is|pass)\b/g,
    (m, str, com, kw) => str ? `<span class="str">${str}</span>` : com ? `<span class="com">${com}</span>` : `<span class="kw">${kw}</span>`);
}

// ---------- gráficas SVG ----------
/** Barras horizontales: [{etiqueta, valor, color, texto}] */
function barrasH(datos, { ancho = 640, alto_barra = 30, max = null, etiquetaAncho = 220, marca = null } = {}) {
  const tope = max ?? Math.max(...datos.map((d) => d.valor), 1e-9);
  const util = ancho - etiquetaAncho - 190;
  const alto = datos.length * (alto_barra + 10) + 10;
  const g = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho });
  datos.forEach((d, k) => {
    const y = 6 + k * (alto_barra + 10);
    const w = Math.max(2, (d.valor / tope) * util);
    g.appendChild(s("text", { x: etiquetaAncho - 10, y: y + alto_barra / 2 + 5, "text-anchor": "end", "font-size": 13, texto: d.etiqueta }));
    g.appendChild(s("rect", { x: etiquetaAncho, y, width: util, height: alto_barra, rx: 6, fill: css("--panel-2") }));
    g.appendChild(s("rect", { x: etiquetaAncho, y, width: w, height: alto_barra, rx: 6, fill: d.color || css("--acento") }));
    g.appendChild(s("text", { x: etiquetaAncho + Math.min(w, util) + 8, y: y + alto_barra / 2 + 5, "font-size": 13, "font-weight": 600, texto: d.texto ?? fmt(d.valor) }));
  });
  if (marca) {
    const x = etiquetaAncho + (marca.valor / tope) * util;
    g.appendChild(s("line", { x1: x, x2: x, y1: 0, y2: alto, stroke: css("--mal"), "stroke-width": 2, "stroke-dasharray": "5 4" }));
    g.appendChild(s("text", { x: x + 4, y: alto - 2, "font-size": 11, fill: css("--mal"), texto: marca.texto }));
  }
  return g;
}

/** Gráfica de líneas: series [{nombre, valores, color}] */
function lineas(series, { ancho = 760, alto = 260, ymax = null, ymin = 0, etiquetaY = "", marcaX = null, pasos = false } = {}) {
  const m = { izq: 46, der: 14, arr: 14, aba: 30 };
  const n = Math.max(...series.map((se) => se.valores.length));
  const top = ymax ?? Math.max(...series.flatMap((se) => se.valores), 1e-9) * 1.08;
  const X = (i) => m.izq + (n <= 1 ? 0 : (i / (n - 1)) * (ancho - m.izq - m.der));
  const Y = (v) => alto - m.aba - ((v - ymin) / (top - ymin)) * (alto - m.arr - m.aba);
  const g = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho });
  for (let t = 0; t <= 4; t++) {
    const v = ymin + ((top - ymin) * t) / 4, y = Y(v);
    g.appendChild(s("line", { x1: m.izq, x2: ancho - m.der, y1: y, y2: y, stroke: css("--borde") }));
    g.appendChild(s("text", { x: m.izq - 6, y: y + 4, "text-anchor": "end", "font-size": 11, fill: css("--suave"), texto: fmt(v, v < 10 ? 1 : 0) }));
  }
  if (etiquetaY) g.appendChild(s("text", { x: 4, y: 10, "font-size": 11, fill: css("--suave"), texto: etiquetaY }));
  if (marcaX !== null && marcaX !== undefined) {
    g.appendChild(s("line", { x1: X(marcaX), x2: X(marcaX), y1: m.arr, y2: alto - m.aba, stroke: css("--acento"), "stroke-width": 2, "stroke-dasharray": "4 3" }));
  }
  for (const se of series) {
    let d = "";
    se.valores.forEach((v, i) => {
      if (pasos && i > 0) d += `L${X(i)},${Y(se.valores[i - 1])}`;
      d += `${i ? "L" : "M"}${X(i)},${Y(v)}`;
    });
    g.appendChild(s("path", { d, fill: "none", stroke: se.color, "stroke-width": se.grosor || 2.4, "stroke-linejoin": "round", "stroke-dasharray": se.guiones || null }));
  }
  const ley = s("g", {});
  let lx = m.izq + 6;
  for (const se of series) {
    ley.appendChild(s("rect", { x: lx, y: alto - 14, width: 14, height: 4, fill: se.color, rx: 2 }));
    ley.appendChild(s("text", { x: lx + 18, y: alto - 9, "font-size": 11.5, texto: se.nombre }));
    lx += 30 + se.nombre.length * 6.4;
  }
  g.appendChild(ley);
  return g;
}

// ---------- árboles binarios ----------
/** Calcula posiciones (x por orden de hojas, y por profundidad) de un árbol {nodos, raiz}. */
function disponerArbol(nodos, raiz) {
  const pos = {};
  let hoja = 0, profMax = 0;
  (function rec(id, prof) {
    const n = nodos[id];
    profMax = Math.max(profMax, prof);
    const hijos = [n.izq, n.der].filter((x) => x !== null && x !== undefined);
    if (!hijos.length) { pos[id] = { x: hoja++, y: prof }; return; }
    hijos.forEach((c) => rec(c, prof + 1));
    pos[id] = { x: hijos.reduce((a, c) => a + pos[c].x, 0) / hijos.length, y: prof };
  })(raiz, 0);
  return { pos, hojas: hoja, prof: profMax };
}

/**
 * Dibuja un bosque (lista de raíces) de árboles de Huffman.
 * opciones: resaltar (Set de ids), nuevo (id), codigos (mostrar 0/1), ancho
 */
function dibujarBosque(nodos, raices, { resaltar = new Set(), nuevo = null, anchoHoja = 58, altoNivel = 70, mostrarBits = true } = {}) {
  const arboles = raices.map((r) => ({ r, ...disponerArbol(nodos, r) }));
  const totalHojas = arboles.reduce((a, t) => a + t.hojas, 0) + (arboles.length - 1) * 0.6;
  const prof = Math.max(...arboles.map((t) => t.prof));
  const ancho = Math.max(240, totalHojas * anchoHoja + 30);
  const alto = (prof + 1) * altoNivel + 30;
  const g = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho, height: alto });
  let desplaz = 0;
  const acento = css("--acento"), ok = css("--ok"), borde = css("--suave"), panel = css("--panel");
  for (const t of arboles) {
    const P = (id) => ({ x: 15 + (desplaz + t.pos[id].x + 0.5) * anchoHoja, y: 26 + t.pos[id].y * altoNivel });
    const lineasG = s("g"), nodosG = s("g");
    for (const id of Object.keys(t.pos)) {
      const n = nodos[id], p = P(id);
      [["izq", "0"], ["der", "1"]].forEach(([lado, bit]) => {
        const c = n[lado];
        if (c === null || c === undefined) return;
        const q = P(c);
        const marcado = resaltar.has(Number(id)) || Number(id) === nuevo;
        lineasG.appendChild(s("line", { x1: p.x, y1: p.y, x2: q.x, y2: q.y, stroke: marcado ? acento : borde, "stroke-width": marcado ? 2.5 : 1.5 }));
        if (mostrarBits) {
          const mx = (p.x + q.x) / 2 + (bit === "0" ? -9 : 9), my = (p.y + q.y) / 2;
          lineasG.appendChild(s("text", { x: mx, y: my, "text-anchor": "middle", "font-size": 12, "font-weight": 700, fill: bit === "0" ? "#4c6ef5" : "#f08c00", texto: bit }));
        }
      });
      const esHoja = n.s !== null && n.s !== undefined;
      const color = Number(id) === nuevo ? ok : resaltar.has(Number(id)) ? acento : null;
      if (esHoja) {
        const c = colorDe(n.s);
        nodosG.appendChild(s("rect", { x: p.x - 21, y: p.y - 17, width: 42, height: 34, rx: 8, fill: panel }));
        nodosG.appendChild(s("rect", { x: p.x - 21, y: p.y - 17, width: 42, height: 34, rx: 8, fill: tenue(c, 0.22), stroke: color || c, "stroke-width": color ? 3 : 1.5 }));
        nodosG.appendChild(s("text", { x: p.x, y: p.y - 1, "text-anchor": "middle", "font-size": 15, "font-weight": 700, texto: vis(n.s) }));
        nodosG.appendChild(s("text", { x: p.x, y: p.y + 12, "text-anchor": "middle", "font-size": 10.5, fill: css("--suave"), texto: n.f }));
      } else {
        nodosG.appendChild(s("circle", { cx: p.x, cy: p.y, r: 16, fill: panel }));
        nodosG.appendChild(s("circle", { cx: p.x, cy: p.y, r: 16, fill: color ? tenue(color, 0.25) : panel, stroke: color || borde, "stroke-width": color ? 3 : 1.5 }));
        nodosG.appendChild(s("text", { x: p.x, y: p.y + 5, "text-anchor": "middle", "font-size": 13, "font-weight": 600, texto: n.f }));
      }
    }
    g.appendChild(lineasG); g.appendChild(nodosG);
    desplaz += t.hojas + 0.6;
  }
  return g;
}

/** Árbol del heap a partir del arreglo (posición i -> hijos 2i+1, 2i+2). */
function dibujarHeap(arreglo, { marcar = {}, ancho = 640 } = {}) {
  const n = arreglo.length;
  const niveles = Math.max(1, Math.floor(Math.log2(Math.max(1, n))) + 1);
  const alto = niveles * 72 + 20;
  const g = s("svg", { viewBox: `0 0 ${ancho} ${alto}`, width: ancho });
  const P = (i) => {
    const nivel = Math.floor(Math.log2(i + 1));
    const enNivel = i - (2 ** nivel - 1);
    const huecos = 2 ** nivel;
    return { x: ((enNivel + 0.5) / huecos) * ancho, y: 32 + nivel * 72 };
  };
  for (let i = 1; i < n; i++) {
    const a = P(i), b = P(Math.floor((i - 1) / 2));
    g.appendChild(s("line", { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: css("--borde"), "stroke-width": 2 }));
  }
  for (let i = 0; i < n; i++) {
    const p = P(i);
    const color = marcar[i];
    g.appendChild(s("circle", { cx: p.x, cy: p.y, r: 21, fill: css("--panel") }));
    g.appendChild(s("circle", { cx: p.x, cy: p.y, r: 21, fill: color ? tenue(color, 0.25) : css("--panel"), stroke: color || css("--suave"), "stroke-width": color ? 3.5 : 1.5 }));
    g.appendChild(s("text", { x: p.x, y: p.y + 5, "text-anchor": "middle", "font-size": 15, "font-weight": 700, texto: arreglo[i] }));
    g.appendChild(s("text", { x: p.x + 24, y: p.y - 14, "font-size": 10, fill: css("--suave"), texto: i }));
  }
  return g;
}

// ---------- matrices y lienzos ----------
/** Matriz 8x8 coloreada. modo: "gris" (0-255), "div" (±, azul/rojo), "cero" (resaltar ceros) */
function matriz8(M, { modo = "gris", max = null, grande = false, marcar = null } = {}) {
  const el = h("div", { clase: "matriz" + (grande ? " grande" : "") });
  const tope = max ?? Math.max(1, ...M.flat().map((v) => Math.abs(v)));
  M.forEach((fila, i) => fila.forEach((v, j) => {
    let fondo, color = css("--texto");
    if (modo === "gris") {
      const g = Math.max(0, Math.min(255, Math.round(v)));
      fondo = `rgb(${g},${g},${g})`; color = g > 130 ? "#111" : "#fff";
    } else if (v === 0 && modo === "cero") {
      fondo = css("--panel-2"); color = css("--suave");
    } else {
      const a = Math.min(1, Math.abs(v) / tope) * 0.85 + 0.08;
      fondo = v >= 0 ? `rgba(240,140,0,${a})` : `rgba(76,110,245,${a})`;
    }
    const celda = h("div", { estilo: { background: fondo, color }, title: `(${i},${j}) = ${v}` }, typeof v === "number" ? (Math.abs(v) >= 100 ? Math.round(v) : Math.round(v * 10) / 10) : v);
    if (marcar && marcar(i, j)) celda.style.outline = `2px solid ${css("--mal")}`;
    el.appendChild(celda);
  }));
  return el;
}

/** Pinta una imagen en grises (matriz) en un canvas, ampliada. */
function lienzoGris(M, escala = 4, { cuadricula = 0, alClic = null } = {}) {
  const alto = M.length, ancho = M[0].length;
  const c = h("canvas", { width: ancho * escala, height: alto * escala, clase: "pixelado" });
  const ctx = c.getContext("2d");
  const img = ctx.createImageData(ancho, alto);
  M.forEach((fila, y) => fila.forEach((v, x) => {
    const g = Math.max(0, Math.min(255, Math.round(v))), k = 4 * (y * ancho + x);
    img.data[k] = img.data[k + 1] = img.data[k + 2] = g; img.data[k + 3] = 255;
  }));
  const tmp = document.createElement("canvas");
  tmp.width = ancho; tmp.height = alto;
  tmp.getContext("2d").putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(tmp, 0, 0, ancho * escala, alto * escala);
  if (cuadricula) {
    ctx.strokeStyle = "rgba(255,80,80,.35)"; ctx.lineWidth = 1;
    for (let x = 0; x <= ancho; x += cuadricula) { ctx.beginPath(); ctx.moveTo(x * escala + .5, 0); ctx.lineTo(x * escala + .5, alto * escala); ctx.stroke(); }
    for (let y = 0; y <= alto; y += cuadricula) { ctx.beginPath(); ctx.moveTo(0, y * escala + .5); ctx.lineTo(ancho * escala, y * escala + .5); ctx.stroke(); }
  }
  if (alClic) {
    c.style.cursor = "crosshair";
    c.addEventListener("click", (e) => {
      const r = c.getBoundingClientRect();
      alClic(Math.floor(((e.clientX - r.left) / r.width) * ancho), Math.floor(((e.clientY - r.top) / r.height) * alto));
    });
  }
  return c;
}

/** Envuelve una carga asíncrona mostrando "cargando" y errores. */
async function conCarga(el, fn) {
  el.classList.add("cargando");
  try { await fn(); }
  catch (e) { agregar(el, [h("div", { clase: "error" }, "⚠ " + e.message)]); console.error(e); }
  finally { el.classList.remove("cargando"); }
}
