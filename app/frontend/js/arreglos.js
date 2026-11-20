// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

const CLOUDINARY_CLOUD_NAME    = "dpft5hywe";
const CLOUDINARY_UPLOAD_PRESET = "ml_default";

function abrirWidgetImagen() {
    const widget = cloudinary.createUploadWidget(
        {
            cloudName:    CLOUDINARY_CLOUD_NAME,
            uploadPreset: CLOUDINARY_UPLOAD_PRESET,
            sources:      ['local', 'camera', 'url'],
            multiple:     false,
            maxFileSize:  5000000,
            cropping:     false
        },
        (error, result) => {
            if (!error && result && result.event === "success") {
                const url = result.info.secure_url;
                document.getElementById('imagen-url-arreglo').value = url;
                const preview = document.getElementById('preview-imagen');
                preview.src     = url;
                preview.style.display = 'block';
            }
        }
    );
    widget.open();
}

// Última lista del API; los botones buscan aquí por id
let _arreglos = [];

function escaparAr(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Fecha de creación sin la hora: "2026-06-03"
const fechaCreado = arreglo => (arreglo.fecha_creacion || "").slice(0, 10);

// ── Tabla con buscador, orden y filtros ────────

const _tabla = crearTablaInteractiva({
    tabla: document.getElementById("tabla-arreglos"),
    buscador: document.getElementById("buscador-arreglos"),
    conteo: document.getElementById("conteo-arreglos"),
    limpiar: document.getElementById("limpiar-filtros-arreglos"),
    recordar: "bloomlab-tabla-arreglos",
    vacio: "Todavía no hay arreglos en el catálogo.",
    columnas: [
        { clave: "codigo", etiqueta: "Código", tipo: "texto", ancho: 104 },
        { clave: "nombre", etiqueta: "Nombre", tipo: "texto", ancho: 250 },
        { clave: "categoria", etiqueta: "Categoría", tipo: "texto", ancho: 130 },
        { clave: "costo_total", etiqueta: "Costo total", tipo: "numero", ancho: 130, derecha: true,
          valor: a => Number(a.costo_total) || 0, texto: a => fmt(a.costo_total) },
        { clave: "descripcion", etiqueta: "Descripción", tipo: "texto", ancho: 230 },
        { clave: "fecha_creacion", etiqueta: "Creado", tipo: "fecha", ancho: 108, valor: fechaCreado },
        { clave: "acciones", etiqueta: "Acciones", filtrable: false, ancho: 264 },
    ],
    pintarFila: arreglo => {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${escaparAr(arreglo.codigo)}</td>
            <td>${escaparAr(arreglo.nombre)}</td>
            <td>${arreglo.categoria ? `<span class="cat-chip">${escaparAr(arreglo.categoria)}</span>` : ""}</td>
            <td class="col-der"><span class="cost-prefix">$</span>${fmt(arreglo.costo_total)}</td>
            <td title="${escaparAr(arreglo.descripcion ?? "")}">${escaparAr(arreglo.descripcion ?? "")}</td>
            <td class="col-nowrap">${escaparAr(fechaCreado(arreglo))}</td>
            <td>
                <div class="action-cell">
                    <button class="btn btn-primary btn-sm" onclick="verDetalle(${arreglo.id})">Ver</button>
                    <button class="btn btn-secondary btn-sm" onclick="editarArreglo(${arreglo.id})">Editar</button>
                    <button class="btn btn-secondary btn-sm" onclick="duplicarArregloCatalogo(_arreglos.find(a => a.id === ${arreglo.id}))">Duplicar</button>
                    <button class="btn btn-danger btn-sm" onclick="eliminarArreglo(${arreglo.id})">Eliminar</button>
                </div>
            </td>`;

        // La fila abre el detalle, pero no cuando el clic es en la celda de
        // acciones: el clic de un botón también llega a la fila, y navegar
        // cerraría de inmediato el formulario o la confirmación que abrió.
        fila.addEventListener("click", e => {
            if (e.target.closest(".action-cell")) return;
            verDetalle(arreglo.id);
        });

        return fila;
    },
});

async function cargarArreglos() {

    const respuesta = await fetchAuth(
        `${API_URL}/arreglos`
    );

    if (!respuesta.ok) {
        ui.aviso("No se pudieron cargar los arreglos");
        return;
    }

    _arreglos = await respuesta.json();
    _tabla.actualizar(_arreglos);
}

function verDetalle(id) {
    window.location.href = `detalle_arreglo.html?id=${id}`;
}

async function crearArreglo() {
    const nombre      = document.getElementById("nombre-arreglo").value;
    const categoria   = document.getElementById("categoria-arreglo").value;
    const descripcion = document.getElementById("descripcion-arreglo").value;
    const imagen_url  = document.getElementById("imagen-url-arreglo").value;  // ← NUEVO

    const respuesta = await fetchAuth(`${API_URL}/arreglos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre, categoria, descripcion, imagen_url })  // ← NUEVO
    });

    if (!respuesta.ok) {
        ui.aviso("Error al crear arreglo");
        return;
    }

    cargarArreglos();
    document.getElementById("nombre-arreglo").value = "";
    document.getElementById("categoria-arreglo").value = "";
    document.getElementById("descripcion-arreglo").value = "";
    document.getElementById("imagen-url-arreglo").value = "";
    document.getElementById("preview-imagen").style.display = "none";
}
async function editarArreglo(id) {

    const arreglo = _arreglos.find(a => a.id === id);
    if (!arreglo) return;

    const datos = await ui.formulario({
        titulo: "Editar arreglo",
        descripcion: `${arreglo.codigo} · los insumos y la foto se editan en el detalle del arreglo.`,
        textoAceptar: "Guardar cambios",
        campos: [
            { nombre: "nombre", etiqueta: "Nombre", valor: arreglo.nombre, requerido: true, completo: true },
            { nombre: "categoria", etiqueta: "Categoría", valor: arreglo.categoria ?? "", completo: true,
              sugerencias: [...new Set(_arreglos.map(a => (a.categoria ?? "").trim()).filter(Boolean))] },
            { nombre: "descripcion", etiqueta: "Descripción", tipo: "area", valor: arreglo.descripcion ?? "" },
        ],
    });
    if (!datos) return;

    const respuesta = await fetchAuth(`${API_URL}/arreglos/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        // La foto se conserva: sin imagen_url el servidor la dejaba en blanco
        body: JSON.stringify({ ...datos, imagen_url: arreglo.imagen_url ?? null })
    });

    if (!respuesta.ok) {
        ui.aviso("Error al actualizar arreglo");
        return;
    }

    ui.aviso("Arreglo actualizado", "ok");
    cargarArreglos();
}

async function eliminarArreglo(id) {

    const arreglo = _arreglos.find(a => a.id === id);
    const confirmar = await ui.confirmar(
        `Se eliminará "${arreglo ? arreglo.nombre : "este arreglo"}" del catálogo.`,
        { titulo: "¿Eliminar arreglo?", textoAceptar: "Eliminar", peligro: true }
    );
    if (!confirmar) return;

    const respuesta = await fetchAuth(`${API_URL}/arreglos/${id}`, {
        method: "DELETE"
    });

    if (!respuesta.ok) {
        ui.aviso("Error al eliminar arreglo");
        return;
    }

    ui.aviso("Arreglo eliminado", "ok");
    cargarArreglos();
}

// INIT
cargarArreglos();
