const CLOUDINARY_CLOUD_NAME    = dpft5hywe;
const CLOUDINARY_UPLOAD_PRESET = ml_default;

function abrirWidgetImagen() {
    const widget = cloudinary.createUploadWidget(
        {
            cloudName:    CLOUDINARY_CLOUD_NAME,
            uploadPreset: CLOUDINARY_UPLOAD_PRESET,
            sources:      ['local', 'camera', 'url'],
            multiple:     false,
            maxFileSize:  5000000,
            cropping:     false
        },
        (error, result) => {
            if (!error && result && result.event === "success") {
                const url = result.info.secure_url;
                document.getElementById('imagen-url-arreglo').value = url;
                const preview = document.getElementById('preview-imagen');
                preview.src     = url;
                preview.style.display = 'block';
            }
        }
    );
    widget.open();
}

async function cargarArreglos() {

    const respuesta = await fetch(
        `${API_URL}/arreglos`
    );

    const arreglos = await respuesta.json();

    const tbody = document.querySelector("#tabla-arreglos tbody");

    tbody.innerHTML = "";

    arreglos.forEach(arreglo => {

        const fila = document.createElement("tr");

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
            window.location.href = `detalle_arreglo.html?id=${arreglo.id}`;
        });

        tbody.appendChild(fila);
    });
}

cargarArreglos();

function verDetalle(id) {
    window.location.href = `detalle_arreglo.html?id=${id}`;
}

async function crearArreglo() {
    const nombre      = document.getElementById("nombre-arreglo").value;
    const categoria   = document.getElementById("categoria-arreglo").value;
    const descripcion = document.getElementById("descripcion-arreglo").value;
    const imagen_url  = document.getElementById("imagen-url-arreglo").value;  // ← NUEVO

    const respuesta = await fetch(`${API_URL}/arreglos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre, categoria, descripcion, imagen_url })  // ← NUEVO
    });

    if (!respuesta.ok) {
        alert("Error al crear arreglo");
        return;
    }

    cargarArreglos();
    document.getElementById("nombre-arreglo").value = "";
    document.getElementById("categoria-arreglo").value = "";
    document.getElementById("descripcion-arreglo").value = "";
    document.getElementById("imagen-url-arreglo").value = "";
    document.getElementById("preview-imagen").style.display = "none";
}
async function editarArreglo(id, nombreActual, categoriaActual, descripcionActual) {

    const nombre = prompt("Nombre", nombreActual);
    if (!nombre) return;

    const categoria = prompt("Categoría", categoriaActual);
    const descripcion = prompt("Descripción", descripcionActual);

    const respuesta = await fetch(`${API_URL}/arreglos/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            nombre,
            categoria,
            descripcion
        })
    });

    if (!respuesta.ok) {
        alert("Error al actualizar arreglo");
        return;
    }

    cargarArreglos();
}

async function eliminarArreglo(id) {

    const confirmar = confirm("¿Eliminar arreglo?");
    if (!confirmar) return;

    const respuesta = await fetch(`${API_URL}/arreglos/${id}`, {
        method: "DELETE"
    });

    if (!respuesta.ok) {
        alert("Error al eliminar arreglo");
        return;
    }

    cargarArreglos();
}

function filtrarArreglos() {
    const texto = document.getElementById('buscador-arreglos')
        .value.toLowerCase().trim();
    const filas = document.querySelectorAll('#tabla-arreglos tbody tr');

    filas.forEach(fila => {
        // Busca en: código (0), nombre (1), categoría (2), descripción (4)
        const codigo      = fila.cells[0]?.textContent.toLowerCase() ?? '';
        const nombre      = fila.cells[1]?.textContent.toLowerCase() ?? '';
        const categoria   = fila.cells[2]?.textContent.toLowerCase() ?? '';
        const descripcion = fila.cells[4]?.textContent.toLowerCase() ?? '';

        const coincide = !texto ||
            codigo.includes(texto) ||
            nombre.includes(texto) ||
            categoria.includes(texto) ||
            descripcion.includes(texto);

        fila.style.display = coincide ? '' : 'none';
    });
}
