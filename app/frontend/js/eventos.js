async function cargarEventos() {

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/eventos"
        );

    const eventos =
        await respuesta.json();

    const tbody =
        document.querySelector(
            "#tabla-eventos tbody"
        );

    tbody.innerHTML = "";

    eventos.forEach(evento => {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td>${evento.cliente}</td>
            <td>${evento.nombre}</td>
            <td>${evento.fecha_evento ?? ""}</td>
            <td>${evento.lugar ?? ""}</td>
            <td>${evento.estatus ?? ""}</td>
            <td>${evento.costo_final ?? 0}</td>
            <td>${evento.precio_sugerido ?? 0}</td>

            <td>

                <button
                    onclick="abrirEvento(${evento.id})"
                >
                    Abrir
                </button>

                <button
                    onclick='editarEvento(${JSON.stringify(evento)})'
                >
                    Editar
                </button>

                <button
                    onclick='eliminarEvento(${evento.id})'
                >
                    Eliminar
                </button>

            </td>
        `;

        tbody.appendChild(fila);

    });

}

async function cargarClientes() {

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/clientes"
        );

    const clientes =
        await respuesta.json();

    const select =
        document.getElementById(
            "cliente-select"
        );

    select.innerHTML =
        `<option value="">
            Seleccionar cliente
        </option>`;

    clientes.forEach(cliente => {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            cliente.id;

        option.textContent =
            cliente.nombre;

        select.appendChild(option);

    });

}

async function crearEvento() {

    const cliente_id =
        parseInt(
            document.getElementById(
                "cliente-select"
            ).value
        );

    const nombre =
        document.getElementById(
            "nombre"
        ).value;

    const fecha_evento =
        document.getElementById(
            "fecha_evento"
        ).value;

    const lugar =
        document.getElementById(
            "lugar"
        ).value;

    const descripcion =
        document.getElementById(
            "descripcion"
        ).value;

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/eventos",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    cliente_id,
                    nombre,
                    fecha_evento,
                    lugar,
                    descripcion,
                    estatus: "Cotizacion"

                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al crear evento"
        );

        return;
    }

    cargarEventos();
}

function abrirEvento(id) {

    window.location.href =
        `detalle_evento.html?id=${id}`;
}

cargarEventos();

cargarClientes();

async function editarEvento(evento) {

    const nombre =
        prompt(
            "Nombre",
            evento.nombre
        );

    if (!nombre) return;

    const fecha_evento =
        prompt(
            "Fecha",
            evento.fecha_evento ?? ""
        );

    const lugar =
        prompt(
            "Lugar",
            evento.lugar ?? ""
        );

    const descripcion =
        prompt(
            "Descripción",
            evento.descripcion ?? ""
        );

    const estatus =
        prompt(
            "Estatus",
            evento.estatus ?? "Cotizacion"
        );

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/eventos/${evento.id}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    cliente_id:
                        evento.cliente_id,

                    nombre,
                    fecha_evento,
                    lugar,
                    descripcion,
                    estatus

                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al actualizar"
        );

        return;
    }

    cargarEventos();
}

async function eliminarEvento(id) {

    const confirmar =
        confirm(
            "¿Eliminar evento?"
        );

    if (!confirmar) return;

    await fetch(
        `http://127.0.0.1:8000/eventos/${id}`,
        {
            method: "DELETE"
        }
    );

    cargarEventos();
}