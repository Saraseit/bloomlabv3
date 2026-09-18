/* ============================================================
   BloomLab · Modo oscuro
   Se carga en el <head> de cada página para aplicar el tema
   antes del primer render (evita el parpadeo en blanco).
   Preferencia guardada en localStorage; si no hay, sigue al
   sistema (prefers-color-scheme).
   ============================================================ */

(function () {
    const CLAVE = "bloomlab-theme";

    function temaGuardado() {
        try {
            return localStorage.getItem(CLAVE);
        } catch (_) {
            return null;
        }
    }

    function temaDelSistema() {
        return window.matchMedia &&
               window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }

    function aplicarTema(tema) {
        document.documentElement.setAttribute("data-theme", tema);
        const btn = document.getElementById("theme-toggle");
        if (btn) {
            const esOscuro = tema === "dark";
            btn.textContent = esOscuro ? "☀️" : "🌙";
            btn.title       = esOscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
            btn.setAttribute("aria-label", btn.title);
        }
    }

    function alternarTema() {
        const actual = document.documentElement.getAttribute("data-theme");
        const nuevo  = actual === "dark" ? "light" : "dark";
        try {
            localStorage.setItem(CLAVE, nuevo);
        } catch (_) { /* almacenamiento no disponible */ }
        aplicarTema(nuevo);
    }

    // 1. Aplicar de inmediato (el script corre en el <head>)
    aplicarTema(temaGuardado() || temaDelSistema());

    // 2. Seguir al sistema mientras el usuario no haya elegido manualmente
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
            if (!temaGuardado()) aplicarTema(e.matches ? "dark" : "light");
        });
    }

    // 3. Botón flotante para alternar
    document.addEventListener("DOMContentLoaded", () => {
        const btn = document.createElement("button");
        btn.id        = "theme-toggle";
        btn.type      = "button";
        btn.className = "theme-toggle";
        btn.addEventListener("click", alternarTema);
        document.body.appendChild(btn);
        aplicarTema(document.documentElement.getAttribute("data-theme"));
    });

    window.alternarTema = alternarTema;
})();
