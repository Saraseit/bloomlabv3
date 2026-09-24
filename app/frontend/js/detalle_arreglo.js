// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

const parametros = new URLSearchParams(window.location.search);
const arregloId = parametros.get("id");

// ── Cloudinary ──
const CLOUDINARY_CLOUD_NAME    = "dpft5hywe";
const CLOUDINARY_UPLOAD_PRESET = "ml_default";

// Costo final por código de insumo, que llena cargarInsumos() y usa el
// modal como sugerencia. Se declara aquí porque cargarInsumos() corre
// antes de la sección del modal.
const _costosCatalogo = {};

// Renglón que se está editando; lo fija editarDetalle() al abrir el modal.
let _detalleEditando = null;

async function cargarDetalle() {

    const respuesta = await fetchAuth(`${API_URL}/arreglos/${arregloId}`);
    const arreglo = await respuesta.json();

    document.getElementById("nombre-arreglo").textContent = arreglo.nombre;
    document.getElementById("codigo").textContent = arreglo.codigo;
    document.getElementById("categoria").textContent = arreglo.categoria ?? "";
    document.getElementById("descripcion").textContent = arreglo.descripcion ?? "";
    document.getElementById("costo-total").textContent = fmt(arreglo.costo_total);

    // Foto del arreglo
    const foto     = document.getElementById('foto-arreglo');
    const hint     = document.getElementById('hint-imagen');
    const inputUrl = document.getElementById('imagen-url-actual');

    if (arreglo.imagen_url) {
        foto.src = arreglo.imagen_url;
        foto.style.display = 'block';
        hint.textContent = '';
        inputUrl.value = arreglo.imagen_url;
    } else {
        foto.style.display = 'none';
        hint.textContent = 'Sin imagen asignada';
        inputUrl.value = '';
    }

    const tbody = document.querySelector("#tabla-detalle tbody");
    tbody.innerHTML = "";

    (arreglo.insumos || []).forEach(insumo => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${insumo.codigo}</td>
            <td>${insumo.nombre}</td>
            <td>${Number(insumo.cantidad)} ${insumo.unidad_uso ?? ""}</td>
            <td>${fmt(insumo.costo_real)}</td>
            <td>${fmt(insumo.subtotal)}</td>
            <td>${insumo.observaciones ?? ""}</td>
            <td>
                <button onclick='editarDetalle(${JSON.stringify(insumo)})'>
                    Editar
                </button>

                <button onclick="eliminarDetalle(${insumo.id})">
                    Eliminar
                </button>
            </td>
        `;

        tbody.appendChild(fila);
    });
}

cargarDetalle();
cargarInsumos();

async function cargarInsumos() {

    const respuesta = await fetchAuth(`${API_URL}/insumos`);
    const insumos = await respuesta.json();

    const select = document.getElementById("insumo-select");
    select.innerHTML = `<option value="">Seleccionar insumo</option>`;

    insumos.forEach(insumo => {
        const option = document.createElement("option");
        option.value = insumo.id;
        option.textContent =
            `${insumo.codigo} - ${insumo.nombre} (por ${insumo.unidad_uso})`;

        // Costo por unidad de USO con merma:
        // (costo de la unidad de compra / contenido) * (1 + merma / 100).
        // El API retorna la merma como entero (10), no como decimal (0.10).
        // Se guarda con 4 decimales: $480 / 24 tallos no debe redondear
        // a centavos antes de multiplicar por la cantidad.
        const piezas = Number(insumo.piezas_por_paquete) || 1;
        const costoFinal =
            (insumo.costo_referencia / piezas) *
            (1 + insumo.porcentaje_merma / 100);
        option.dataset.costoFinal = costoFinal.toFixed(4);
        option.dataset.unidadUso  = insumo.unidad_uso;
        option.dataset.presentacion = piezas !== 1
            ? `${insumo.unidad} de ${piezas} ${insumo.unidad_uso} a $${fmt(insumo.costo_referencia)}`
            : `${insumo.unidad} a $${fmt(insumo.costo_referencia)}`;

        // Se guarda por código de insumo para sugerirlo en el modal de edición
        _costosCatalogo[insumo.codigo] = costoFinal;

        select.appendChild(option);
    });
}
document.getElementById("insumo-select").addEventListener("change", function () {
    const opcionSeleccionada = this.options[this.selectedIndex];
    const costoInput = document.getElementById("costo-real");

    const hint = document.getElementById("hint-unidad-uso");

    if (opcionSeleccionada && opcionSeleccionada.dataset.costoFinal) {
        costoInput.value = opcionSeleccionada.dataset.costoFinal;
        hint.textContent =
            `Cantidad en ${opcionSeleccionada.dataset.unidadUso}. ` +
            `Se compra por ${opcionSeleccionada.dataset.presentacion}.`;
    } else {
        costoInput.value = "";
        hint.textContent = "";
    }
});
async function agregarInsumo() {

    const insumo_id = parseInt(document.getElementById("insumo-select").value);
    const cantidad = parseFloat(document.getElementById("cantidad").value);
    const costo_real = parseFloat(document.getElementById("costo-real").value);
    const observaciones = document.getElementById("observaciones").value;

    const respuesta = await fetchAuth(`${API_URL}/arreglo-detalle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            arreglo_id: parseInt(arregloId),
            insumo_id,
            cantidad,
            costo_real,
            observaciones
        })
    });

    if (!respuesta.ok) {
        alert("Error al agregar insumo");
        return;
    }

    cargarDetalle();
    cargarInsumos();
}

async function eliminarDetalle(id) {

    const confirmar = confirm("¿Eliminar insumo?");
    if (!confirmar) return;

    await fetchAuth(`${API_URL}/arreglo-detalle/${id}`, { method: "DELETE" });

    cargarDetalle();

    document.getElementById("insumo-select").value = "";
    document.getElementById("cantidad").value = "";
    document.getElementById("costo-real").value = "";
    document.getElementById("observaciones").value = "";
}

// ── Modal de edición del detalle ───────────────

function editarDetalle(insumo) {

    _detalleEditando = insumo;

    document.getElementById("modal-detalle-insumo").textContent =
        `${insumo.codigo} — ${insumo.nombre}`;

    document.getElementById("edit-cantidad").value      = insumo.cantidad ?? 0;
    document.getElementById("edit-costo-real").value    = insumo.costo_real ?? 0;
    document.getElementById("edit-observaciones").value = insumo.observaciones ?? "";

    // El costo del catálogo se ofrece como referencia, sin pisar el capturado
    const sugerido = _costosCatalogo[insumo.codigo];
    document.getElementById("hint-costo-catalogo").textContent =
        sugerido !== undefined
            ? `Catálogo por ${insumo.unidad_uso ?? "unidad"} (con merma): $${Number(sugerido).toFixed(4)}`
            : "";

    document.getElementById("modal-detalle").style.display = "flex";
    document.getElementById("edit-cantidad").focus();
}

function cerrarModalDetalle() {
    document.getElementById("modal-detalle").style.display = "none";
    _detalleEditando = null;
}

async function guardarDetalleEditado() {

    if (!_detalleEditando) return;

    const cantidad = parseFloat(
        document.getElementById("edit-cantidad").value
    );
    if (isNaN(cantidad) || cantidad <= 0) {
        alert("La cantidad debe ser mayor a 0");
        return;
    }

    const costo_real = parseFloat(
        document.getElementById("edit-costo-real").value
    );
    if (isNaN(costo_real) || costo_real < 0) {
        alert("Captura un costo real válido");
        return;
    }

    const observaciones =
        document.getElementById("edit-observaciones").value;

    const respuesta = await fetchAuth(
        `${API_URL}/arreglo-detalle/${_detalleEditando.id}`,
        {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cantidad, costo_real, observaciones })
        }
    );

    if (!respuesta.ok) {
        console.log(await respuesta.text());
        alert("Error al actualizar");
        return;
    }

    cerrarModalDetalle();
    cargarDetalle();
    cargarInsumos();
}

// Cerrar al hacer clic fuera de la tarjeta
document.getElementById("modal-detalle")
    .addEventListener("click", function (e) {
        if (e.target === this) cerrarModalDetalle();
    });

// Cerrar con Escape (accesibilidad de teclado)
document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (document.getElementById("modal-detalle").style.display === "flex") {
        cerrarModalDetalle();
    }
});

// ── Imagen del arreglo ──────────────────────────

function abrirWidgetImagenDetalle() {
    const widget = cloudinary.createUploadWidget(
        {
            cloudName:    CLOUDINARY_CLOUD_NAME,
            uploadPreset: CLOUDINARY_UPLOAD_PRESET,
            sources:      ['local', 'camera', 'url'],
            multiple:     false,
            maxFileSize:  5000000,
            cropping:     false
        },
        async (error, result) => {
            if (!error && result && result.event === "success") {
                const url = result.info.secure_url;

                const foto = document.getElementById('foto-arreglo');
                foto.src = url;
                foto.style.display = 'block';
                document.getElementById('hint-imagen').textContent = '';
                document.getElementById('imagen-url-actual').value = url;

                await guardarImagenArreglo(url);
            }
        }
    );
    widget.open();
}

async function guardarImagenArreglo(url) {
    const respuesta = await fetchAuth(`${API_URL}/arreglos/${arregloId}`);
    const arreglo   = await respuesta.json();

    const update = await fetchAuth(`${API_URL}/arreglos/${arregloId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nombre:      arreglo.nombre,
            categoria:   arreglo.categoria,
            descripcion: arreglo.descripcion,
            imagen_url:  url
        })
    });

    if (!update.ok) {
        alert('Error al guardar imagen');
    }
}