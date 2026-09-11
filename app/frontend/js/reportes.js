// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

// Nombres de clientes, eventos y arreglos son texto libre
function escapar(texto) {
    return String(texto ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

// "2026-03" -> "Marzo 2026"
const MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
];

function nombreMes(clave) {
    const [anio, mes] = String(clave ?? "").split("-");
    const indice = parseInt(mes, 10) - 1;
    if (!anio || isNaN(indice) || !MESES[indice]) return clave ?? "";
    return `${MESES[indice]} ${anio}`;
}

function filaVacia(columnas, mensaje) {
    return `
        <tr>
            <td colspan="${columnas}" class="tabla-vacia">${mensaje}</td>
        </tr>
    `;
}

// Un reporte que falle no debe dejar la pantalla a medias: se avisa en
// su propia sección y las demás siguen pintándose.
function mostrarError(idContenedor, mensaje) {
    const contenedor = document.getElementById(idContenedor);
    if (contenedor) {
        contenedor.innerHTML =
            `<div class="error-seccion">${escapar(mensaje)}</div>`;
    }
}

// Cada sección se envuelve para que un error suyo no tumbe al resto
function pintarSeccion(idError, datos, pintar) {
    if (datos && datos.__error) {
        mostrarError(idError, datos.__error);
        return;
    }
    try {
        pintar(datos);
    } catch (e) {
        mostrarError(idError, "No se pudo mostrar esta sección: " + e.message);
    }
}


// ── 1. KPIs globales ───────────────────────────

function pintarResumen(r) {

    document.getElementById("kpi-eventos").textContent =
        r.eventos_confirmados ?? 0;
    document.getElementById("kpi-ingresos").textContent =
        fmt(r.ingresos_totales);
    document.getElementById("kpi-costos").textContent =
        fmt(r.costos_totales);
    document.getElementById("kpi-utilidad").textContent =
        fmt(r.utilidad_real);
    document.getElementById("kpi-margen").textContent =
        fmtPct(r.margen_promedio);
    document.getElementById("kpi-cobrado").textContent =
        fmt(r.total_cobrado);
    document.getElementById("kpi-cartera").textContent =
        fmt(r.cartera_pendiente);

    const tarjeta = document.getElementById("kpi-card-cartera");
    tarjeta.classList.remove("kpi-cartera-pendiente", "kpi-cartera-limpia");
    tarjeta.classList.add(
        r.cartera_pendiente > 0
            ? "kpi-cartera-pendiente"
            : "kpi-cartera-limpia"
    );
}


// ── 2. Ingresos por mes ────────────────────────

function pintarMeses(meses) {

    const tbody = document.querySelector("#tabla-meses tbody");
    tbody.innerHTML = "";

    if (!meses.length) {
        tbody.innerHTML = filaVacia(3,
            "No hay eventos confirmados en los últimos 12 meses.");
        return;
    }

    // El API los devuelve ascendentes; en pantalla van del más reciente
    [...meses].reverse().forEach(m => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td><span class="mes-mono">${escapar(nombreMes(m.mes))}</span></td>
            <td class="col-num">${m.cantidad}</td>
            <td class="col-num">$${fmt(m.ingresos)}</td>
        `;

        tbody.appendChild(fila);
    });
}


// ── 3. Top clientes ────────────────────────────

function pintarTopClientes(clientes) {

    const tbody = document.querySelector("#tabla-top-clientes tbody");
    tbody.innerHTML = "";

    if (!clientes.length) {
        tbody.innerHTML = filaVacia(4,
            "Todavía no hay clientes con eventos confirmados.");
        return;
    }

    clientes.forEach(c => {

        const fila = document.createElement("tr");

        const celdaDeuda = c.deuda > 0
            ? `<span class="deuda-pendiente">$${fmt(c.deuda)}</span>`
            : `<span class="deuda-cero">$${fmt(0)}</span>`;

        fila.innerHTML = `
            <td>${escapar(c.nombre)}</td>
            <td class="col-num">${c.eventos}</td>
            <td class="col-num">$${fmt(c.facturado)}</td>
            <td class="col-num">${celdaDeuda}</td>
        `;

        tbody.appendChild(fila);
    });
}


// ── 4. Top arreglos ────────────────────────────

function pintarTopArreglos(arreglos) {

    const tbody = document.querySelector("#tabla-top-arreglos tbody");
    tbody.innerHTML = "";

    if (!arreglos.length) {
        tbody.innerHTML = filaVacia(5,
            "Todavía no hay arreglos usados en eventos confirmados.");
        return;
    }

    arreglos.forEach(a => {

        const fila = document.createElement("tr");

        const celdaCategoria = a.categoria
            ? `<span class="tipo-chip">${escapar(a.categoria)}</span>`
            : '<span class="sin-dato">—</span>';

        fila.innerHTML = `
            <td>${escapar(a.nombre)}</td>
            <td>${celdaCategoria}</td>
            <td class="col-num">${a.veces_usado}</td>
            <td class="col-num">${a.unidades_totales}</td>
            <td class="col-num">$${fmt(a.costo_promedio)}</td>
        `;

        tbody.appendChild(fila);
    });
}


// ── 5. Rentabilidad por evento ─────────────────

function pintarRentabilidad(eventos) {

    const tbody = document.querySelector("#tabla-rentabilidad tbody");
    tbody.innerHTML = "";

    if (!eventos.length) {
        tbody.innerHTML = filaVacia(9,
            "Todavía no hay eventos confirmados con precio acordado.");
        return;
    }

    eventos.forEach(e => {

        const fila = document.createElement("tr");

        // Una pérdida pesa más que un buen margen, así que se revisa primero
        if (e.utilidad < 0) {
            fila.className = "fila-perdida";
        } else if (e.margen_pct > 40) {
            fila.className = "fila-buena";
        }

        const celdaTipo = e.tipo_evento
            ? `<span class="tipo-chip">${escapar(e.tipo_evento)}</span>`
            : '<span class="sin-dato">—</span>';

        const claseUtilidad = e.utilidad < 0
            ? "valor-negativo"
            : "valor-positivo";

        fila.innerHTML = `
            <td><span class="mes-mono">${escapar(e.fecha_evento ?? "—")}</span></td>
            <td>
                <a class="enlace-evento"
                   href="/frontend/detalle_evento.html?id=${e.id}">
                    ${escapar(e.nombre)}
                </a>
            </td>
            <td>${celdaTipo}</td>
            <td>${escapar(e.cliente)}</td>
            <td class="col-num">$${fmt(e.precio_venta)}</td>
            <td class="col-num">$${fmt(e.costo_final)}</td>
            <td class="col-num">$${fmt(e.gastos_reales)}</td>
            <td class="col-num">
                <span class="${claseUtilidad}">$${fmt(e.utilidad)}</span>
            </td>
            <td class="col-num">${fmtPct(e.margen_pct)}</td>
        `;

        tbody.appendChild(fila);
    });
}


// ── Carga ──────────────────────────────────────

// Devuelve los datos, o un objeto con __error para que la sección
// muestre el problema sin interrumpir a las demás.
async function traer(ruta) {
    try {
        const respuesta = await fetchAuth(`${API_URL}${ruta}`);
        if (!respuesta.ok) {
            return { __error: `El servidor respondió ${respuesta.status}` };
        }
        return await respuesta.json();
    } catch (e) {
        return { __error: "No se pudo conectar con el servidor" };
    }
}

async function cargarReportes() {

    const [resumen, meses, clientes, arreglos, rentabilidad] =
        await Promise.all([
            traer("/reportes/resumen"),
            traer("/reportes/eventos-por-mes"),
            traer("/reportes/top-clientes"),
            traer("/reportes/top-arreglos"),
            traer("/reportes/rentabilidad"),
        ]);

    pintarSeccion("error-resumen", resumen, pintarResumen);
    pintarSeccion("error-meses", meses, pintarMeses);
    pintarSeccion("error-clientes", clientes, pintarTopClientes);
    pintarSeccion("error-arreglos", arreglos, pintarTopArreglos);
    pintarSeccion("error-rentabilidad", rentabilidad, pintarRentabilidad);
}

// INIT
cargarReportes();
