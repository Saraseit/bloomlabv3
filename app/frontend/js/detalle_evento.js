// Sesión: sin token se redirige a login antes de tocar la API
const usuario = verificarAuth();
if (!usuario) throw new Error("Sin sesión");

const parametros = new URLSearchParams(window.location.search);
const eventoId = parametros.get("id");

// ────────────────────────────────────────────
// Valores numéricos crudos del evento en curso.
// La pantalla se pinta con fmt(), que agrega separador de miles
// ("1,234.56"), y parseFloat("1,234.56") devuelve 1. Por eso los
// cálculos leen estas variables y nunca el textContent.
// ────────────────────────────────────────────
let _costoFinal     = 0;
let _precioMinimo   = 0;
let _precioSugerido = 0;
let _costoFlete     = 0;
let _costoMontaje   = 0;
let _precioVenta    = 0;

async function cargarEvento() {

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}`
    );

    const evento = await respuesta.json();

    document.getElementById("nombre-evento").textContent = evento.nombre;
    document.getElementById("cliente").textContent = evento.cliente;
    document.getElementById("fecha-evento").textContent = evento.fecha_evento;
    document.getElementById("lugar").textContent = evento.lugar ?? "";
    document.getElementById("descripcion").textContent = evento.descripcion ?? "";
    // Se guardan los valores crudos antes de formatear la pantalla
    _costoFlete   = evento.costo_flete   ?? 0;
    _costoMontaje = evento.costo_montaje ?? 0;
    _precioVenta  = evento.precio_venta  ?? 0;

    document.getElementById("costo-base").textContent = fmt(evento.costo_base);
    document.getElementById('valor-flete').textContent   = fmt(_costoFlete);
    document.getElementById('valor-montaje').textContent = fmt(_costoMontaje);
    document.getElementById("comision-porcentaje").textContent =
        fmtPct(evento.comision_porcentaje);
    document.getElementById("importe-comision").textContent = fmt(evento.importe_comision);
    document.getElementById("costo-final").textContent = fmt(evento.costo_final);
    document.getElementById("precio-minimo").textContent = fmt(evento.precio_minimo);
    document.getElementById("precio-sugerido").textContent = fmt(evento.precio_sugerido);

    const tbody = document.querySelector("#tabla-evento-arreglos tbody");

    tbody.innerHTML = "";

    (evento.arreglos || []).forEach(arreglo => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${arreglo.codigo}</td>
            <td>${arreglo.nombre}</td>
            <td>${arreglo.cantidad}</td>
            <td>${fmt(arreglo.costo_unitario)}</td>
            <td>${fmt(arreglo.subtotal)}</td>
            <td>${arreglo.observaciones ?? ""}</td>

            <td>
                <button onclick='editarArreglo(${JSON.stringify(arreglo)})'>
                    Editar
                </button>

                <button onclick='eliminarArreglo(${arreglo.id})'>
                    Eliminar
                </button>
            </td>
        `;

        tbody.appendChild(fila);
    });

    iniciarNegociacion(
    evento.costo_final,
    evento.precio_minimo,
    evento.precio_sugerido,
    evento.precio_venta
    );

    // Pagos y gastos reales solo existen para un evento ya contratado
    if (evento.estatus === 'Confirmado') {
        mostrarSeccionesContrato();
        cargarPagos();
        cargarGastosReales();
    } else {
        ocultarSeccionesContrato();
    }
}

async function cargarArreglos() {

    const respuesta = await fetchAuth(`${API_URL}/arreglos`);

    const arreglos = await respuesta.json();

    const select = document.getElementById("arreglo-select");

    select.innerHTML = `<option value="">Seleccionar arreglo</option>`;

    arreglos.forEach(arreglo => {

        const option = document.createElement("option");

        option.value = arreglo.id;
        option.textContent = `${arreglo.codigo} - ${arreglo.nombre}`;

        select.appendChild(option);
    });
}

async function agregarArreglo() {

    const arreglo_id = parseInt(
        document.getElementById("arreglo-select").value
    );

    const cantidad = parseFloat(
        document.getElementById("cantidad").value
    );

    const observaciones =
        document.getElementById("observaciones").value;

    if (!arreglo_id || !cantidad) {
        alert("Completa los datos");
        return;
    }

    const respuesta = await fetchAuth(`${API_URL}/evento-arreglos`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            evento_id: parseInt(eventoId),
            arreglo_id,
            cantidad,
            observaciones
        })
    });

    if (!respuesta.ok) {
        alert("Error al agregar arreglo");
        return;
    }

    document.getElementById("cantidad").value = "";
    document.getElementById("observaciones").value = "";

    cargarEvento();
}

async function editarArreglo(arreglo) {

    const cantidad = parseFloat(prompt("Cantidad", arreglo.cantidad));
    if (!cantidad) return;

    const observaciones =
        prompt("Observaciones", arreglo.observaciones ?? "");

    const respuesta = await fetchAuth(
        `${API_URL}/evento-arreglos/${arreglo.id}`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                cantidad,
                observaciones
            })
        }
    );

    if (!respuesta.ok) {
        alert("Error al actualizar");
        return;
    }

    cargarEvento();
}

async function eliminarArreglo(id) {

    const confirmar = confirm("¿Eliminar arreglo?");
    if (!confirmar) return;

    await fetchAuth(
        `${API_URL}/evento-arreglos/${id}`,
        {
            method: "DELETE"
        }
    );

    cargarEvento();
}

// ── Gastos operativos ──────────────────────────

function abrirModalGastos() {
    // Precarga con los valores crudos: la pantalla los muestra con
    // separador de miles y un <input type="number"> no acepta comas.
    document.getElementById('input-flete').value   = _costoFlete   || 0;
    document.getElementById('input-montaje').value = _costoMontaje || 0;

    const modal = document.getElementById('modal-gastos');
    modal.style.display = 'flex';
}

function cerrarModalGastos() {
    document.getElementById('modal-gastos').style.display = 'none';
}

async function guardarGastos() {
    const costo_flete   = parseFloat(document.getElementById('input-flete').value)   || 0;
    const costo_montaje = parseFloat(document.getElementById('input-montaje').value) || 0;

    const respuesta = await fetchAuth(`${API_URL}/eventos/${eventoId}/gastos`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ costo_flete, costo_montaje })
    });

    if (!respuesta.ok) {
        alert('Error al guardar gastos');
        return;
    }

    cerrarModalGastos();
    cargarEvento(); // recarga KPIs y valores
}

// Cerrar modal al hacer clic fuera
document.getElementById('modal-gastos')
    .addEventListener('click', function(e) {
        if (e.target === this) cerrarModalGastos();
    });

// ── Negociación de precio ──────────────────────────

function iniciarNegociacion(costoFinal, precioMinimo, precioSugerido, precioVenta) {
    _costoFinal     = costoFinal;
    _precioMinimo   = precioMinimo;
    _precioSugerido = precioSugerido;

    // Referencias visuales
    document.getElementById('ref-precio-minimo').textContent   = fmt(precioMinimo);
    document.getElementById('ref-precio-sugerido').textContent = fmt(precioSugerido);

    // Si ya hay precio acordado, precarga los campos.
    // Son <input type="number">: no aceptan comas, van con toFixed().
    if (precioVenta && precioVenta > 0) {
        const margen = (1 - costoFinal / precioVenta) * 100;
        const ganancia = precioVenta - costoFinal;
        document.getElementById('input-precio-venta').value = precioVenta.toFixed(2);
        document.getElementById('input-margen').value       = margen.toFixed(1);
        document.getElementById('input-ganancia').value     = ganancia.toFixed(2);
        actualizarHints(margen, precioMinimo, precioSugerido);
    }
}

// Cuando el usuario escribe el margen
document.getElementById('input-margen').addEventListener('input', function () {
    if (!_costoFinal) return;
    const margen = parseFloat(this.value);
    if (isNaN(margen) || margen >= 100) return;

    const precio   = _costoFinal / (1 - margen / 100);
    const ganancia = precio - _costoFinal;

    document.getElementById('input-precio-venta').value = precio.toFixed(2);
    document.getElementById('input-ganancia').value     = ganancia.toFixed(2);

    actualizarHints(margen, _precioMinimo, _precioSugerido);
});

// Cuando el usuario escribe la ganancia
document.getElementById('input-ganancia').addEventListener('input', function () {
    if (!_costoFinal) return;
    const ganancia = parseFloat(this.value);
    if (isNaN(ganancia)) return;

    const precio = _costoFinal + ganancia;
    const margen = (1 - _costoFinal / precio) * 100;

    document.getElementById('input-precio-venta').value = precio.toFixed(2);
    document.getElementById('input-margen').value       = margen.toFixed(1);

    actualizarHints(margen, _precioMinimo, _precioSugerido);
});

// Cuando el usuario escribe el precio directamente
document.getElementById('input-precio-venta').addEventListener('input', function () {
    if (!_costoFinal) return;
    const precio = parseFloat(this.value);
    if (isNaN(precio) || precio <= 0) return;

    const margen   = (1 - _costoFinal / precio) * 100;
    const ganancia = precio - _costoFinal;

    document.getElementById('input-margen').value   = margen.toFixed(1);
    document.getElementById('input-ganancia').value = ganancia.toFixed(2);

    actualizarHints(margen, _precioMinimo, _precioSugerido);
});

function actualizarHints(margen, minimo, sugerido) {
    const hintM = document.getElementById('hint-margen');
    const hintG = document.getElementById('hint-ganancia');
    const hintP = document.getElementById('hint-precio');

    // Limpiar clases
    [hintM, hintG, hintP].forEach(h => {
        h.className = 'input-hint';
        h.textContent = '';
    });

    if (margen < 30) {
        hintM.textContent = '⚠️ Bajo el mínimo permitido (30%)';
        hintM.classList.add('hint-error');
        hintP.textContent = '⚠️ Precio por debajo del mínimo';
        hintP.classList.add('hint-error');
    } else if (margen < 40) {
        const diff = (40 - margen).toFixed(1);
        hintM.textContent = `A ${diff}% del objetivo`;
        hintM.classList.add('hint-warn');
        hintP.textContent = 'Entre mínimo y objetivo';
        hintP.classList.add('hint-warn');
    } else {
        hintM.textContent = '✓ Por encima del objetivo';
        hintM.classList.add('hint-ok');
        hintP.textContent = '✓ Precio sobre objetivo';
        hintP.classList.add('hint-ok');
    }
}

async function guardarPrecioVenta() {
    const precio = parseFloat(
        document.getElementById('input-precio-venta').value
    );

    if (isNaN(precio) || precio <= 0) {
        alert('Captura un precio válido');
        return;
    }

    if (precio < _precioMinimo) {
        const confirmar = confirm(
            `El precio $${fmt(precio)} está por debajo del mínimo ($${fmt(_precioMinimo)}). ¿Confirmar de todas formas?`
        );
        if (!confirmar) return;
    }

    const respuesta = await fetchAuth(`${API_URL}/eventos/${eventoId}/precio-venta`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ precio_venta: precio })
    });

    if (!respuesta.ok) {
        alert('Error al guardar precio');
        return;
    }

    alert(`Precio $${fmt(precio)} guardado correctamente`);
}

async function generarPDF(tipo) {

    // window.open no puede mandar el header Authorization, y el endpoint
    // del PDF ahora exige token. Se abre la pestaña primero —de forma
    // sincrónica, para que el navegador no la bloquee como popup— y se le
    // carga el PDF descargado con fetchAuth.
    const ventana = window.open('', '_blank');

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/pdf?tipo=${tipo}`
    );

    if (!respuesta.ok) {
        if (ventana) ventana.close();
        alert('Error al generar el PDF');
        return;
    }

    const blob = await respuesta.blob();
    const url = URL.createObjectURL(blob);

    if (ventana) {
        ventana.location = url;
    } else {
        // La pestaña quedó bloqueada: al menos no se pierde el archivo
        window.location.href = url;
    }

    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// ══════════════════════════════════════════════
// Contrato: pagos recibidos y gastos reales
//
// Estas secciones solo aplican a eventos Confirmados. Los resúmenes
// siempre se releen del API después de cada alta, edición o borrado:
// nunca se acumulan totales en variables de JS.
// ══════════════════════════════════════════════

// Últimas listas traídas del API. Se usan para precargar los modales
// por id, en vez de serializar el objeto dentro del onclick: un
// concepto con apóstrofo rompería el atributo.
let _pagos = [];
let _gastosReales = [];

// Registro que se está editando; null cuando es un alta.
let _pagoEditando = null;
let _gastoEditando = null;

function mostrarSeccionesContrato() {
    document.getElementById('banner-contrato').style.display = 'none';
    document.getElementById('seccion-pagos').style.display = 'block';
    document.getElementById('seccion-gastos-reales').style.display = 'block';
}

function ocultarSeccionesContrato() {
    document.getElementById('banner-contrato').style.display = 'flex';
    document.getElementById('seccion-pagos').style.display = 'none';
    document.getElementById('seccion-gastos-reales').style.display = 'none';
}

// Fecha local de hoy en formato YYYY-MM-DD.
// toISOString() daría la fecha en UTC y de noche adelantaría un día.
function hoyISO() {
    const d = new Date();
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const dia = String(d.getDate()).padStart(2, '0');
    return `${d.getFullYear()}-${mes}-${dia}`;
}

// Los conceptos y notas son texto libre del usuario
function escapar(texto) {
    return String(texto ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}


// ── Pagos ──────────────────────────────────────

async function cargarPagos() {

    const respuesta = await fetchAuth(`${API_URL}/eventos/${eventoId}/pagos`);
    _pagos = await respuesta.json();

    const tbody = document.querySelector("#tabla-pagos tbody");
    tbody.innerHTML = "";

    if (_pagos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="tabla-vacia">
                    Todavía no hay pagos registrados para este evento.
                </td>
            </tr>
        `;
    }

    _pagos.forEach(pago => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${pago.fecha}</td>
            <td>${escapar(pago.concepto)}</td>
            <td><span class="metodo-chip">${escapar(pago.metodo)}</span></td>
            <td>$${fmt(pago.monto)}</td>

            <td>
                <div class="action-cell">
                    <button class="btn btn-secondary btn-sm"
                            onclick="editarPago(${pago.id})">
                        Editar
                    </button>

                    <button class="btn btn-danger btn-sm"
                            onclick="eliminarPago(${pago.id})">
                        Eliminar
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(fila);
    });

    await cargarResumenPagos();
}

async function cargarResumenPagos() {

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/pagos/resumen`
    );

    const resumen = await respuesta.json();

    document.getElementById('pago-precio-acordado').textContent =
        fmt(_precioVenta);
    document.getElementById('pago-total-pagado').textContent =
        fmt(resumen.total_pagado);

    // saldo_pendiente es null mientras el evento no tenga precio acordado
    const saldo = resumen.saldo_pendiente;
    const tarjeta = document.getElementById('kpi-saldo');

    document.getElementById('pago-saldo').textContent =
        saldo === null ? '—' : fmt(saldo);

    tarjeta.classList.remove('kpi-saldo-deuda', 'kpi-saldo-liquidado');
    tarjeta.classList.add(
        saldo !== null && saldo > 0
            ? 'kpi-saldo-deuda'
            : 'kpi-saldo-liquidado'
    );
}

function abrirModalPago() {

    _pagoEditando = null;

    document.getElementById('modal-pago-titulo').textContent =
        'Registrar Pago';

    document.getElementById('pago-fecha').value    = hoyISO();
    document.getElementById('pago-concepto').value = '';
    document.getElementById('pago-monto').value    = '';
    document.getElementById('pago-metodo').value   = 'Transferencia';
    document.getElementById('pago-notas').value    = '';

    document.getElementById('modal-pago').style.display = 'flex';
    document.getElementById('pago-concepto').focus();
}

function editarPago(pagoId) {

    const pago = _pagos.find(p => p.id === pagoId);
    if (!pago) return;

    _pagoEditando = pago;

    document.getElementById('modal-pago-titulo').textContent =
        'Editar Pago';

    document.getElementById('pago-fecha').value    = pago.fecha ?? hoyISO();
    document.getElementById('pago-concepto').value = pago.concepto ?? '';
    // Campo numérico: sin separador de miles
    document.getElementById('pago-monto').value    = Number(pago.monto).toFixed(2);
    document.getElementById('pago-metodo').value   = pago.metodo ?? 'Transferencia';
    document.getElementById('pago-notas').value    = pago.notas ?? '';

    document.getElementById('modal-pago').style.display = 'flex';
    document.getElementById('pago-concepto').focus();
}

function cerrarModalPago() {
    document.getElementById('modal-pago').style.display = 'none';
    _pagoEditando = null;
}

async function guardarPago() {

    const fecha = document.getElementById('pago-fecha').value;
    if (!fecha) {
        alert('Captura la fecha del pago');
        return;
    }

    const concepto = document.getElementById('pago-concepto').value.trim();
    if (concepto.length < 2) {
        alert('El concepto debe tener al menos 2 caracteres');
        return;
    }

    const monto = parseFloat(document.getElementById('pago-monto').value);
    if (isNaN(monto) || monto <= 0) {
        alert('El monto debe ser mayor a 0');
        return;
    }

    const metodo = document.getElementById('pago-metodo').value;
    const notas  = document.getElementById('pago-notas').value;

    const cuerpo = { fecha, concepto, monto, metodo, notas };

    const url = _pagoEditando
        ? `${API_URL}/eventos/${eventoId}/pagos/${_pagoEditando.id}`
        : `${API_URL}/eventos/${eventoId}/pagos`;

    const respuesta = await fetchAuth(url, {
        method: _pagoEditando ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo)
    });

    if (!respuesta.ok) {
        alert('Error al guardar el pago');
        return;
    }

    cerrarModalPago();

    // Recarga el evento completo: KPIs del resumen financiero,
    // pagos y gastos reales vuelven a leerse del API
    cargarEvento();
}

async function eliminarPago(pagoId) {

    const confirmar = confirm('¿Eliminar este pago?');
    if (!confirmar) return;

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/pagos/${pagoId}`,
        { method: 'DELETE' }
    );

    if (!respuesta.ok) {
        alert('Error al eliminar el pago');
        return;
    }

    cargarEvento();
}


// ── Gastos reales ──────────────────────────────

async function cargarGastosReales() {

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/gastos-reales`
    );

    _gastosReales = await respuesta.json();

    const tbody = document.querySelector("#tabla-gastos-reales tbody");
    tbody.innerHTML = "";

    if (_gastosReales.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="tabla-vacia">
                    Todavía no hay gastos reales registrados para este evento.
                </td>
            </tr>
        `;
    }

    _gastosReales.forEach(gasto => {

        const fila = document.createElement("tr");

        const reembolsable = gasto.es_reembolsable
            ? '<span class="reembolsable-si">Sí</span>'
            : '<span class="reembolsable-no">No</span>';

        fila.innerHTML = `
            <td>${gasto.fecha}</td>
            <td><span class="categoria-chip">${escapar(gasto.categoria)}</span></td>
            <td>${escapar(gasto.concepto)}</td>
            <td>$${fmt(gasto.monto)}</td>
            <td>${reembolsable}</td>

            <td>
                <div class="action-cell">
                    <button class="btn btn-secondary btn-sm"
                            onclick="editarGastoReal(${gasto.id})">
                        Editar
                    </button>

                    <button class="btn btn-danger btn-sm"
                            onclick="eliminarGastoReal(${gasto.id})">
                        Eliminar
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(fila);
    });

    await cargarResumenGastosReales();
}

async function cargarResumenGastosReales() {

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/gastos-reales/resumen`
    );

    const resumen = await respuesta.json();

    document.getElementById('gasto-total').textContent =
        fmt(resumen.total_gastos);
    document.getElementById('gasto-reembolsable').textContent =
        fmt(resumen.gastos_reembolsables);

    // Utilidad real = precio acordado - costo final - gastos reales
    const utilidad = _precioVenta - _costoFinal - resumen.total_gastos;

    document.getElementById('gasto-utilidad').textContent = fmt(utilidad);

    const tarjeta = document.getElementById('kpi-utilidad');
    tarjeta.classList.remove('kpi-utilidad-positiva', 'kpi-utilidad-negativa');
    tarjeta.classList.add(
        utilidad < 0 ? 'kpi-utilidad-negativa' : 'kpi-utilidad-positiva'
    );
}

function abrirModalGastoReal() {

    _gastoEditando = null;

    document.getElementById('modal-gasto-titulo').textContent =
        'Registrar Gasto Real';

    document.getElementById('gasto-fecha').value     = hoyISO();
    document.getElementById('gasto-categoria').value = '';
    document.getElementById('gasto-concepto').value  = '';
    document.getElementById('gasto-monto').value     = '';
    document.getElementById('gasto-notas').value     = '';
    document.getElementById('gasto-reembolsable-check').checked = false;

    document.getElementById('modal-gasto-real').style.display = 'flex';
    document.getElementById('gasto-categoria').focus();
}

function editarGastoReal(gastoId) {

    const gasto = _gastosReales.find(g => g.id === gastoId);
    if (!gasto) return;

    _gastoEditando = gasto;

    document.getElementById('modal-gasto-titulo').textContent =
        'Editar Gasto Real';

    document.getElementById('gasto-fecha').value     = gasto.fecha ?? hoyISO();
    document.getElementById('gasto-categoria').value = gasto.categoria ?? '';
    document.getElementById('gasto-concepto').value  = gasto.concepto ?? '';
    // Campo numérico: sin separador de miles
    document.getElementById('gasto-monto').value     = Number(gasto.monto).toFixed(2);
    document.getElementById('gasto-notas').value     = gasto.notas ?? '';
    document.getElementById('gasto-reembolsable-check').checked =
        Boolean(gasto.es_reembolsable);

    document.getElementById('modal-gasto-real').style.display = 'flex';
    document.getElementById('gasto-categoria').focus();
}

function cerrarModalGastoReal() {
    document.getElementById('modal-gasto-real').style.display = 'none';
    _gastoEditando = null;
}

async function guardarGastoReal() {

    const fecha = document.getElementById('gasto-fecha').value;
    if (!fecha) {
        alert('Captura la fecha del gasto');
        return;
    }

    const categoria = document.getElementById('gasto-categoria').value.trim();
    if (categoria.length < 2) {
        alert('La categoría debe tener al menos 2 caracteres');
        return;
    }

    const concepto = document.getElementById('gasto-concepto').value.trim();
    if (concepto.length < 2) {
        alert('El concepto debe tener al menos 2 caracteres');
        return;
    }

    const monto = parseFloat(document.getElementById('gasto-monto').value);
    if (isNaN(monto) || monto <= 0) {
        alert('El monto debe ser mayor a 0');
        return;
    }

    const es_reembolsable =
        document.getElementById('gasto-reembolsable-check').checked;
    const notas = document.getElementById('gasto-notas').value;

    const cuerpo = {
        fecha,
        categoria,
        concepto,
        monto,
        es_reembolsable,
        notas
    };

    const url = _gastoEditando
        ? `${API_URL}/eventos/${eventoId}/gastos-reales/${_gastoEditando.id}`
        : `${API_URL}/eventos/${eventoId}/gastos-reales`;

    const respuesta = await fetchAuth(url, {
        method: _gastoEditando ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cuerpo)
    });

    if (!respuesta.ok) {
        alert('Error al guardar el gasto');
        return;
    }

    cerrarModalGastoReal();
    cargarEvento();
}

async function eliminarGastoReal(gastoId) {

    const confirmar = confirm('¿Eliminar este gasto?');
    if (!confirmar) return;

    const respuesta = await fetchAuth(
        `${API_URL}/eventos/${eventoId}/gastos-reales/${gastoId}`,
        { method: 'DELETE' }
    );

    if (!respuesta.ok) {
        alert('Error al eliminar el gasto');
        return;
    }

    cargarEvento();
}


// ── Cierre de los modales de contrato ──────────

// Clic fuera de la tarjeta
document.getElementById('modal-pago')
    .addEventListener('click', function (e) {
        if (e.target === this) cerrarModalPago();
    });

document.getElementById('modal-gasto-real')
    .addEventListener('click', function (e) {
        if (e.target === this) cerrarModalGastoReal();
    });

// Escape cierra el modal abierto (accesibilidad de teclado)
document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;

    if (document.getElementById('modal-pago').style.display === 'flex') {
        cerrarModalPago();
    }
    if (document.getElementById('modal-gasto-real').style.display === 'flex') {
        cerrarModalGastoReal();
    }
    if (document.getElementById('modal-gastos').style.display === 'flex') {
        cerrarModalGastos();
    }
});


// INIT (UNA SOLA VEZ)
cargarEvento();
cargarArreglos();