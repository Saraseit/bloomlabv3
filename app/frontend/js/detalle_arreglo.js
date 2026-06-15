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
                    onclick="editarDetalle(
                        ${insumo.id},
                        ${insumo.cantidad},
                        ${insumo.costo_real},
                        '${(insumo.observaciones ?? "").replace(/'/g, "\\'")}'
                    )"
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
cargarInsumos();

async function cargarInsumos() {

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/insumos"
        );

    const insumos =
        await respuesta.json();

    const select =
        document.getElementById(
            "insumo-select"
        );

    select.innerHTML =
        `<option value="">
            Seleccionar insumo
        </option>`;

    insumos.forEach(insumo => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            insumo.id;

        option.textContent =
            `${insumo.codigo} - ${insumo.nombre}`;

        select.appendChild(option);

    });

}

async function agregarInsumo() {

    const insumo_id =
        parseInt(
            document.getElementById(
                "insumo-select"
            ).value
        );

    const cantidad =
        parseFloat(
            document.getElementById(
                "cantidad"
            ).value
        );

    const costo_real =
        parseFloat(
            document.getElementById(
                "costo-real"
            ).value
        );

    const observaciones =
        document.getElementById(
            "observaciones"
        ).value;
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
    cargarInsumos();
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
        document.getElementById(
        "insumo-select"
    ).value = "";

    document.getElementById(
        "cantidad"
    ).value = "";

    document.getElementById(
        "costo-real"
    ).value = "";

    document.getElementById(
        "observaciones"
    ).value = "";
}

async function editarDetalle(
    id,
    cantidadActual,
    costoActual,
    observacionesActuales
) {

    const cantidad =
        parseFloat(
            prompt(
                "Cantidad",
                cantidadActual
            )
        );

    const costo_real =
        parseFloat(
            prompt(
                "Costo Real",
                costoActual
            )
        );

    const observaciones =
        prompt(
            "Observaciones",
            observacionesActuales
        );

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/arreglo-detalle/${id}`,
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

        console.log(
            await respuesta.text()
        );

        alert(
            "Error al actualizar"
        );

        return;
    }

    cargarDetalle();
    cargarInsumos();
}

