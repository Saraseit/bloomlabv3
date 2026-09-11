// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

// La API ya exige rol admin en /usuarios; esto solo evita que alguien
// sin permiso se quede viendo una pantalla que no va a cargar nada.
if (usuario.rol !== "admin") {
    alert("Esta sección es solo para administradores");
    window.location.href = "/frontend/index.html";
    throw new Error("Sin permiso");
}

// Última lista traída del API. Los modales buscan aquí por id en vez de
// serializar el objeto dentro del onclick.
let _usuarios = [];

// Usuario que se está editando; null cuando es un alta.
let _usuarioEditando = null;

// Los nombres y correos son texto libre
function escapar(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// "2026-09-11T19:38:37.919207" -> "2026-09-11 19:38"
function formatoFecha(valor) {
    if (!valor) return null;
    return String(valor).replace("T", " ").slice(0, 16);
}

async function cargarUsuarios() {

    const respuesta = await fetchAuth(`${API_URL}/usuarios`);

    if (!respuesta.ok) {
        alert("Error al cargar los usuarios");
        return;
    }

    _usuarios = await respuesta.json();

    const tbody = document.querySelector("#tabla-usuarios tbody");

    tbody.innerHTML = "";

    if (_usuarios.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="tabla-vacia">
                    Todavía no hay usuarios registrados.
                </td>
            </tr>
        `;
        return;
    }

    _usuarios.forEach(u => {

        const fila = document.createElement("tr");

        if (!u.activo) fila.className = "fila-inactiva";

        const esTuUsuario = u.id === usuario.id;

        const acceso = formatoFecha(u.ultimo_acceso);

        const celdaAcceso = acceso
            ? acceso
            : '<span class="sin-dato">Nunca</span>';

        const celdaEstado = u.activo
            ? '<span class="estado-activo">Activo</span>'
            : '<span class="estado-inactivo">Inactivo</span>';

        // No puedes desactivarte a ti mismo: el backend lo rechaza y
        // aquí ni siquiera se ofrece el botón.
        const botonBaja = (esTuUsuario || !u.activo)
            ? ""
            : `<button class="btn btn-danger btn-sm"
                       onclick="desactivarUsuario(${u.id})">
                   Desactivar
               </button>`;

        fila.innerHTML = `
            <td>
                ${escapar(u.nombre)}
                ${esTuUsuario ? '<span class="es-tu-usuario">tú</span>' : ""}
            </td>
            <td>${escapar(u.email)}</td>
            <td><span class="rol-chip rol-${escapar(u.rol)}">${escapar(u.rol)}</span></td>
            <td>${celdaAcceso}</td>
            <td>${celdaEstado}</td>

            <td>
                <div class="action-cell">
                    <button class="btn btn-secondary btn-sm"
                            onclick="editarUsuario(${u.id})">
                        Editar
                    </button>
                    ${botonBaja}
                </div>
            </td>
        `;

        tbody.appendChild(fila);
    });
}

function abrirModalUsuario() {

    _usuarioEditando = null;

    document.getElementById("modal-usuario-titulo").textContent =
        "Nuevo Usuario";

    document.getElementById("usuario-nombre").value = "";
    document.getElementById("usuario-email").value = "";
    document.getElementById("usuario-password").value = "";
    document.getElementById("usuario-rol").value = "vendedor";
    document.getElementById("usuario-activo").checked = true;

    // Al crear se pide contraseña; el estado activo no aplica todavía
    document.getElementById("grupo-password").style.display = "";
    document.getElementById("grupo-activo").style.display = "none";

    document.getElementById("modal-usuario").style.display = "flex";
    document.getElementById("usuario-nombre").focus();
}

function editarUsuario(usuarioId) {

    const u = _usuarios.find(x => x.id === usuarioId);
    if (!u) return;

    _usuarioEditando = u;

    document.getElementById("modal-usuario-titulo").textContent =
        "Editar Usuario";

    document.getElementById("usuario-nombre").value = u.nombre ?? "";
    document.getElementById("usuario-email").value = u.email ?? "";
    document.getElementById("usuario-rol").value = u.rol ?? "vendedor";
    document.getElementById("usuario-activo").checked = Boolean(u.activo);

    // La contraseña se cambia por separado, no desde aquí
    document.getElementById("usuario-password").value = "";
    document.getElementById("grupo-password").style.display = "none";
    document.getElementById("grupo-activo").style.display = "";

    document.getElementById("modal-usuario").style.display = "flex";
    document.getElementById("usuario-nombre").focus();
}

function cerrarModalUsuario() {
    document.getElementById("modal-usuario").style.display = "none";
    _usuarioEditando = null;
}

async function guardarUsuario() {

    const nombre = document.getElementById("usuario-nombre").value.trim();
    if (nombre.length < 2) {
        alert("El nombre debe tener al menos 2 caracteres");
        return;
    }

    const email = document.getElementById("usuario-email").value.trim();
    if (!email.includes("@")) {
        alert("Captura un correo electrónico válido");
        return;
    }

    const rol = document.getElementById("usuario-rol").value;

    if (_usuarioEditando) {

        const activo = document.getElementById("usuario-activo").checked;

        const respuesta = await fetchAuth(
            `${API_URL}/usuarios/${_usuarioEditando.id}`,
            {
                method: "PUT",
                body: JSON.stringify({ nombre, email, rol, activo })
            }
        );

        if (!respuesta.ok) {
            const data = await respuesta.json();
            alert(mensajeError(data, "Error al actualizar el usuario"));
            return;
        }

    } else {

        const password = document.getElementById("usuario-password").value;
        if (password.length < 8) {
            alert("La contraseña debe tener al menos 8 caracteres");
            return;
        }

        const respuesta = await fetchAuth(`${API_URL}/usuarios`, {
            method: "POST",
            body: JSON.stringify({ nombre, email, password, rol })
        });

        if (!respuesta.ok) {
            const data = await respuesta.json();
            alert(mensajeError(data, "Error al crear el usuario"));
            return;
        }
    }

    cerrarModalUsuario();
    cargarUsuarios();
}

async function desactivarUsuario(usuarioId) {

    const u = _usuarios.find(x => x.id === usuarioId);
    if (!u) return;

    const confirmar = confirm(
        `¿Desactivar a ${u.nombre}? No podrá volver a iniciar sesión.`
    );
    if (!confirmar) return;

    const respuesta = await fetchAuth(`${API_URL}/usuarios/${usuarioId}`, {
        method: "DELETE"
    });

    if (!respuesta.ok) {
        const data = await respuesta.json();
        alert(mensajeError(data, "Error al desactivar el usuario"));
        return;
    }

    cargarUsuarios();
}

// El backend manda detail como texto en los errores de negocio, pero
// como lista en los 422 de validación de pydantic.
function mensajeError(data, porDefecto) {
    const detalle = data && data.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle) && detalle.length) {
        return detalle[0].msg || porDefecto;
    }
    return porDefecto;
}

// Cerrar al hacer clic fuera de la tarjeta
document.getElementById("modal-usuario")
    .addEventListener("click", function (e) {
        if (e.target === this) cerrarModalUsuario();
    });

// Cerrar con Escape (accesibilidad de teclado)
document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (document.getElementById("modal-usuario").style.display === "flex") {
        cerrarModalUsuario();
    }
});

// INIT
cargarUsuarios();
