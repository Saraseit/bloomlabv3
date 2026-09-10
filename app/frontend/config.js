const API_URL = "https://bloomlabv3.onrender.com";

// ──────────────────────────────────────────────
// Formateo de valores
// config.js se carga en todas las páginas, así que fmt() y fmtPct()
// quedan disponibles como funciones globales para todos los módulos.
// ──────────────────────────────────────────────

// Dinero con separador de miles: 1234.5 -> "1,234.50"
// Ojo: el resultado lleva comas, así que NO debe escribirse en un
// <input type="number">; esos campos siguen usando toFixed(2).
function fmt(n) {
    return Number(n || 0).toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Porcentajes: 10 -> "10.00%"
function fmtPct(n) {
    return Number(n || 0).toFixed(2) + '%';
}
