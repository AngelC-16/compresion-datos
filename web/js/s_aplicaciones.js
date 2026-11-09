/* 5 · Aplicaciones: compresor real de archivos */

SECCIONES.push({
  id: "archivo", grupo: 4, titulo: "Ejemplo práctico: comprimir un archivo de verdad",
  bajada: "Nuestro Huffman y nuestro mini-DEFLATE (LZ77 + Huffman, la misma idea del ZIP) contra los compresores profesionales. Todos se verifican: el archivo debe volver idéntico, bit por bit.",
  codigo: [["archivo", "comprimir_deflate"], ["archivo", "comprimir_huffman"], ["archivo", "EscritorBits"]],
  render(raiz) {
    const res = h("div");
    const cargar = (parametros) => conCarga(res, async () => {
      const d = await api("archivo", parametros);
      const filas = d.filas;
      const limitePct = d.tamano ? 100 * d.limite / d.tamano : 0;
      const descargar = h("button", {
        clase: "boton primario", onclick: () => {
          const bin = Uint8Array.from(atob(d.edd), (c) => c.charCodeAt(0));
          const a = h("a", { href: URL.createObjectURL(new Blob([bin])), download: d.nombre + ".edd" });
          document.body.appendChild(a); a.click(); a.remove();
        },
      }, "⬇ Descargar comprimido (.edd)");
      vaciar(res,
        h("div", { clase: "indicadores" },
          indicador("Archivo", d.nombre),
          indicador("Tamaño original", ent(d.tamano) + " bytes"),
          indicador("Entropía (orden 0)", fmt(d.entropia, 3) + " bits/byte", "acento"),
          indicador("Límite para Huffman", ent(d.limite) + " bytes", "ok")),
        tarjeta("Tamaño final (% del original) — más corto es mejor",
          h("div", { clase: "desplazable" }, barrasH(filas.map((f) => ({
            etiqueta: f.metodo, valor: f.pct, texto: `${fmt(f.pct, 1)} %  (${ent(f.bytes)} B)`,
            color: f.propio ? (f.pct > 100 ? css("--mal") : css("--acento")) : css("--suave"),
          })), { ancho: 860, etiquetaAncho: 290, max: Math.max(100, ...filas.map((f) => f.pct)), marca: { valor: limitePct, texto: "límite de la entropía de orden 0" } })),
          h("p", { clase: "nota" }, "Azul = implementado por nosotros · gris = profesionales (zlib, bz2, lzma) · línea roja = lo mínimo que puede lograr un compresor que solo mira la frecuencia de cada byte.")),
        tarjeta("Detalle",
          h("div", { clase: "desplazable" }, h("table", { clase: "datos" },
            h("thead", {}, h("tr", {}, h("th", {}, "método"), h("th", {}, "bytes"), h("th", {}, "% orig."), h("th", {}, "tiempo"), h("th", {}, "¿idéntico al descomprimir?"))),
            h("tbody", {}, filas.map((f) => h("tr", { clase: f.propio ? "resaltada" : "" },
              h("td", {}, f.metodo), h("td", { clase: "num" }, ent(f.bytes)), h("td", { clase: "num" }, fmt(f.pct, 1) + " %"),
              h("td", { clase: "num" }, fmt(f.segundos * 1000, 1) + " ms"), h("td", {}, f.ok ? "✅ sí" : "❌ no")))))),
          h("div", { estilo: { marginTop: "12px" } }, descargar),
          idea("<b>Lectura:</b> RLE agranda un texto (no hay rachas: «la trampa»). Huffman queda cerca de la línea roja pero no puede bajarla. LZ77 + Huffman <b>sí</b> la baja porque aprovecha palabras repetidas. Los profesionales ganan con búsquedas más inteligentes, bloques y codificación aritmética.")),
        tarjeta("Los bytes más frecuentes y su código Huffman",
          h("div", { clase: "desplazable" }, h("table", { clase: "datos" },
            h("thead", {}, h("tr", {}, h("th", {}, "byte"), h("th", {}, "carácter"), h("th", {}, "veces"), h("th", {}, "bits en ASCII"), h("th", {}, "bits con Huffman"))),
            h("tbody", {}, d.top.map((t) => h("tr", {}, h("td", { clase: "num" }, t.byte), h("td", { clase: "mono" }, t.car === null ? "·" : vis(t.car)),
              h("td", { clase: "num" }, ent(t.veces)), h("td", { clase: "num" }, 8), h("td", { clase: "num" }, h("b", { estilo: { color: css("--ok") } }, t.bits))))))),
          h("p", { clase: "nota" }, "Lo más frecuente (el espacio, la «e», la «a»…) se guarda con menos de 8 bits; lo raro, con más.")));
    });
    const entrada = h("input", { type: "file", estilo: { display: "none" } });
    const zona = h("div", { clase: "zona-archivo" }, "📂 Arrastre aquí cualquier archivo (máx. 400 KB) o haga clic para elegirlo");
    const leer = (f) => {
      if (!f) return;
      const lector = new FileReader();
      lector.onload = () => cargar({ nombre: f.name, datos: lector.result.split(",")[1] || "" });
      lector.readAsDataURL(f);
    };
    zona.onclick = () => entrada.click();
    entrada.onchange = () => leer(entrada.files[0]);
    zona.ondragover = (e) => { e.preventDefault(); zona.classList.add("encima"); };
    zona.ondragleave = () => zona.classList.remove("encima");
    zona.ondrop = (e) => { e.preventDefault(); zona.classList.remove("encima"); leer(e.dataTransfer.files[0]); };
    vaciar(raiz,
      tarjeta("Archivo a comprimir", zona, entrada,
        h("div", { clase: "fila", estilo: { marginTop: "10px" } }, h("button", { clase: "boton", onclick: () => cargar({}) }, "Usar el guion de la exposición (guion.txt)"))),
      res,
      tarjeta("Qué hay debajo",
        h("div", { clase: "indicadores" },
          indicador("Árbol binario", "Huffman"),
          indicador("Cola de prioridad", "O(log n)"),
          indicador("Tabla hash", "LZ77 · O(1)")),
        h("p", { clase: "nota" }, "El formato .edd guarda: firma «EDD2», método, tamaño original, la LONGITUD del código de cada símbolo (gracias a los códigos canónicos no hace falta guardar el árbol) y los bits.")));
    cargar({});
  },
});
