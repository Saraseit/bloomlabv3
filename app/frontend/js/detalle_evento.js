const parametros =
    new URLSearchParams(
        window.location.search
    );

const eventoId =
    parametros.get("id");

async function cargarEvento() {

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/eventos/${eventoId}`
        );

    const evento =
        await respuesta.json();

    document.getElementById(
        "nombre-evento"
    ).textContent =
        evento.nombre;

    document.getElementById(
        "cliente"
    ).textContent =
        evento.cliente;

    document.getElementById(
        "fecha-evento"
    ).textContent =
        evento.fecha_evento;

    document.getElementById(
        "lugar"
    ).textContent =
        evento.lugar ?? "";

    document.getElementById(
        "descripcion"
    ).textContent =
        evento.descripcion ?? "";

    document.getElementById(
        "costo-base"
    ).textContent =
        evento.costo_base ?? 0;

    document.getElementById(
        "comision-porcentaje"
    ).textContent =
        evento.comision_porcentaje ?? 0;

    document.getElementById(
        "importe-comision"
    ).textContent =
        evento.importe_comision ?? 0;

    document.getElementById(
        "costo-final"
    ).textContent =
        evento.costo_final ?? 0;

    document.getElementById(
        "precio-minimo"
    ).textContent =
        evento.precio_minimo ?? 0;

    document.getElementById(
        "precio-sugerido"
    ).textContent =
        evento.precio_sugerido ?? 0;

    const tbody =
        document.querySelector(
            "#tabla-evento-arreglos tbody"
        );

    tbody.innerHTML = "";

    evento.arreglos.forEach(arreglo => {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td>${arreglo.codigo}</td>
            <td>${arreglo.nombre}</td>
            <td>${arreglo.cantidad}</td>
            <td>${arreglo.costo_unitario}</td>
            <td>${arreglo.subtotal}</td>
            <td>${arreglo.observaciones ?? ""}</td>

            <td>

                <button
                    onclick='editarArreglo(${JSON.stringify(arreglo)})'
                >
                    Editar
                </button>

                <button
                    onclick='eliminarArreglo(${arreglo.id})'
                >
                    Eliminar
                </button>

            </td>
        `;

        tbody.appendChild(fila);

    });

}

async function cargarArreglos() {

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/arreglos"
        );

    const arreglos =
        await respuesta.json();

    const select =
        document.getElementById(
            "arreglo-select"
        );

    select.innerHTML =
        `<option value="">
            Seleccionar arreglo
        </option>`;

    arreglos.forEach(arreglo => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            arreglo.id;

        option.textContent =
            `${arreglo.codigo} - ${arreglo.nombre}`;

        select.appendChild(option);

    });

}

cargarEvento();

cargarArreglos();

async function agregarArreglo() {

    const arreglo_id =
        parseInt(
            document.getElementById(
                "arreglo-select"
            ).value
        );

    const cantidad =
        parseFloat(
            document.getElementById(
                "cantidad"
            ).value
        );

    const observaciones =
        document.getElementById(
            "observaciones"
        ).value;

    if (
        !arreglo_id ||
        !cantidad
    ) {

        alert(
            "Completa los datos"
        );

        return;
    }

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/evento-arreglos",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    evento_id:
                        parseInt(eventoId),

                    arreglo_id,

                    cantidad,

                    observaciones
                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al agregar arreglo"
        );

        return;
    }

    document.getElementById(
        "cantidad"
    ).value = "";

    document.getElementById(
        "observaciones"
    ).value = "";

    cargarEvento();
}

cargarEvento();

cargarArreglos();

async function editarArreglo(arreglo) {

    const cantidad =
        parseFloat(
            prompt(
                "Cantidad",
                arreglo.cantidad
            )
        );

    if (!cantidad) return;

    const observaciones =
        prompt(
            "Observaciones",
            arreglo.observaciones ?? ""
        );

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/evento-arreglos/${arreglo.id}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    cantidad,

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

    cargarEvento();
}
cargarEvento();

cargarArreglos();

async function eliminarArreglo(id) {

    const confirmar =
        confirm(
            "¿Eliminar arreglo?"
        );

    if (!confirmar) return;

    await fetch(
        `http://127.0.0.1:8000/evento-arreglos/${id}`,
        {
            method: "DELETE"
        }
    );

    cargarEvento();
}
