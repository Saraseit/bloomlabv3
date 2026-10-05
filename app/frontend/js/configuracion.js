// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

let _parametros = [];
let _puedeEditar = false;

function escaparConfig(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function textoCambio(p) {
    if (!p.actualizado_en) return "Valor inicial";
    const fecha = p.actualizado_en.replace("T", " ");
    return p.actualizado_por
        ? `Cambiado el ${fecha} por ${p.actualizado_por}`
        : `Cambiado el ${fecha}`;
}

async function cargarConfiguracion() {

    const respuesta = await fetchAuth(`${API_URL}/configuracion`);

    if (!respuesta.ok) {
        alert("No se pudo cargar la configuración");
        return;
    }

    const datos = await respuesta.json();
    _parametros = datos.parametros;
    _puedeEditar = datos.puede_editar;

    const lista = document.getElementById("parametros-lista");
    lista.innerHTML = "";

    _parametros.forEach(p => {
        const fila = document.createElement("div");
        fila.className = "parametro";
        fila.innerHTML = `
            <div>
                <p class="parametro-nombre">${escaparConfig(p.nombre)}</p>
                <p class="parametro-descripcion">${escaparConfig(p.descripcion)}</p>
                <p class="parametro-cambio">${escaparConfig(textoCambio(p))}</p>
            </div>
            <div class="input-con-sufijo">
                <input
                    type="number"
                    class="form-input"
                    id="param-${p.clave}"
                    value="${Number(p.valor)}"
                    step="0.1"
                    min="0"
                    max="99.9"
                    ${_puedeEditar ? "" : "disabled"}
                    aria-label="${escaparConfig(p.nombre)}"
                >
                <span class="input-sufijo">%</span>
            </div>
        `;
        lista.appendChild(fila);
    });

    document.getElementById("aviso-solo-lectura").style.display =
        _puedeEditar ? "none" : "block";
    document.getElementById("btn-guardar").style.display =
        _puedeEditar ? "" : "none";
}

function mostrarMensaje(texto, tipo) {
    const el = document.getElementById("mensaje-guardado");
    el.textContent = texto;
    el.className = `mensaje-guardado mensaje-${tipo}`;
}

async function guardarConfiguracion() {

    const valores = {};
    for (const p of _parametros) {
        const v = parseFloat(document.getElementById(`param-${p.clave}`).value);
        if (isNaN(v) || v < 0 || v >= 100) {
            mostrarMensaje(`${p.nombre}: captura un valor entre 0 y 99.9%`, "error");
            return;
        }
        valores[p.clave] = v;
    }

    if (valores.margen_minimo > valores.margen_objetivo) {
        mostrarMensaje("El margen mínimo no puede ser mayor que el objetivo.", "error");
        return;
    }
    if (valores.margen_autorizacion > valores.margen_minimo) {
        mostrarMensaje("El margen que requiere autorización no puede ser mayor que el mínimo.", "error");
        return;
    }

    const respuesta = await fetchAuth(`${API_URL}/configuracion`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(valores)
    });

    const resultado = await respuesta.json().catch(() => ({}));

    if (!respuesta.ok) {
        mostrarMensaje(resultado.detail || "No se pudo guardar", "error");
        return;
    }

    mostrarMensaje(
        `Guardado. Se recalcularon ${resultado.eventos_recalculados} eventos.`,
        "ok"
    );
    cargarConfiguracion();
}

cargarConfiguracion();
