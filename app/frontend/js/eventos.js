// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

// Última lista del API; los botones buscan aquí por id
let _eventos = [];
let _clientes = [];

const ESTATUS = ["Cotizacion", "Pendiente Autorización", "Confirmado", "Completado", "Cancelado"];

function escaparEv(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function claseEstatus(estatus) {
    const t = (estatus || "").toLowerCase();
    if (t.includes("cotiz")) return "badge-cotizacion";
    if (t.includes("pendiente")) return "badge-cotizacion";
    if (t.includes("confirm")) return "badge-confirmado";
    if (t.includes("complet")) return "badge-completado";
    if (t.includes("cancel")) return "badge-cancelado";
    return "badge-default";
}

// ── Tabla con buscador, orden y filtros ────────

const _tabla = crearTablaInteractiva({
    tabla: document.getElementById("tabla-eventos"),
    buscador: document.getElementById("buscador-eventos"),
    conteo: document.getElementById("conteo-eventos"),
    limpiar: document.getElementById("limpiar-filtros-eventos"),
    recordar: "bloomlab-tabla-eventos",
    vacio: "Todavía no hay eventos registrados.",
    columnas: [
        { clave: "cliente", etiqueta: "Cliente", tipo: "texto", ancho: 140 },
        { clave: "nombre", etiqueta: "Evento", tipo: "texto", ancho: 170 },
        { clave: "fecha_evento", etiqueta: "Fecha", tipo: "fecha", ancho: 108 },
        { clave: "lugar", etiqueta: "Lugar", tipo: "texto", ancho: 124 },
        { clave: "estatus", etiqueta: "Estatus", tipo: "texto", ancho: 124 },
        { clave: "costo_final", etiqueta: "Costo total", tipo: "numero", ancho: 130, derecha: true,
          valor: e => Number(e.costo_final) || 0, texto: e => fmt(e.costo_final) },
        { clave: "precio_sugerido", etiqueta: "Precio sugerido", tipo: "numero", ancho: 156, derecha: true,
          valor: e => e.precio_sugerido == null ? null : Number(e.precio_sugerido),
          texto: e => e.precio_sugerido == null ? "—" : fmt(e.precio_sugerido) },
        { clave: "acciones", etiqueta: "Acciones", filtrable: false, ancho: 268 },
    ],
    pintarFila: evento => {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${escaparEv(evento.cliente)}</td>
            <td>${escaparEv(evento.nombre)}</td>
            <td class="col-nowrap">${escaparEv(evento.fecha_evento ?? "")}</td>
            <td>${escaparEv(evento.lugar ?? "")}</td>
            <td><span class="badge ${claseEstatus(evento.estatus)}">${escaparEv(evento.estatus ?? "")}</span></td>
            <td class="col-der">$${fmt(evento.costo_final)}</td>
            <td class="col-der">${evento.precio_sugerido == null ? "—" : "$" + fmt(evento.precio_sugerido)}</td>
            <td>
                <div class="action-cell">
                    <button class="btn btn-primary btn-sm" onclick="abrirEvento(${evento.id})">Abrir</button>
                    <button class="btn btn-secondary btn-sm" onclick="editarEvento(${evento.id})">Editar</button>
                    <button class="btn btn-secondary btn-sm" onclick="duplicarEvento(${evento.id})">Duplicar</button>
                    <button class="btn btn-danger btn-sm" onclick="eliminarEvento(${evento.id})">Eliminar</button>
                </div>
            </td>`;
        return fila;
    },
});

async function cargarEventos() {
    const respuesta = await fetchAuth(`${API_URL}/eventos`);
    if (!respuesta.ok) {
        ui.aviso("No se pudieron cargar los eventos");
        return;
    }
    _eventos = await respuesta.json();
    _tabla.actualizar(_eventos);
}

async function cargarClientes() {

    const respuesta = await fetchAuth(`${API_URL}/clientes`);
    _clientes = await respuesta.json();

    const select = document.getElementById("cliente-select");

    select.innerHTML = `<option value="">Seleccionar cliente</option>`;

    _clientes.forEach(cliente => {
        const option = document.createElement("option");
        option.value = cliente.id;
        option.textContent = cliente.nombre;
        select.appendChild(option);
    });
}

async function crearEvento() {

    const cliente_id = parseInt(
        document.getElementById("cliente-select").value
    );
    if (!cliente_id) {
        ui.aviso("Selecciona un cliente", "error");
        return;
    }

    const nombre = document.getElementById("nombre").value.trim();
    if (!nombre) {
        ui.aviso("Captura el nombre del evento", "error");
        return;
    }

    const tipo_evento = document.getElementById("tipo_evento").value;
    const fecha_evento = document.getElementById("fecha_evento").value;
    const lugar = document.getElementById("lugar").value;
    const descripcion = document.getElementById("descripcion").value;

    const comisionTexto = document.getElementById("comision_porcentaje").value.trim();
    const comision_porcentaje = comisionTexto === "" ? 0 : parseFloat(comisionTexto);
    if (isNaN(comision_porcentaje) || comision_porcentaje < 0 || comision_porcentaje >= 100) {
        ui.aviso("La comisión debe estar entre 0 y 99.99%", "error");
        return;
    }

    const respuesta = await fetchAuth(`${API_URL}/eventos`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            cliente_id,
            nombre,
            tipo_evento,
            // Sin fecha va null: una cadena vacía no es una fecha válida
            fecha_evento: fecha_evento || null,
            lugar,
            descripcion,
            estatus: "Cotizacion",
            comision_porcentaje
        })
    });

    if (!respuesta.ok) {
        ui.aviso("Error al crear evento");
        return;
    }

    ["nombre", "tipo_evento", "fecha_evento", "lugar", "descripcion", "comision_porcentaje"]
        .forEach(id => document.getElementById(id).value = "");
    document.getElementById("cliente-select").value = "";

    ui.aviso("Evento creado", "ok");
    cargarEventos();
}

function abrirEvento(id) {
    window.location.href = `detalle_evento.html?id=${id}`;
}

async function editarEvento(id) {

    const evento = _eventos.find(e => e.id === id);
    if (!evento) return;

    const estatus = ESTATUS.includes(evento.estatus) || !evento.estatus
        ? ESTATUS
        : [evento.estatus, ...ESTATUS];

    const datos = await ui.formulario({
        titulo: "Editar evento",
        textoAceptar: "Guardar cambios",
        campos: [
            { nombre: "nombre", etiqueta: "Nombre del evento", valor: evento.nombre, requerido: true, completo: true },
            { nombre: "cliente_id", etiqueta: "Cliente", tipo: "seleccion", valor: evento.cliente_id, requerido: true,
              opciones: _clientes.map(c => ({ valor: c.id, texto: c.nombre })) },
            { nombre: "estatus", etiqueta: "Estatus", tipo: "seleccion", valor: evento.estatus ?? "Cotizacion",
              opciones: estatus },
            { nombre: "tipo_evento", etiqueta: "Tipo de evento", valor: evento.tipo_evento ?? "",
              sugerencias: [...new Set(_eventos.map(e => e.tipo_evento).filter(Boolean))] },
            { nombre: "fecha_evento", etiqueta: "Fecha", tipo: "fecha", valor: evento.fecha_evento ?? "" },
            { nombre: "lugar", etiqueta: "Lugar", valor: evento.lugar ?? "", completo: true },
            { nombre: "descripcion", etiqueta: "Descripción", tipo: "area", valor: evento.descripcion ?? "" },
        ],
    });
    if (!datos) return;

    const respuesta = await fetchAuth(`${API_URL}/eventos/${evento.id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            ...datos,
            cliente_id: parseInt(datos.cliente_id),
            fecha_evento: datos.fecha_evento || null
        })
    });

    if (!respuesta.ok) {
        ui.aviso("Error al actualizar");
        return;
    }

    ui.aviso("Evento actualizado", "ok");
    cargarEventos();
}

async function duplicarEvento(id) {

    const confirmar = await ui.confirmar(
        "Se creará una copia en estatus Cotización, sin fecha ni precio acordado.",
        { titulo: "¿Duplicar este evento?", textoAceptar: "Duplicar" }
    );
    if (!confirmar) return;

    const resp = await fetchAuth(
        `${API_URL}/eventos/${id}/duplicar`,
        { method: "POST" }
    );

    if (!resp.ok) {
        ui.aviso("Error al duplicar el evento");
        return;
    }

    const resultado = await resp.json();

    // Se abre el duplicado para que el usuario lo ajuste en caliente
    ui.avisoAlLlegar("Evento duplicado. Esta es la copia.", "ok");
    window.location.href =
        `/frontend/detalle_evento.html?id=${resultado.id}`;
}

async function eliminarEvento(id) {

    const evento = _eventos.find(e => e.id === id);
    const confirmar = await ui.confirmar(
        `Se eliminará "${evento ? evento.nombre : "este evento"}".`,
        { titulo: "¿Eliminar evento?", textoAceptar: "Eliminar", peligro: true }
    );
    if (!confirmar) return;

    const respuesta = await fetchAuth(`${API_URL}/eventos/${id}`, {
        method: "DELETE"
    });

    if (!respuesta.ok) {
        ui.aviso("Error al eliminar el evento");
        return;
    }

    ui.aviso("Evento eliminado", "ok");
    cargarEventos();
}

// INIT
cargarEventos();
cargarClientes();
