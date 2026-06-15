async function eliminarInsumo(id) {

    const confirmar = confirm(
        "¿Eliminar este insumo?"
    );

    if (!confirmar) {
        return;
    }

    await fetch(
        `http://127.0.0.1:8000/insumos/${id}`,
        {
            method: "DELETE"
        }
    );
cargarInsumos();
cargarCategorias();
}

async function editarInsumo(insumo) {

    const nombre =
        prompt(
            "Nombre",
            insumo.nombre
        );

    if (!nombre) return;

    const categoria_id =
        parseInt(
            prompt(
                "ID Categoría",
                "1"
            )
        );

    const unidad =
        prompt(
            "Unidad",
            insumo.unidad
        );

    const costo_referencia =
        parseFloat(
            prompt(
                "Costo Referencia",
                insumo.costo_referencia
            )
        );

    const porcentaje_merma =
        parseFloat(
            prompt(
                "Porcentaje Merma",
                insumo.porcentaje_merma
            )
        );

    const respuesta = await fetch(
        `http://127.0.0.1:8000/insumos/${insumo.id}`,
        {
            method: "PUT",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                nombre,
                categoria_id,
                unidad,
                costo_referencia,
                porcentaje_merma
            })
        }
    );

    if (!respuesta.ok) {

        alert("Error al actualizar");

        return;
    }
cargarInsumos();
cargarCategorias();
}

async function nuevoInsumo() {

    const nombre =
        prompt("Nombre");

    if (!nombre) return;

    const categoria_id =
        parseInt(
            document.getElementById(
                "categoria-select"
            ).value
        );

    const unidad =
        prompt("Unidad");

    const costo_referencia =
        parseFloat(
            prompt("Costo Referencia")
        );

    const porcentaje_merma =
        parseFloat(
            prompt("Porcentaje Merma")
        );

    const respuesta = await fetch(
        "http://127.0.0.1:8000/insumos",
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                nombre,
                categoria_id,
                unidad,
                costo_referencia,
                porcentaje_merma
            })
        }
    );

    if (!respuesta.ok) {

        alert(
            "Error al crear insumo"
        );

        return;
    }
cargarInsumos();
cargarCategorias();
}

async function cargarInsumos() {

    const respuesta = await fetch(
        "http://127.0.0.1:8000/insumos"
    );

    const insumos = await respuesta.json();

    const tbody =
        document.querySelector(
            "#tabla-insumos tbody"
        );

    tbody.innerHTML = "";

    insumos.forEach(insumo => {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td>${insumo.codigo}</td>
            <td>${insumo.nombre}</td>
            <td>${insumo.categoria}</td>
            <td>${insumo.unidad}</td>
            <td>${insumo.costo_referencia}</td>
            <td>${insumo.porcentaje_merma}</td>
            <td>
                 <button
                     onclick='editarInsumo(${JSON.stringify(insumo)})'
                 >
                     Editar
                </button>

                <button
                     onclick="eliminarInsumo(${insumo.id})"
                >
                     Eliminar
                 </button>

            </td>
        `;

        tbody.appendChild(fila);
    });

}
cargarInsumos();
cargarCategorias();

async function cargarCategorias() {

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/categorias"
        );

    const categorias =
        await respuesta.json();

    const select =
        document.getElementById(
            "categoria-select"
        );

    select.innerHTML =
        `<option value="">
            Seleccionar categoría
        </option>`;

    categorias.forEach(categoria => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            categoria.id;

        option.textContent =
            categoria.nombre;

        select.appendChild(option);

    });

}

cargarInsumos();
cargarCategorias();