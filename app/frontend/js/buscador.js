// ============================================================
// BloomLab · Búsqueda de texto compartida
//
// - Sin acentos ni mayúsculas: "orquidea" encuentra "Orquídea".
// - Varias palabras en cualquier orden: "rosa blan" encuentra
//   "rosa blanca" y "Rosa blanca premium".
// - resaltarCoincidencias() marca con <mark> lo que coincidió.
// - crearAutocompletado() convierte un <input> en buscador con
//   lista de sugerencias y navegación por teclado.
// ============================================================

function normalizarBusqueda(texto) {
    return String(texto ?? "")
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .toLowerCase();
}

function palabrasBusqueda(consulta) {
    return normalizarBusqueda(consulta).split(/\s+/).filter(Boolean);
}

// true si TODAS las palabras de la consulta aparecen en alguno de los textos
function coincideBusqueda(textos, consulta) {
    const palabras = palabrasBusqueda(consulta);
    if (palabras.length === 0) return true;
    const objetivo = normalizarBusqueda([].concat(textos).join(" "));
    return palabras.every(p => objetivo.includes(p));
}

function escaparTextoHtml(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// Devuelve HTML escapado con <mark> en cada coincidencia.
// Busca sobre el texto normalizado y traduce las posiciones al original,
// así "Orquídea" se marca completo aunque se haya escrito "orquidea".
function resaltarCoincidencias(texto, consulta) {
    const original = String(texto ?? "");
    const palabras = palabrasBusqueda(consulta);
    if (palabras.length === 0 || !original) return escaparTextoHtml(original);

    // mapa[i] = índice en el original del carácter i del texto normalizado
    let normalizado = "";
    const mapa = [];
    let indice = 0;
    for (const caracter of original) {
        const n = normalizarBusqueda(caracter);
        for (let k = 0; k < n.length; k++) mapa.push(indice);
        normalizado += n;
        indice += caracter.length;
    }

    const rangos = [];
    palabras.forEach(p => {
        let desde = 0;
        while (true) {
            const pos = normalizado.indexOf(p, desde);
            if (pos === -1) break;
            const ini = mapa[pos];
            const ultimo = mapa[pos + p.length - 1];
            // fin = justo después del carácter original que cierra la coincidencia
            let fin = ultimo + 1;
            while (fin < original.length && /[̀-ͯ\udc00-\udfff]/.test(original[fin])) fin++;
            rangos.push([ini, fin]);
            desde = pos + p.length;
        }
    });

    if (rangos.length === 0) return escaparTextoHtml(original);

    // Unir rangos encimados ("ro" y "ros" en la misma zona)
    rangos.sort((a, b) => a[0] - b[0]);
    const unidos = [rangos[0].slice()];
    for (const [ini, fin] of rangos.slice(1)) {
        const ultimo = unidos[unidos.length - 1];
        if (ini <= ultimo[1]) ultimo[1] = Math.max(ultimo[1], fin);
        else unidos.push([ini, fin]);
    }

    let html = "";
    let cursor = 0;
    for (const [ini, fin] of unidos) {
        html += escaparTextoHtml(original.slice(cursor, ini));
        html += `<mark>${escaparTextoHtml(original.slice(ini, fin))}</mark>`;
        cursor = fin;
    }
    return html + escaparTextoHtml(original.slice(cursor));
}

// ── Autocompletado ─────────────────────────────
//
// opciones:
//   input         <input type="text"> donde se escribe
//   lista         <ul> donde se pintan las sugerencias
//   obtenerItems  () => arreglo de elementos donde buscar
//   textos        item => [textos donde buscar]
//   pintar        (item, consulta) => HTML de la sugerencia
//   etiqueta      item => texto que queda en el input al elegir
//   alElegir      item | null => void (null cuando se borra la elección)
//   maximo        sugerencias visibles (default 30)
function crearAutocompletado(opciones) {

    const { input, lista, obtenerItems, textos, pintar, etiqueta, alElegir } = opciones;
    const maximo = opciones.maximo ?? 30;

    let resultados = [];
    let activo = -1;
    let elegido = null;

    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-controls", lista.id);
    input.setAttribute("autocomplete", "off");
    lista.setAttribute("role", "listbox");

    function cerrar() {
        lista.hidden = true;
        input.setAttribute("aria-expanded", "false");
        input.removeAttribute("aria-activedescendant");
        activo = -1;
    }

    function marcarActivo(nuevo) {
        const items = lista.querySelectorAll("[role=option]");
        if (items.length === 0) return;
        activo = (nuevo + items.length) % items.length;
        items.forEach((li, i) => li.setAttribute("aria-selected", i === activo ? "true" : "false"));
        const li = items[activo];
        input.setAttribute("aria-activedescendant", li.id);
        li.scrollIntoView({ block: "nearest" });
    }

    function elegir(item) {
        elegido = item;
        input.value = item ? etiqueta(item) : "";
        cerrar();
        alElegir(item);
    }

    function buscar() {
        const consulta = input.value.trim();

        // Si el texto ya no es el del elemento elegido, la elección se anula
        if (elegido && input.value !== etiqueta(elegido)) {
            elegido = null;
            alElegir(null);
        }

        if (!consulta) {
            cerrar();
            return;
        }

        const todos = obtenerItems().filter(item => coincideBusqueda(textos(item), consulta));
        resultados = todos.slice(0, maximo);

        if (resultados.length === 0) {
            lista.innerHTML = `<li class="combo-vacio">Sin coincidencias para “${escaparTextoHtml(consulta)}”</li>`;
        } else {
            lista.innerHTML = resultados.map((item, i) => `
                <li role="option" id="${lista.id}-op-${i}" data-indice="${i}" aria-selected="false">
                    ${pintar(item, consulta)}
                </li>`).join("") +
                (todos.length > maximo
                    ? `<li class="combo-mas">Mostrando ${maximo} de ${todos.length} coincidencias. Sigue escribiendo para afinar.</li>`
                    : "");
        }

        lista.hidden = false;
        input.setAttribute("aria-expanded", "true");
        activo = -1;
        if (resultados.length > 0) marcarActivo(0);
    }

    input.addEventListener("input", buscar);
    input.addEventListener("focus", () => { if (input.value.trim() && !elegido) buscar(); });

    input.addEventListener("keydown", e => {
        if (lista.hidden) {
            if (e.key === "ArrowDown" && input.value.trim()) { buscar(); e.preventDefault(); }
            return;
        }
        if (e.key === "ArrowDown")      { marcarActivo(activo + 1); e.preventDefault(); }
        else if (e.key === "ArrowUp")   { marcarActivo(activo - 1); e.preventDefault(); }
        else if (e.key === "Enter") {
            if (activo >= 0 && resultados[activo]) { elegir(resultados[activo]); e.preventDefault(); }
        }
        else if (e.key === "Escape")    { cerrar(); e.preventDefault(); }
    });

    // mousedown y no click: el click llega después del blur del input
    lista.addEventListener("mousedown", e => {
        const li = e.target.closest("[role=option]");
        e.preventDefault();
        if (li) elegir(resultados[Number(li.dataset.indice)]);
    });

    input.addEventListener("blur", cerrar);

    return {
        limpiar() { elegido = null; input.value = ""; cerrar(); },
        elegido() { return elegido; },
        enfocar() { input.focus(); },
    };
}
