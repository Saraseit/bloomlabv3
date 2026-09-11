async function iniciarSesion() {
    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const btnLogin = document.getElementById("btn-login");
    const errorDiv = document.getElementById("error-msg");

    errorDiv.textContent = "";
    btnLogin.disabled = true;
    btnLogin.textContent = "Iniciando...";

    try {
        const resp = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({email, password})
        });
        const data = await resp.json();
        if (!resp.ok) {
            errorDiv.textContent = mensajeError(data);
            return;
        }
        guardarSesion(data.token, data.usuario);
        window.location.href = "/frontend/index.html";
    } catch (e) {
        errorDiv.textContent = "No se pudo conectar con el servidor";
    } finally {
        btnLogin.disabled = false;
        btnLogin.textContent = "Iniciar sesión";
    }
}

// El 401 del login trae detail como texto, pero un 422 de validación lo
// trae como lista de errores; sin esto se pintaría "[object Object]".
function mensajeError(data) {
    const detalle = data.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle) && detalle.length) {
        return "Revisa el correo y la contraseña";
    }
    return "Error al iniciar sesión";
}

// Enter en el campo de contraseña dispara el login
document.getElementById("password")
    .addEventListener("keydown", e => {
        if (e.key === "Enter") iniciarSesion();
    });

// Enter en el correo pasa a la contraseña
document.getElementById("email")
    .addEventListener("keydown", e => {
        if (e.key === "Enter") document.getElementById("password").focus();
    });

// Si ya hay sesión activa, no tiene sentido mostrar el login
if (obtenerToken()) {
    window.location.href = "/frontend/index.html";
}
