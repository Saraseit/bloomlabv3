// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

async function cargarClientes() {

    const respuesta = await fetchAuth(`${API_URL}/clientes`);

    const clientes = await respuesta.json();
    _clientes = clientes;

    const tbody = document.querySelector("#tabla-clientes tbody");

    tbody.innerHTML = "";

    clientes.forEach(cliente => {

        const fila = document.createElement("tr");

        // deuda_total viene calculada por el API en la misma consulta
        const deuda = cliente.deuda_total ?? 0;

        const celdaDeuda = deuda > 0
            ? `<span class="deuda-pendiente">$${fmt(deuda)}</span>`
            : `<span class="deuda-cero">$${fmt(0)}</span>`;

        fila.innerHTML = `
            <td>${cliente.nombre}</td>
            <td>${cliente.empresa ?? ""}</td>
            <td>${cliente.telefono ?? ""}</td>
            <td>${cliente.email ?? ""}</td>
            <td>${celdaDeuda}</td>

            <td>
                <button onclick='verDetalleCliente(${cliente.id})'>
                    Ver detalle
                </button>

                <button onclick='editarCliente(${cliente.id})'>
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

function verDetalleCliente(id) {
    window.location.href = `detalle_cliente.html?id=${id}`;
}

async function crearCliente() {

    const nombre = document.getElementById("nombre").value;
    const empresa = document.getElementById("empresa").value;
    const telefono = document.getElementById("telefono").value;
    const email = document.getElementById("email").value;

    const respuesta = await fetchAuth(`${API_URL}/clientes`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            empresa,
            telefono,
            email
        })
    });

    if (!respuesta.ok) {
        ui.aviso("Error al crear");
        return;
    }

    cargarClientes();
}

// Última lista del API; Editar busca aquí por id
let _clientes = [];

async function editarCliente(id) {

    const cliente = _clientes.find(c => c.id === id);
    if (!cliente) return;

    const datos = await ui.formulario({
        titulo: "Editar cliente",
        textoAceptar: "Guardar cambios",
        campos: [
            { nombre: "nombre", etiqueta: "Nombre", valor: cliente.nombre, requerido: true, minimo: 2, completo: true },
            { nombre: "empresa", etiqueta: "Empresa", valor: cliente.empresa ?? "" },
            { nombre: "telefono", etiqueta: "Teléfono", tipo: "tel", valor: cliente.telefono ?? "" },
            { nombre: "email", etiqueta: "Email", tipo: "email", valor: cliente.email ?? "", completo: true },
            { nombre: "notas", etiqueta: "Notas", tipo: "area", valor: cliente.notas ?? "" },
        ],
    });
    if (!datos) return;

    const respuesta = await fetchAuth(`${API_URL}/clientes/${cliente.id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(datos)
    });

    if (!respuesta.ok) {
        ui.aviso("Error al actualizar");
        return;
    }

    ui.aviso("Cliente actualizado", "ok");
    cargarClientes();
}

async function eliminarCliente(id) {

    const cliente = _clientes.find(c => c.id === id);
    const confirmar = await ui.confirmar(
        `Se eliminará a "${cliente ? cliente.nombre : "este cliente"}".`,
        { titulo: "¿Eliminar cliente?", textoAceptar: "Eliminar", peligro: true }
    );
    if (!confirmar) return;

    await fetchAuth(`${API_URL}/clientes/${id}`, {
        method: "DELETE"
    });

    cargarClientes();
}