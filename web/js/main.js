/* Navegación: menú lateral, ruta de la presentación y tema claro/oscuro */

const GRUPOS = ["1 · Contexto", "2 · Clasificación", "3 · Sin pérdida", "4 · Con pérdida", "5 · Aplicaciones"];
const ORDEN = ["inicio", "entropia", "adaptativa", "rle", "huffman", "lz77", "lzw", "bwt", "aritmetica",
  "jpeg", "audio", "video", "heap", "archivo"];

SECCIONES.push({
  id: "inicio", grupo: -1, titulo: "¿Cómo cabe todo?",
  bajada: "Compresión de datos: menos bits, la misma información. Cada sección ejecuta el código Python del proyecto y muestra, paso a paso, lo que hace el algoritmo.",
  render(raiz) {
    const tarjetas = ORDEN.slice(1).map((id) => {
      const sec = SECCIONES.find((x) => x.id === id);
      return h("button", { clase: "tarjeta", estilo: { textAlign: "left", cursor: "pointer", margin: 0 }, onclick: () => ir(id) },
        h("div", { clase: "etiqueta" }, GRUPOS[sec.grupo]), h("h3", { estilo: { margin: "4px 0" } }, sec.titulo),
        h("div", { clase: "nota" }, sec.bajada.length > 130 ? sec.bajada.slice(0, 128) + "…" : sec.bajada));
    });
    vaciar(raiz,
      tarjeta("Cómo usar esta página",
        h("ul", {},
          h("li", {}, "Elija un tema en el menú (están en el mismo orden de la presentación)."),
          h("li", {}, "Cambie el texto o los controles: el servidor Python vuelve a calcular todo al instante."),
          h("li", {}, "Use el reproductor ", h("b", {}, "⏮ ◀ ▶ Reproducir ▶ ⏭"), " para avanzar paso a paso y leer qué está haciendo el algoritmo."),
          h("li", {}, "Abra «🐍 Ver el código Python» al final de cada sección para ver la función real que lo hace."))),
      h("div", { clase: "rejilla" }, tarjetas));
  },
});

let actual = null;
function ir(id) {
  if (!SECCIONES.find((x) => x.id === id)) id = "inicio";
  if (location.hash.slice(1) !== id) history.replaceState(null, "", "#" + id);
  actual = id;
  const sec = SECCIONES.find((x) => x.id === id);
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("activo", b.dataset.id === id));
  const ruta = document.getElementById("ruta");
  vaciar(ruta, GRUPOS.map((g, i) => h("span", { clase: i === sec.grupo ? "actual" : i < sec.grupo ? "hecho" : "" }, (i < sec.grupo ? "✓ " : "") + g)));
  const cuerpo = h("div");
  const k = ORDEN.indexOf(id);
  const siguiente = ORDEN[k + 1], anterior = ORDEN[k - 1];
  vaciar(document.getElementById("contenido"),
    h("div", { clase: "encabezado" }, h("div", {},
      sec.grupo >= 0 ? h("div", { clase: "etiqueta" }, GRUPOS[sec.grupo]) : null,
      h("h2", {}, sec.titulo), h("p", { clase: "bajada" }, sec.bajada))),
    cuerpo,
    sec.codigo ? tarjeta(null, verCodigo(sec.codigo)) : null,
    h("div", { clase: "fila", estilo: { justifyContent: "space-between", marginTop: "10px" } },
      anterior ? h("button", { clase: "boton", onclick: () => ir(anterior) }, "← " + SECCIONES.find((x) => x.id === anterior).titulo) : h("span"),
      siguiente ? h("button", { clase: "boton primario", onclick: () => ir(siguiente) }, SECCIONES.find((x) => x.id === siguiente).titulo + " →") : h("span")));
  window.scrollTo(0, 0);
  sec.render(cuerpo);
}

function construirMenu() {
  const nav = document.getElementById("menu");
  let grupo = null, n = 0;
  for (const id of ORDEN) {
    const sec = SECCIONES.find((x) => x.id === id);
    if (sec.grupo !== grupo && sec.grupo >= 0) { grupo = sec.grupo; nav.appendChild(h("div", { clase: "grupo" }, GRUPOS[grupo])); }
    nav.appendChild(h("button", { clase: "nav-item", "data-id": id, onclick: () => ir(id) },
      h("span", { clase: "num" }, id === "inicio" ? "★" : ++n), sec.id === "inicio" ? "Inicio" : sec.titulo));
  }
}

function tema(nuevo) {
  document.documentElement.dataset.tema = nuevo;
  try { localStorage.setItem("tema", nuevo); } catch (e) { /* sin almacenamiento */ }
  document.getElementById("boton-tema").textContent = nuevo === "oscuro" ? "☀️ Tema claro" : "🌙 Tema oscuro";
}

window.addEventListener("DOMContentLoaded", () => {
  let guardado = null;
  try { guardado = localStorage.getItem("tema"); } catch (e) { /* nada */ }
  tema(guardado || "claro");
  document.getElementById("boton-tema").onclick = () => { tema(document.documentElement.dataset.tema === "oscuro" ? "claro" : "oscuro"); if (actual) ir(actual); };
  construirMenu();
  ir(location.hash.slice(1) || "inicio");
  window.addEventListener("hashchange", () => { if (location.hash.slice(1) !== actual) ir(location.hash.slice(1)); });
});
