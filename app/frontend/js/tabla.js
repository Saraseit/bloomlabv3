// ============================================================
// BloomLab · Tabla con buscador, orden y filtros estilo Excel
//
// crearTablaInteractiva({
//   tabla, buscador, conteo, limpiar,   elementos del DOM
//   columnas: [{ clave, etiqueta, tipo, valor(fila), texto(fila), filtrable }],
//   pintarFila(fila) -> <tr>,
//   vacio: "mensaje sin filas", recordar: "clave-localStorage"
// })
// tipo: texto (lista de valores), numero (rango), fecha (rango)
// Devuelve { actualizar(filas) }
// Usa coincideBusqueda() de buscador.js si está cargado.
// ============================================================

function crearTablaInteractiva(op) {

    const columnas = op.columnas;
    let filas = [];
    let estado = { busqueda: "", orden: null, filtros: {} };

    // Lo último que se usó se recuerda en este navegador
    if (op.recordar) {
        try {
            const guardado = JSON.parse(localStorage.getItem(op.recordar) || "null");
            if (guardado) estado = { ...estado, orden: guardado.orden || null, filtros: guardado.filtros || {} };
        } catch (_) { /* sin almacenamiento */ }
    }

    function guardar() {
        if (!op.recordar) return;
        try {
            localStorage.setItem(op.recordar, JSON.stringify({ orden: estado.orden, filtros: estado.filtros }));
        } catch (_) { /* sin almacenamiento */ }
    }

    const col = clave => columnas.find(c => c.clave === clave);
    const valorDe = (c, f) => c.valor ? c.valor(f) : f[c.clave];
    const textoDe = (c, f) => {
        if (c.texto) return c.texto(f);
        const v = valorDe(c, f);
        return v == null || v === "" ? "(vacío)" : String(v);
    };

    function coincideTexto(textos, consulta) {
        if (typeof coincideBusqueda === "function") return coincideBusqueda(textos, consulta);
        const q = consulta.toLowerCase();
        return textos.join(" ").toLowerCase().includes(q);
    }

    function pasaFiltro(c, f, filtro) {
        if (!filtro) return true;
        if (c.tipo === "numero" || c.tipo === "fecha") {
            const v = valorDe(c, f);
            if (v == null || v === "") return filtro.min == null && filtro.max == null;
            const x = c.tipo === "numero" ? Number(v) : String(v).slice(0, 10);
            if (filtro.min != null && filtro.min !== "" && x < (c.tipo === "numero" ? Number(filtro.min) : filtro.min)) return false;
            if (filtro.max != null && filtro.max !== "" && x > (c.tipo === "numero" ? Number(filtro.max) : filtro.max)) return false;
            return true;
        }
        return filtro.valores.includes(textoDe(c, f));
    }

    function filasVisibles(excepto) {
        const q = estado.busqueda.trim();
        let r = filas.filter(f => {
            if (q && !coincideTexto(columnas.filter(c => c.filtrable !== false).map(c => textoDe(c, f)), q)) return false;
            return columnas.every(c => c.clave === excepto || pasaFiltro(c, f, estado.filtros[c.clave]));
        });
        if (estado.orden && excepto === undefined) {
            const c = col(estado.orden.clave);
            if (c) {
                const dir = estado.orden.dir === "desc" ? -1 : 1;
                r = [...r].sort((a, b) => {
                    let x = valorDe(c, a), y = valorDe(c, b);
                    const vx = x == null || x === "", vy = y == null || y === "";
                    if (vx && vy) return 0;
                    if (vx) return 1;          // vacíos siempre al final
                    if (vy) return -1;
                    if (c.tipo === "numero") return (Number(x) - Number(y)) * dir;
                    return String(x).localeCompare(String(y), "es", { numeric: true, sensitivity: "base" }) * dir;
                });
            }
        }
        return r;
    }

    // ── Pintar ─────────────────────────────────

    function pintar() {
        const tbody = op.tabla.querySelector("tbody");
        const visibles = filasVisibles();
        tbody.innerHTML = "";
        if (visibles.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${columnas.length}" class="tabla-vacia">${
                filas.length ? "Ninguna fila coincide con la búsqueda o los filtros." : (op.vacio || "Sin registros.")
            }</td></tr>`;
        } else {
            visibles.forEach(f => tbody.appendChild(op.pintarFila(f)));
        }
        const activos = Object.keys(estado.filtros).length + (estado.busqueda.trim() ? 1 : 0);
        if (op.conteo) {
            op.conteo.textContent = activos
                ? `${visibles.length} de ${filas.length}`
                : `${filas.length} en total`;
        }
        if (op.limpiar) op.limpiar.hidden = !activos && !estado.orden;
        pintarEncabezados();
    }

    function pintarEncabezados() {
        op.tabla.querySelectorAll("thead th").forEach((th, i) => {
            const c = columnas[i];
            if (!c || c.filtrable === false) return;
            const orden = estado.orden && estado.orden.clave === c.clave ? estado.orden.dir : null;
            const filtrado = !!estado.filtros[c.clave];
            th.classList.add("th-interactivo");
            th.setAttribute("aria-sort", orden === "asc" ? "ascending" : orden === "desc" ? "descending" : "none");
            th.innerHTML = `
                <button type="button" class="th-boton ${filtrado ? "th-filtrado" : ""}"
                        aria-haspopup="dialog" aria-label="Ordenar y filtrar ${c.etiqueta}">
                    <span>${c.etiqueta}</span>
                    <span class="th-indicador">${orden === "asc" ? "▲" : orden === "desc" ? "▼" : ""}</span>
                    <span class="th-embudo" aria-hidden="true">${filtrado ? "⏷●" : "⏷"}</span>
                </button>`;
            th.querySelector("button").addEventListener("click", e => {
                e.stopPropagation();
                abrirPanel(c, th);
            });
        });
    }

    // ── Panel de orden y filtro de una columna ─

    let panel = null;

    function cerrarPanel() {
        if (panel) { panel.remove(); panel = null; }
        document.removeEventListener("mousedown", fueraDelPanel);
        document.removeEventListener("keydown", escapePanel);
    }
    function fueraDelPanel(e) { if (panel && !panel.contains(e.target)) cerrarPanel(); }
    function escapePanel(e) { if (e.key === "Escape") cerrarPanel(); }

    function esc(t) {
        return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function abrirPanel(c, th) {
        cerrarPanel();
        panel = document.createElement("div");
        panel.className = "tabla-panel";
        panel.setAttribute("role", "dialog");
        panel.setAttribute("aria-label", `Ordenar y filtrar ${c.etiqueta}`);

        const textoAsc = c.tipo === "numero" ? "Menor a mayor" : c.tipo === "fecha" ? "Más antiguo primero" : "Ordenar A → Z";
        const textoDesc = c.tipo === "numero" ? "Mayor a menor" : c.tipo === "fecha" ? "Más reciente primero" : "Ordenar Z → A";
        const filtro = estado.filtros[c.clave];

        let cuerpoFiltro;
        if (c.tipo === "numero" || c.tipo === "fecha") {
            const t = c.tipo === "numero" ? "number" : "date";
            cuerpoFiltro = `
                <div class="tabla-panel-rango">
                    <label>${c.tipo === "numero" ? "Desde" : "Desde"}
                        <input type="${t}" class="form-input" data-rango="min" value="${esc(filtro?.min ?? "")}" step="any"></label>
                    <label>Hasta
                        <input type="${t}" class="form-input" data-rango="max" value="${esc(filtro?.max ?? "")}" step="any"></label>
                </div>`;
        } else {
            // Valores posibles según los demás filtros, como en Excel
            const conteo = new Map();
            filasVisibles(c.clave).forEach(f => {
                const t = textoDe(c, f);
                conteo.set(t, (conteo.get(t) || 0) + 1);
            });
            const valores = [...conteo.keys()].sort((a, b) => a.localeCompare(b, "es", { numeric: true }));
            const marcados = new Set(filtro ? filtro.valores : valores);
            cuerpoFiltro = `
                <input type="search" class="form-input tabla-panel-buscar" placeholder="Buscar valor..." aria-label="Buscar valor">
                <label class="tabla-panel-todos"><input type="checkbox" data-todos> (Seleccionar todo)</label>
                <div class="tabla-panel-lista">
                    ${valores.map(v => `
                        <label class="tabla-panel-valor" data-texto="${esc(v.toLowerCase())}">
                            <input type="checkbox" value="${esc(v)}" ${marcados.has(v) ? "checked" : ""}>
                            <span>${esc(v)}</span><span class="tabla-panel-num">${conteo.get(v)}</span>
                        </label>`).join("")}
                </div>`;
        }

        panel.innerHTML = `
            <button type="button" class="tabla-panel-orden" data-dir="asc">${textoAsc}</button>
            <button type="button" class="tabla-panel-orden" data-dir="desc">${textoDesc}</button>
            <div class="tabla-panel-sep"></div>
            <div class="tabla-panel-titulo">Filtrar ${esc(c.etiqueta)}</div>
            ${cuerpoFiltro}
            <div class="tabla-panel-acciones">
                <button type="button" class="btn btn-secondary btn-sm" data-accion="limpiar">Quitar filtro</button>
                <button type="button" class="btn btn-primary btn-sm" data-accion="aplicar">Aceptar</button>
            </div>`;

        document.body.appendChild(panel);
        const r = th.getBoundingClientRect();
        const ancho = 260;
        panel.style.top = `${window.scrollY + r.bottom + 4}px`;
        panel.style.left = `${Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - ancho - 8))}px`;

        panel.querySelectorAll(".tabla-panel-orden").forEach(b => b.addEventListener("click", () => {
            estado.orden = { clave: c.clave, dir: b.dataset.dir };
            guardar(); cerrarPanel(); pintar();
        }));

        const todos = panel.querySelector("[data-todos]");
        const casillas = () => [...panel.querySelectorAll(".tabla-panel-valor input")];
        const visiblesLista = () => casillas().filter(x => !x.closest("label").hidden);
        function sincronizarTodos() {
            if (!todos) return;
            const v = visiblesLista();
            todos.checked = v.length > 0 && v.every(x => x.checked);
            todos.indeterminate = !todos.checked && v.some(x => x.checked);
        }
        if (todos) {
            sincronizarTodos();
            todos.addEventListener("change", () => { visiblesLista().forEach(x => x.checked = todos.checked); });
            casillas().forEach(x => x.addEventListener("change", sincronizarTodos));
            panel.querySelector(".tabla-panel-buscar").addEventListener("input", e => {
                const q = e.target.value.trim().toLowerCase();
                panel.querySelectorAll(".tabla-panel-valor").forEach(l => { l.hidden = q && !l.dataset.texto.includes(q); });
                sincronizarTodos();
            });
        }

        panel.querySelector("[data-accion=limpiar]").addEventListener("click", () => {
            delete estado.filtros[c.clave];
            guardar(); cerrarPanel(); pintar();
        });
        panel.querySelector("[data-accion=aplicar]").addEventListener("click", () => {
            if (todos) {
                const marcadas = casillas().filter(x => x.checked).map(x => x.value);
                if (marcadas.length === casillas().length) delete estado.filtros[c.clave];
                else estado.filtros[c.clave] = { valores: marcadas };
            } else {
                const min = panel.querySelector("[data-rango=min]").value;
                const max = panel.querySelector("[data-rango=max]").value;
                if (min === "" && max === "") delete estado.filtros[c.clave];
                else estado.filtros[c.clave] = { min: min === "" ? null : min, max: max === "" ? null : max };
            }
            guardar(); cerrarPanel(); pintar();
        });

        setTimeout(() => {
            document.addEventListener("mousedown", fueraDelPanel);
            document.addEventListener("keydown", escapePanel);
        });
        (panel.querySelector(".tabla-panel-buscar") || panel.querySelector("input") || panel.querySelector("button")).focus();
    }

    // ── Buscador y limpiar ─────────────────────

    if (op.buscador) {
        op.buscador.addEventListener("input", () => { estado.busqueda = op.buscador.value; pintar(); });
    }
    if (op.limpiar) {
        op.limpiar.addEventListener("click", () => {
            estado = { busqueda: "", orden: null, filtros: {} };
            if (op.buscador) op.buscador.value = "";
            guardar(); pintar();
        });
    }

    return {
        actualizar(nuevas) { filas = nuevas || []; pintar(); },
    };
}
