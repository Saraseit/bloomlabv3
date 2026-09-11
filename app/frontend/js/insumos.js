// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

async function eliminarInsumo(id) {

    const confirmar = confirm("¿Eliminar este insumo?");
    if (!confirmar) return;

    await fetchAuth(`${API_URL}/insumos/${id}`, {
        method: "DELETE"
    });

    cargarInsumos();
    cargarCategorias();
}

// ── Modal de edición ───────────────────────────

// Insumo que se está editando; lo fija editarInsumo() al abrir el modal.
let _insumoEditando = null;

function editarInsumo(insumo) {

    _insumoEditando = insumo;

    // Se reaprovecha el catálogo ya cargado por cargarCategorias()
    poblarSelectCategorias(
        document.getElementById("edit-categoria"),
        insumo.categoria_id
    );

    document.getElementById("edit-nombre").value  = insumo.nombre ?? "";
    document.getElementById("edit-unidad").value  = insumo.unidad ?? "";
    document.getElementById("edit-costo").value   = insumo.costo_referencia ?? "";
    // El API entrega la merma como entero (10), igual que la captura
    // el usuario; la conversión a decimal la hace el backend.
    document.getElementById("edit-merma").value   = insumo.porcentaje_merma ?? 0;

    document.getElementById("modal-insumo").style.display = "flex";
    document.getElementById("edit-nombre").focus();
}

function cerrarModalInsumo() {
    document.getElementById("modal-insumo").style.display = "none";
    _insumoEditando = null;
}

async function guardarInsumoEditado() {

    if (!_insumoEditando) return;

    const nombre = document.getElementById("edit-nombre").value.trim();
    if (!nombre) {
        alert("El nombre es obligatorio");
        return;
    }

    const categoria_id = parseInt(
        document.getElementById("edit-categoria").value
    );
    if (!categoria_id) {
        alert("Selecciona una categoría");
        return;
    }

    const unidad = document.getElementById("edit-unidad").value.trim();
    if (!unidad) {
        alert("La unidad es obligatoria");
        return;
    }

    const costo_referencia = parseFloat(
        document.getElementById("edit-costo").value
    ) || 0;
    if (costo_referencia <= 0) {
        alert("El costo de referencia debe ser mayor a 0");
        return;
    }

    // Se manda tal como lo escribe el usuario (10 = 10%),
    // igual que en nuevoInsumo(); el backend divide entre 100.
    const porcentaje_merma = parseFloat(
        document.getElementById("edit-merma").value
    ) || 0;
    if (porcentaje_merma < 0 || porcentaje_merma > 100) {
        alert("La merma debe estar entre 0 y 100");
        return;
    }

    const respuesta = await fetchAuth(`${API_URL}/insumos/${_insumoEditando.id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            categoria_id,
            unidad,
            costo_referencia,
            porcentaje_merma
        })
    });

    if (!respuesta.ok) {
        alert("Error al actualizar");
        return;
    }

    cerrarModalInsumo();
    cargarInsumos();
    cargarCategorias();
}

// Cerrar al hacer clic fuera de la tarjeta
document.getElementById("modal-insumo")
    .addEventListener("click", function (e) {
        if (e.target === this) cerrarModalInsumo();
    });

// Cerrar con Escape (accesibilidad de teclado)
document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (document.getElementById("modal-insumo").style.display === "flex") {
        cerrarModalInsumo();
    }
});

async function nuevoInsumo() {

    const nombre = document.getElementById("nombre-insumo").value.trim();
    if (!nombre) {
        alert("El nombre es obligatorio");
        return;
    }

    const categoria_id = parseInt(
        document.getElementById("categoria-select").value
    );
    if (!categoria_id) {
        alert("Selecciona una categoría");
        return;
    }

    const unidad = document.getElementById("unidad").value.trim();
    const costo_referencia = parseFloat(
        document.getElementById("costo-referencia").value
    ) || 0;
    const porcentaje_merma = parseFloat(
        document.getElementById("porcentaje-merma").value
    ) || 0;

    const respuesta = await fetchAuth(`${API_URL}/insumos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nombre,
            categoria_id,
            unidad,
            costo_referencia,
            porcentaje_merma
        })
    });

    if (!respuesta.ok) {
        alert("Error al crear insumo");
        return;
    }

    // Limpiar formulario
    document.getElementById("nombre-insumo").value    = "";
    document.getElementById("categoria-select").value = "";
    document.getElementById("unidad").value           = "";
    document.getElementById("costo-referencia").value = "";
    document.getElementById("porcentaje-merma").value = "";

    cargarInsumos();
    cargarCategorias();
}

async function cargarInsumos() {

    const respuesta = await fetchAuth(`${API_URL}/insumos`);
    const insumos = await respuesta.json();

    const tbody = document.querySelector("#tabla-insumos tbody");

    tbody.innerHTML = "";

    insumos.forEach(insumo => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${insumo.codigo}</td>
            <td>${insumo.nombre}</td>
            <td>${insumo.categoria}</td>
            <td>${insumo.unidad}</td>
            <td>${fmt(insumo.costo_referencia)}</td>
            <td>${fmtPct(insumo.porcentaje_merma)}</td>

            <td>
                <button onclick='editarInsumo(${JSON.stringify(insumo)})'>
                    Editar
                </button>

                <button onclick="eliminarInsumo(${insumo.id})">
                    Eliminar
                </button>
            </td>
        `;

        tbody.appendChild(fila);
    });
}

// Catálogo de categorías compartido por el formulario y el modal
let _categorias = [];

function poblarSelectCategorias(select, seleccionada) {

    select.innerHTML = `
        <option value="">Seleccionar categoría</option>
    `;

    _categorias.forEach(categoria => {

        const option = document.createElement("option");

        option.value = categoria.id;
        option.textContent = categoria.nombre;

        select.appendChild(option);
    });

    if (seleccionada !== undefined && seleccionada !== null) {
        select.value = seleccionada;
    }
}

async function cargarCategorias() {

    const respuesta = await fetchAuth(`${API_URL}/categorias`);
    _categorias = await respuesta.json();

    poblarSelectCategorias(
        document.getElementById("categoria-select")
    );
}

function filtrarInsumos() {
    const texto = document.getElementById('buscador-insumos')
        .value.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-insumos tbody tr');

    filas.forEach(fila => {
        // Busca en: código (0), nombre (1), categoría (2)
        const codigo    = fila.cells[0]?.textContent.toLowerCase() ?? '';
        const nombre    = fila.cells[1]?.textContent.toLowerCase() ?? '';
        const categoria = fila.cells[2]?.textContent.toLowerCase() ?? '';

        const coincide = !texto ||
            codigo.includes(texto) ||
            nombre.includes(texto) ||
            categoria.includes(texto);

        fila.style.display = coincide ? '' : 'none';
    });
}

// INIT (IMPORTANTE: solo una vez)
cargarInsumos();
cargarCategorias();