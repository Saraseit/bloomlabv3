const TOKEN_KEY = "bloomlab_token";
const USUARIO_KEY = "bloomlab_usuario";

function guardarSesion(token, usuario) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USUARIO_KEY, JSON.stringify(usuario));
}

function obtenerToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function obtenerUsuario() {
    const u = localStorage.getItem(USUARIO_KEY);
    return u ? JSON.parse(u) : null;
}

function cerrarSesion() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USUARIO_KEY);
    window.location.href = "/frontend/login.html";
}

function verificarAuth() {
    // Llama esta función al inicio de cada página protegida.
    // Si no hay token, redirige a login inmediatamente.
    const token = obtenerToken();
    if (!token) {
        window.location.href = "/frontend/login.html";
        return null;
    }
    return obtenerUsuario();
}

// Agrega el token a todos los fetch del sistema.
// Uso: fetchAuth(url, opciones) en lugar de fetch(url, opciones)
async function fetchAuth(url, opciones = {}) {
    const token = obtenerToken();
    const headers = {
        "Content-Type": "application/json",
        ...(opciones.headers || {}),
        ...(token ? {"Authorization": `Bearer ${token}`} : {})
    };
    const resp = await fetch(url, { ...opciones, headers });
    if (resp.status === 401) {
        // Token expirado o inválido — forzar re-login
        cerrarSesion();
        // La redirección a login ya va en camino, pero devolver la
        // respuesta dejaría que quien llamó siguiera tratando el cuerpo
        // del 401 como si fueran datos (insumos.forEach is not a
        // function, y así en cada pantalla). Esta promesa nunca resuelve,
        // así que la cadena se corta aquí y la página se va a login sin
        // ensuciar la consola.
        await new Promise(() => {});
    }
    return resp;
}
