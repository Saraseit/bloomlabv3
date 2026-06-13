async function cargarArreglos() {

    const respuesta = await fetch(
        "http://127.0.0.1:8000/arreglos"
    );

    const arreglos = await respuesta.json();

    const tbody =
        document.querySelector(
            "#tabla-arreglos tbody"
        );

    tbody.innerHTML = "";

    arreglos.forEach(arreglo => {

        const fila =
            document.createElement("tr");

        fila.innerHTML = `
            <td>${arreglo.codigo}</td>
            <td>${arreglo.nombre}</td>
            <td>${arreglo.categoria ?? ""}</td>
            <td>${arreglo.costo_total ?? 0}</td>
            <td>${arreglo.descripcion ?? ""}</td>
            <td>

                <button onclick="verDetalle(${arreglo.id})">
                    Ver
                </button>

                <button onclick="
                    editarArreglo(
                        ${arreglo.id},
                        '${(arreglo.nombre ?? '').replace(/'/g, "\\'")}',
                        '${(arreglo.categoria ?? '').replace(/'/g, "\\'")}',
                        '${(arreglo.descripcion ?? '').replace(/'/g, "\\'")}'
                    )
                ">
                    Editar
                </button>

                <button onclick="eliminarArreglo(${arreglo.id})">
                    Eliminar
                </button>

            </td>
        `;

        fila.style.cursor = "pointer";

        fila.addEventListener("click", () => {

        window.location.href =
        `detalle_arreglo.html?id=${arreglo.id}`;

        });

        tbody.appendChild(fila);

    });

}

cargarArreglos();

function verDetalle(id) {

    window.location.href =
        `detalle_arreglo.html?id=${id}`;
}

async function crearArreglo() {

    const nombre =
        prompt("Nombre");

    if (!nombre) return;

    const categoria =
        prompt("Categoría");

    const descripcion =
        prompt("Descripción");

    const respuesta =
        await fetch(
            "http://127.0.0.1:8000/arreglos",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    nombre,
                    categoria,
                    descripcion
                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al crear arreglo"
        );

        return;
    }

    cargarArreglos();
}

async function editarArreglo(
    id,
    nombreActual,
    categoriaActual,
    descripcionActual
) {

    const nombre =
        prompt(
            "Nombre",
            nombreActual
        );

    if (!nombre) return;

    const categoria =
        prompt(
            "Categoría",
            categoriaActual
        );

    const descripcion =
        prompt(
            "Descripción",
            descripcionActual
        );

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/arreglos/${id}`,
            {
                method: "PUT",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    nombre,
                    categoria,
                    descripcion
                })
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al actualizar arreglo"
        );

        return;
    }

    cargarArreglos();
}

async function eliminarArreglo(id) {

    const confirmar =
        confirm(
            "¿Eliminar arreglo?"
        );

    if (!confirmar) return;

    const respuesta =
        await fetch(
            `http://127.0.0.1:8000/arreglos/${id}`,
            {
                method: "DELETE"
            }
        );

    if (!respuesta.ok) {

        alert(
            "Error al eliminar arreglo"
        );

        return;
    }

    cargarArreglos();
}

