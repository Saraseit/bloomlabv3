async function cargarClientes() {

    const respuesta = await fetch(`${API_URL}/clientes`);

    const clientes = await respuesta.json();

    const tbody = document.querySelector("#tabla-clientes tbody");

    tbody.innerHTML = "";

    clientes.forEach(cliente => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${cliente.nombre}</td>
            <td>${cliente.empresa ?? ""}</td>
            <td>${cliente.telefono ?? ""}</td>
            <td>${cliente.email ?? ""}</td>
            <td>${cliente.comision_porcentaje ?? 0}</td>

            <td>
                <button onclick='editarCliente(${JSON.stringify(cliente)})'>
                    Editar
                </button>

                <button onclick='eliminarCliente(${cliente.id})'>
                    Eliminar
                </button>
            </td>
        `;

        tbody.appendChild(fila);
    });
}

cargarClientes();

async function crearCliente() {

    const nombre = document.getElementById("nombre").value;
    const empresa = document.getElementById("empresa").value;
    const telefono = document.getElementById("telefono").value;
    const email = document.getElementById("email").value;

    const comision_porcentaje = parseFloat(
        document.getElementById("comision").value || 0
    );

    const respuesta = await fetch(`${API_URL}/clientes`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            empresa,
            telefono,
            email,
            comision_porcentaje
        })
    });

    if (!respuesta.ok) {
        alert("Error al crear");
        return;
    }

    cargarClientes();
}

async function editarCliente(cliente) {

    const nombre = prompt("Nombre", cliente.nombre);
    if (!nombre) return;

    const empresa = prompt("Empresa", cliente.empresa ?? "");
    const telefono = prompt("Teléfono", cliente.telefono ?? "");
    const email = prompt("Email", cliente.email ?? "");

    const comision_porcentaje = parseFloat(
        prompt("Comisión %", cliente.comision_porcentaje ?? 0)
    );

    const respuesta = await fetch(`${API_URL}/clientes/${cliente.id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            empresa,
            telefono,
            email,
            notas: cliente.notas ?? "",
            comision_porcentaje
        })
    });

    if (!respuesta.ok) {
        alert("Error al actualizar");
        return;
    }

    cargarClientes();
}

async function eliminarCliente(id) {

    const confirmar = confirm("¿Eliminar cliente?");
    if (!confirmar) return;

    await fetch(`${API_URL}/clientes/${id}`, {
        method: "DELETE"
    });

    cargarClientes();
}