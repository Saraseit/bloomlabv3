async function eliminarInsumo(id) {

    const confirmar = confirm("¿Eliminar este insumo?");
    if (!confirmar) return;

    await fetch(`${API_URL}/insumos/${id}`, {
        method: "DELETE"
    });

    cargarInsumos();
    cargarCategorias();
}

async function editarInsumo(insumo) {

    const nombre = prompt("Nombre", insumo.nombre);
    if (!nombre) return;

    const categoria_id = parseInt(
        prompt("ID Categoría", insumo.categoria_id ?? 1)
    );

    const unidad = prompt("Unidad", insumo.unidad);

    const costo_referencia = parseFloat(
        prompt("Costo Referencia", insumo.costo_referencia)
    );

    const porcentaje_merma = parseFloat(
        prompt("Porcentaje Merma", insumo.porcentaje_merma)
    );

    const respuesta = await fetch(`${API_URL}/insumos/${insumo.id}`, {
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

    cargarInsumos();
    cargarCategorias();
}

async function nuevoInsumo() {

    const nombre = prompt("Nombre");
    if (!nombre) return;

    const categoria_id = parseInt(
        document.getElementById("categoria-select").value
    );

    const unidad = prompt("Unidad");
    const costo_referencia = parseFloat(prompt("Costo Referencia"));
    const porcentaje_merma = parseFloat(prompt("Porcentaje Merma"));

    const respuesta = await fetch(`${API_URL}/insumos`, {
        method: "POST",
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
        alert("Error al crear insumo");
        return;
    }

    cargarInsumos();
    cargarCategorias();
}

async function cargarInsumos() {

    const respuesta = await fetch(`${API_URL}/insumos`);
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
            <td>${insumo.costo_referencia}</td>
            <td>${insumo.porcentaje_merma}</td>

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

async function cargarCategorias() {

    const respuesta = await fetch(`${API_URL}/categorias`);
    const categorias = await respuesta.json();

    const select = document.getElementById("categoria-select");

    select.innerHTML = `
        <option value="">Seleccionar categoría</option>
    `;

    categorias.forEach(categoria => {

        const option = document.createElement("option");

        option.value = categoria.id;
        option.textContent = categoria.nombre;

        select.appendChild(option);
    });
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