const parametros =
    new URLSearchParams(
        window.location.search
    );

const arregloId =
    parametros.get("id");

async function cargarDetalle() {

    const respuesta = await fetch(
        `http://127.0.0.1:8000/arreglos/${arregloId}`
    );

    const arreglo =
        await respuesta.json();

    document.getElementById(
        "nombre-arreglo"
    ).textContent =
        arreglo.nombre;

    document.getElementById(
        "codigo"
    ).textContent =
        arreglo.codigo;

    document.getElementById(
        "categoria"
    ).textContent =
        arreglo.categoria ?? "";

    document.getElementById(
        "descripcion"
    ).textContent =
        arreglo.descripcion ?? "";

    document.getElementById(
        "costo-total"
    ).textContent =
        arreglo.costo_total ?? 0;

    const tbody =
        document.querySelector(
            "#tabla-detalle tbody"
        );

    tbody.innerHTML = "";

    arreglo.insumos.forEach(insumo => {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td>${insumo.codigo}</td>
            <td>${insumo.nombre}</td>
            <td>${insumo.cantidad}</td>
            <td>${insumo.costo_real}</td>
            <td>${insumo.subtotal}</td>
            <td>${insumo.observaciones}</td>
            <td>

                <button
                    onclick='editarDetalle(${JSON.stringify(insumo)})'
                >
                    Editar
                </button>

                <button
                    onclick='eliminarDetalle(${insumo.id})'
                >
                    Eliminar
                </button>

            </td>
        `;

        tbody.appendChild(fila);

    });

}

cargarDetalle();

async function agregarInsumo() {

    const insumo_id =
        parseInt(
            prompt("ID del insumo")
        );

    const cantidad =
        parseFloat(
            prompt("Cantidad")
        );

    const costo_real =
        parseFloat(
            prompt("Costo real")
        );

    const observaciones =
        prompt("Observaciones");

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/arreglo-detalle",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    arreglo_id: parseInt(arregloId),
                    insumo_id,
                    cantidad,
                    costo_real,
                    observaciones
                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al agregar insumo"
        );

        return;
    }

    cargarDetalle();
}

async function eliminarDetalle(id) {

    const confirmar =
        confirm(
            "¿Eliminar insumo?"
        );

    if (!confirmar) return;

    await fetch(
        `http://127.0.0.1:8000/arreglo-detalle/${id}`,
        {
            method: "DELETE"
        }
    );

    cargarDetalle();
}

async function editarDetalle(detalle) {

    const cantidad =
        parseFloat(
            prompt(
                "Cantidad",
                detalle.cantidad
            )
        );

    const costo_real =
        parseFloat(
            prompt(
                "Costo Real",
                detalle.costo_real
            )
        );

    const observaciones =
        prompt(
            "Observaciones",
            detalle.observaciones ?? ""
        );

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/arreglo-detalle/${detalle.id}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    cantidad,
                    costo_real,
                    observaciones
                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al actualizar"
        );

        return;
    }

    cargarDetalle();
}