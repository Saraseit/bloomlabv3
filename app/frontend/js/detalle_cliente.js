const params = new URLSearchParams(window.location.search);
const clienteId = params.get('id');

// Los nombres, empresas y conceptos son texto libre del usuario
function escapar(texto) {
    return String(texto ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Mismas clases de badge que usa la tabla de eventos
function claseEstatus(estatus) {
    const texto = (estatus ?? '').toLowerCase();

    if (texto.includes('cotiz')) return 'badge badge-cotizacion';
    if (texto.includes('confirm') || texto.includes('activo')) return 'badge badge-confirmado';
    if (texto.includes('complet') || texto.includes('entregado')) return 'badge badge-completado';
    if (texto.includes('cancel')) return 'badge badge-cancelado';

    return 'badge badge-default';
}

async function cargarCliente() {

    const respuesta = await fetch(
        `${API_URL}/clientes/${clienteId}/detalle`
    );

    const cliente = await respuesta.json();

    if (cliente.error) {
        document.getElementById('nombre-cliente').textContent =
            'Cliente no encontrado';
        return;
    }

    // ── Ficha de contacto ──
    document.getElementById('nombre-cliente').textContent = cliente.nombre;

    document.getElementById('empresa').textContent =
        cliente.empresa || '—';

    const telefono = document.getElementById('telefono');
    if (cliente.telefono) {
        telefono.innerHTML =
            `<a class="contact-link" href="tel:${escapar(cliente.telefono).replace(/\s/g, '')}">` +
            `${escapar(cliente.telefono)}</a>`;
    } else {
        telefono.textContent = '—';
    }

    const email = document.getElementById('email');
    if (cliente.email) {
        email.innerHTML =
            `<a class="contact-link" href="mailto:${escapar(cliente.email)}">` +
            `${escapar(cliente.email)}</a>`;
    } else {
        email.textContent = '—';
    }

    document.getElementById('comision').innerHTML =
        `<span class="comision-chip">${fmtPct(cliente.comision_porcentaje)}</span>`;

    // ── KPIs ──
    document.getElementById('total-eventos').textContent =
        cliente.total_eventos ?? 0;
    document.getElementById('eventos-confirmados').textContent =
        cliente.eventos_confirmados ?? 0;
    document.getElementById('total-facturado').textContent =
        fmt(cliente.total_facturado);
    document.getElementById('total-cobrado').textContent =
        fmt(cliente.total_cobrado);
    document.getElementById('deuda-total').textContent =
        fmt(cliente.deuda_total);

    const tarjetaDeuda = document.getElementById('kpi-deuda');
    tarjetaDeuda.classList.remove('kpi-deuda-pendiente', 'kpi-deuda-saldada');
    tarjetaDeuda.classList.add(
        cliente.deuda_total > 0
            ? 'kpi-deuda-pendiente'
            : 'kpi-deuda-saldada'
    );

    // ── Historial de eventos ──
    const tbody = document.querySelector('#tabla-eventos-cliente tbody');
    tbody.innerHTML = '';

    const eventos = cliente.eventos || [];

    if (eventos.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="tabla-vacia">
                    Este cliente todavía no tiene eventos registrados.
                </td>
            </tr>
        `;
        return;
    }

    eventos.forEach(evento => {

        const fila = document.createElement('tr');

        // Sin precio acordado todavía no hay saldo que mostrar
        const precio = evento.precio_venta;
        const pagado = evento.pagado ?? 0;
        const saldo = precio === null ? null : precio - pagado;

        if (saldo !== null && saldo > 0) {
            fila.className = 'fila-con-saldo';
        } else if (saldo !== null && evento.estatus === 'Confirmado') {
            fila.className = 'fila-liquidada';
        }

        const celdaTipo = evento.tipo_evento
            ? `<span class="tipo-chip">${escapar(evento.tipo_evento)}</span>`
            : '<span class="sin-dato">—</span>';

        const celdaPrecio = precio === null
            ? '<span class="sin-dato">—</span>'
            : `$${fmt(precio)}`;

        const celdaSaldo = saldo === null
            ? '<span class="sin-dato">—</span>'
            : `<span class="${saldo > 0 ? 'saldo-pendiente' : 'saldo-cero'}">` +
              `$${fmt(saldo)}</span>`;

        fila.innerHTML = `
            <td>${evento.fecha_evento ?? ''}</td>
            <td>${escapar(evento.nombre)}</td>
            <td>${celdaTipo}</td>
            <td>
                <span class="${claseEstatus(evento.estatus)}">
                    ${escapar(evento.estatus)}
                </span>
            </td>
            <td>${celdaPrecio}</td>
            <td>$${fmt(pagado)}</td>
            <td>${celdaSaldo}</td>

            <td>
                <button class="btn btn-secondary btn-sm"
                        onclick="verEvento(${evento.id})">
                    Ver evento
                </button>
            </td>
        `;

        tbody.appendChild(fila);
    });
}

function verEvento(id) {
    window.location.href = `detalle_evento.html?id=${id}`;
}

// INIT
cargarCliente();
