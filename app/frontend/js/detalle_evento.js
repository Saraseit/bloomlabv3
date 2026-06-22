const parametros = new URLSearchParams(window.location.search);
const eventoId = parametros.get("id");

async function cargarEvento() {

    const respuesta = await fetch(
        `${API_URL}/eventos/${eventoId}`
    );

    const evento = await respuesta.json();

    document.getElementById("nombre-evento").textContent = evento.nombre;
    document.getElementById("cliente").textContent = evento.cliente;
    document.getElementById("fecha-evento").textContent = evento.fecha_evento;
    document.getElementById("lugar").textContent = evento.lugar ?? "";
    document.getElementById("descripcion").textContent = evento.descripcion ?? "";
    document.getElementById("costo-base").textContent = evento.costo_base ?? 0;
    document.getElementById('valor-flete').textContent   =
    (evento.costo_flete   ?? 0).toFixed(2);
    document.getElementById('valor-montaje').textContent =
    (evento.costo_montaje ?? 0).toFixed(2);
    document.getElementById("comision-porcentaje").textContent = evento.comision_porcentaje ?? 0;
    document.getElementById("importe-comision").textContent = evento.importe_comision ?? 0;
    document.getElementById("costo-final").textContent = evento.costo_final ?? 0;
    document.getElementById("precio-minimo").textContent = evento.precio_minimo ?? 0;
    document.getElementById("precio-sugerido").textContent = evento.precio_sugerido ?? 0;

    const tbody = document.querySelector("#tabla-evento-arreglos tbody");

    tbody.innerHTML = "";

    (evento.arreglos || []).forEach(arreglo => {

        const fila = document.createElement("tr");

        fila.innerHTML = `
            <td>${arreglo.codigo}</td>
            <td>${arreglo.nombre}</td>
            <td>${arreglo.cantidad}</td>
            <td>${arreglo.costo_unitario}</td>
            <td>${arreglo.subtotal}</td>
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
}

async function cargarArreglos() {

    const respuesta = await fetch(`${API_URL}/arreglos`);

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

    const respuesta = await fetch(`${API_URL}/evento-arreglos`, {
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

    const respuesta = await fetch(
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

    await fetch(
        `${API_URL}/evento-arreglos/${id}`,
        {
            method: "DELETE"
        }
    );

    cargarEvento();
}

// ── Gastos operativos ──────────────────────────

function abrirModalGastos() {
    // Precarga con valores actuales
    const flete   = document.getElementById('valor-flete').textContent;
    const montaje = document.getElementById('valor-montaje').textContent;
    document.getElementById('input-flete').value   = parseFloat(flete)   || 0;
    document.getElementById('input-montaje').value = parseFloat(montaje) || 0;

    const modal = document.getElementById('modal-gastos');
    modal.style.display = 'flex';
}

function cerrarModalGastos() {
    document.getElementById('modal-gastos').style.display = 'none';
}

async function guardarGastos() {
    const costo_flete   = parseFloat(document.getElementById('input-flete').value)   || 0;
    const costo_montaje = parseFloat(document.getElementById('input-montaje').value) || 0;

    const respuesta = await fetch(`${API_URL}/eventos/${eventoId}/gastos`, {
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

let _costoFinal = 0;  // se actualiza cada vez que carga el evento

function iniciarNegociacion(costoFinal, precioMinimo, precioSugerido, precioVenta) {
    _costoFinal = costoFinal;

    // Referencias visuales
    document.getElementById('ref-precio-minimo').textContent   = precioMinimo.toFixed(2);
    document.getElementById('ref-precio-sugerido').textContent = precioSugerido.toFixed(2);

    // Si ya hay precio acordado, precarga los campos
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

    const minimo    = parseFloat(document.getElementById('ref-precio-minimo').textContent);
    const sugerido  = parseFloat(document.getElementById('ref-precio-sugerido').textContent);
    actualizarHints(margen, minimo, sugerido);
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

    const minimo   = parseFloat(document.getElementById('ref-precio-minimo').textContent);
    const sugerido = parseFloat(document.getElementById('ref-precio-sugerido').textContent);
    actualizarHints(margen, minimo, sugerido);
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

    const minimo   = parseFloat(document.getElementById('ref-precio-minimo').textContent);
    const sugerido = parseFloat(document.getElementById('ref-precio-sugerido').textContent);
    actualizarHints(margen, minimo, sugerido);
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

    const minimo = parseFloat(
        document.getElementById('ref-precio-minimo').textContent
    );

    if (precio < minimo) {
        const confirmar = confirm(
            `El precio $${precio.toFixed(2)} está por debajo del mínimo ($${minimo.toFixed(2)}). ¿Confirmar de todas formas?`
        );
        if (!confirmar) return;
    }

    const respuesta = await fetch(`${API_URL}/eventos/${eventoId}/precio-venta`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ precio_venta: precio })
    });

    if (!respuesta.ok) {
        alert('Error al guardar precio');
        return;
    }

    alert(`Precio $${precio.toFixed(2)} guardado correctamente`);
}

function generarPDF(tipo) {
    window.open(`${API_URL}/eventos/${eventoId}/pdf?tipo=${tipo}`, '_blank');
}

// INIT (UNA SOLA VEZ)
cargarEvento();
cargarArreglos();