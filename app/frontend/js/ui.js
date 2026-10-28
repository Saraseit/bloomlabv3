// ============================================================
// BloomLab · Avisos, confirmaciones y formularios propios
//
// Reemplazan alert(), confirm() y prompt() del navegador:
//   ui.aviso(mensaje, tipo)          aviso en esquina, no bloquea
//   await ui.confirmar(mensaje, op)  true / false
//   await ui.formulario(op)          objeto con los valores, o null
//   ui.avisoAlLlegar(mensaje, tipo)  aviso que se muestra en la
//                                    siguiente página (antes de redirigir)
// ============================================================

const ui = (() => {

    // ── Avisos ─────────────────────────────────

    function contenedorAvisos() {
        let c = document.getElementById("ui-avisos");
        if (!c) {
            c = document.createElement("div");
            c.id = "ui-avisos";
            c.className = "ui-avisos";
            document.body.appendChild(c);
        }
        return c;
    }

    // Sin tipo explícito, un mensaje de error o de validación se pinta rojo
    function tipoPorTexto(texto) {
        const t = String(texto).toLowerCase();
        if (/error|no se pudo|inválid|invalid|debe|captura|completa|elige|selecciona|obligatori|no puede|entre 0/.test(t)) {
            return "error";
        }
        if (/guardad|cread|actualizad|eliminad|registrad|listo/.test(t)) return "ok";
        return "info";
    }

    function aviso(mensaje, tipo) {
        if (!document.body) {
            document.addEventListener("DOMContentLoaded", () => aviso(mensaje, tipo));
            return;
        }
        tipo = tipo || tipoPorTexto(mensaje);
        const el = document.createElement("div");
        el.className = `ui-aviso ui-aviso-${tipo}`;
        el.setAttribute("role", tipo === "error" ? "alert" : "status");
        el.innerHTML = `
            <span class="ui-aviso-icono">${tipo === "error" ? "⚠️" : tipo === "ok" ? "✓" : "ℹ️"}</span>
            <span class="ui-aviso-texto"></span>
            <button type="button" class="ui-aviso-cerrar" aria-label="Cerrar aviso">×</button>`;
        el.querySelector(".ui-aviso-texto").textContent = String(mensaje);

        const cerrar = () => {
            el.classList.add("ui-saliendo");
            setTimeout(() => el.remove(), 200);
        };
        el.querySelector(".ui-aviso-cerrar").addEventListener("click", cerrar);
        contenedorAvisos().appendChild(el);
        setTimeout(cerrar, tipo === "error" ? 7000 : 4000);
    }

    const CLAVE_PENDIENTE = "bloomlab-aviso-pendiente";

    function avisoAlLlegar(mensaje, tipo) {
        try {
            sessionStorage.setItem(CLAVE_PENDIENTE, JSON.stringify({ mensaje, tipo }));
        } catch (_) { /* sin almacenamiento: se pierde el aviso */ }
    }

    function mostrarPendiente() {
        try {
            const dato = sessionStorage.getItem(CLAVE_PENDIENTE);
            if (!dato) return;
            sessionStorage.removeItem(CLAVE_PENDIENTE);
            const { mensaje, tipo } = JSON.parse(dato);
            aviso(mensaje, tipo);
        } catch (_) { /* nada que mostrar */ }
    }

    // ── Ventana modal base ─────────────────────

    let _abierta = null;

    function abrirModal(contenido, alCancelar) {
        const fondo = document.createElement("div");
        fondo.className = "ui-modal-fondo";
        fondo.innerHTML = `<div class="ui-modal" role="dialog" aria-modal="true"></div>`;
        const caja = fondo.firstElementChild;
        caja.appendChild(contenido);
        document.body.appendChild(fondo);

        const anterior = document.activeElement;
        const teclas = e => {
            if (e.key === "Escape") { e.preventDefault(); alCancelar(); }
            // Tab no se escapa de la ventana
            if (e.key === "Tab") {
                const focos = caja.querySelectorAll("button, input, select, textarea, [tabindex]:not([tabindex='-1'])");
                if (!focos.length) return;
                const primero = focos[0], ultimo = focos[focos.length - 1];
                if (e.shiftKey && document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
                else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
            }
        };
        document.addEventListener("keydown", teclas);
        fondo.addEventListener("mousedown", e => { if (e.target === fondo) alCancelar(); });

        _abierta = fondo;
        return {
            caja,
            cerrar() {
                document.removeEventListener("keydown", teclas);
                fondo.remove();
                _abierta = null;
                if (anterior && anterior.focus) anterior.focus();
            },
        };
    }

    // ── Confirmación ───────────────────────────

    function confirmar(mensaje, opciones = {}) {
        const peligro = opciones.peligro ?? /eliminar|borrar|rechazar|desactivar|quitar/i.test(mensaje);
        return new Promise(resolver => {
            const cuerpo = document.createElement("div");
            cuerpo.innerHTML = `
                <h3 class="ui-modal-titulo"></h3>
                <p class="ui-modal-mensaje"></p>
                <div class="ui-modal-acciones">
                    <button type="button" class="btn btn-secondary" data-r="no"></button>
                    <button type="button" class="btn ${peligro ? "btn-danger" : "btn-primary"}" data-r="si"></button>
                </div>`;
            cuerpo.querySelector(".ui-modal-titulo").textContent =
                opciones.titulo || (peligro ? "Confirmar acción" : "Confirmar");
            cuerpo.querySelector(".ui-modal-mensaje").textContent = mensaje;
            cuerpo.querySelector("[data-r=no]").textContent = opciones.textoCancelar || "Cancelar";
            cuerpo.querySelector("[data-r=si]").textContent =
                opciones.textoAceptar || (peligro ? "Sí, continuar" : "Aceptar");

            const modal = abrirModal(cuerpo, () => terminar(false));
            function terminar(valor) { modal.cerrar(); resolver(valor); }
            cuerpo.querySelector("[data-r=no]").addEventListener("click", () => terminar(false));
            cuerpo.querySelector("[data-r=si]").addEventListener("click", () => terminar(true));
            // En acciones destructivas el foco arranca en Cancelar
            cuerpo.querySelector(peligro ? "[data-r=no]" : "[data-r=si]").focus();
        });
    }

    // ── Formulario ─────────────────────────────
    //
    // campos: [{ nombre, etiqueta, tipo, valor, requerido, opciones,
    //            sugerencias, min, max, step, placeholder, ayuda, completo }]
    // tipo: texto (default), numero, fecha, email, tel, area, seleccion
    // validar(valores): mensaje de error o null

    function escapar(t) {
        return String(t ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;")
            .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function campoHtml(c, i) {
        const id = `ui-campo-${i}`;
        const req = c.requerido ? "required" : "";
        const comun = `id="${id}" name="${escapar(c.nombre)}" ${req}
            ${c.placeholder ? `placeholder="${escapar(c.placeholder)}"` : ""}`;
        let control;
        if (c.tipo === "area") {
            control = `<textarea class="form-input ui-area" rows="3" ${comun}>${escapar(c.valor)}</textarea>`;
        } else if (c.tipo === "seleccion") {
            const ops = (c.opciones || []).map(o => {
                const valor = typeof o === "object" ? o.valor : o;
                const texto = typeof o === "object" ? o.texto : o;
                const sel = String(valor) === String(c.valor ?? "") ? "selected" : "";
                return `<option value="${escapar(valor)}" ${sel}>${escapar(texto)}</option>`;
            }).join("");
            control = `<select class="form-select" ${comun}>${ops}</select>`;
        } else {
            const tipos = { numero: "number", fecha: "date", email: "email", tel: "tel" };
            const lista = c.sugerencias ? `list="${id}-lista"` : "";
            control = `<input class="form-input" type="${tipos[c.tipo] || "text"}" ${comun} ${lista}
                value="${escapar(c.valor)}"
                ${c.min != null ? `min="${c.min}"` : ""} ${c.max != null ? `max="${c.max}"` : ""}
                ${c.step != null ? `step="${c.step}"` : c.tipo === "numero" ? 'step="any"' : ""}
                autocomplete="off">`;
            if (c.sugerencias) {
                control += `<datalist id="${id}-lista">${c.sugerencias
                    .map(s => `<option value="${escapar(s)}"></option>`).join("")}</datalist>`;
            }
        }
        return `
            <div class="form-group ${c.completo || c.tipo === "area" ? "form-group-full" : ""}">
                <label class="form-label" for="${id}">${escapar(c.etiqueta)}${c.requerido ? " *" : ""}</label>
                ${control}
                ${c.ayuda ? `<span class="input-hint">${escapar(c.ayuda)}</span>` : ""}
            </div>`;
    }

    function formulario(opciones) {
        const campos = opciones.campos || [];
        return new Promise(resolver => {
            const form = document.createElement("form");
            form.noValidate = true;
            form.innerHTML = `
                <h3 class="ui-modal-titulo"></h3>
                ${opciones.descripcion ? '<p class="ui-modal-mensaje ui-modal-descripcion"></p>' : ""}
                <div class="form-grid ui-form-grid">${campos.map(campoHtml).join("")}</div>
                <p class="ui-form-error" role="alert"></p>
                <div class="ui-modal-acciones">
                    <button type="button" class="btn btn-secondary" data-r="no">Cancelar</button>
                    <button type="submit" class="btn btn-primary"></button>
                </div>`;
            form.querySelector(".ui-modal-titulo").textContent = opciones.titulo || "";
            if (opciones.descripcion) form.querySelector(".ui-modal-descripcion").textContent = opciones.descripcion;
            form.querySelector("[type=submit]").textContent = opciones.textoAceptar || "Guardar";

            const modal = abrirModal(form, () => terminar(null));
            modal.caja.classList.add("ui-modal-ancho");
            function terminar(valor) { modal.cerrar(); resolver(valor); }

            const error = form.querySelector(".ui-form-error");
            function mostrarError(texto, control) {
                error.textContent = texto;
                form.querySelectorAll(".ui-invalido").forEach(x => x.classList.remove("ui-invalido"));
                if (control) { control.classList.add("ui-invalido"); control.focus(); }
            }

            form.querySelector("[data-r=no]").addEventListener("click", () => terminar(null));
            form.addEventListener("submit", e => {
                e.preventDefault();
                const valores = {};
                for (let i = 0; i < campos.length; i++) {
                    const c = campos[i];
                    const control = form.querySelector(`#ui-campo-${i}`);
                    let v = control.value.trim();
                    if (c.requerido && v === "") {
                        return mostrarError(`${c.etiqueta}: es obligatorio.`, control);
                    }
                    if (c.tipo === "numero") {
                        if (v === "") { v = null; }
                        else {
                            v = Number(v);
                            if (!Number.isFinite(v)) return mostrarError(`${c.etiqueta}: captura un número.`, control);
                            if (c.min != null && v < c.min) return mostrarError(`${c.etiqueta}: mínimo ${c.min}.`, control);
                            if (c.max != null && v > c.max) return mostrarError(`${c.etiqueta}: máximo ${c.max}.`, control);
                        }
                    }
                    if (c.tipo === "email" && v && !control.checkValidity()) {
                        return mostrarError(`${c.etiqueta}: correo no válido.`, control);
                    }
                    if (c.minimo && v.length < c.minimo) {
                        return mostrarError(`${c.etiqueta}: al menos ${c.minimo} caracteres.`, control);
                    }
                    valores[c.nombre] = v;
                }
                const problema = opciones.validar ? opciones.validar(valores) : null;
                if (problema) return mostrarError(problema);
                terminar(valores);
            });

            const primero = form.querySelector("input, select, textarea");
            if (primero) { primero.focus(); if (primero.select) primero.select(); }
        });
    }

    document.addEventListener("DOMContentLoaded", mostrarPendiente);

    return { aviso, confirmar, formulario, avisoAlLlegar };
})();

// Red de seguridad: si algún alert() quedó en el código, sale como aviso propio
window.alert = mensaje => ui.aviso(mensaje);
