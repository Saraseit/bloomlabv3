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