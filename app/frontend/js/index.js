const MESES = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
];

const DIAS = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

const COLORES_ESTATUS = {
    "Cotizacion":             { bg: "#e6f1fb", text: "#0c447c", border: "#93c5fd" },
    "Confirmado":             { bg: "#eaf6e1", text: "#1a5c2e", border: "#86efac" },
    "Pendiente Autorización": { bg: "#fffbeb", text: "#92400e", border: "#fde68a" },
    "Cancelado":              { bg: "#fef2f2", text: "#991b1b", border: "#fca5a5" },
};

let mesActual  = new Date().getMonth();
let anioActual = new Date().getFullYear();
let todosLosEventos = [];

async function cargarEventos() {
    const respuesta = await fetch(`${API_URL}/eventos`);
    const data      = await respuesta.json();
    todosLosEventos = data;
    renderCalendario();
}

function renderCalendario() {
    const titulo = document.getElementById("cal-titulo");
    titulo.textContent = `${MESES[mesActual]} ${anioActual}`;

    const grid = document.getElementById("cal-grid");
    grid.innerHTML = "";

    // Cabecera de días
    DIAS.forEach(dia => {
        const header = document.createElement("div");
        header.className = "cal-dia-header";
        header.textContent = dia;
        grid.appendChild(header);
    });

    // Primer día del mes y total de días
    const primerDia  = new Date(anioActual, mesActual, 1).getDay();
    const totalDias  = new Date(anioActual, mesActual + 1, 0).getDate();
    const hoy        = new Date();

    // Celdas vacías antes del día 1
    for (let i = 0; i < primerDia; i++) {
        const vacio = document.createElement("div");
        vacio.className = "cal-celda cal-vacio";
        grid.appendChild(vacio);
    }

    // Días del mes
    for (let dia = 1; dia <= totalDias; dia++) {
        const celda = document.createElement("div");
        celda.className = "cal-celda";

        const esHoy = (
            dia === hoy.getDate() &&
            mesActual  === hoy.getMonth() &&
            anioActual === hoy.getFullYear()
        );
        if (esHoy) celda.classList.add("cal-hoy");

        const numDiv = document.createElement("div");
        numDiv.className = "cal-num";
        numDiv.textContent = dia;
        celda.appendChild(numDiv);

        // Eventos de este día
        const fechaDia = `${anioActual}-${String(mesActual + 1).padStart(2,"0")}-${String(dia).padStart(2,"0")}`;
        const eventosDelDia = todosLosEventos.filter(e => {
            if (!e.fecha_evento) return false;
            return e.fecha_evento.slice(0, 10) === fechaDia;
        });

        eventosDelDia.forEach(evento => {
            const color = COLORES_ESTATUS[evento.estatus] || COLORES_ESTATUS["Cotizacion"];
            const chip  = document.createElement("a");
            chip.className   = "cal-chip";
            chip.href        = `detalle_evento.html?id=${evento.id}`;
            chip.textContent = evento.nombre;
            chip.style.cssText = `
                background:${color.bg};
                color:${color.text};
                border-left: 3px solid ${color.border};
            `;
            celda.appendChild(chip);
        });

        grid.appendChild(celda);
    }
}

function mesAnterior() {
    if (mesActual === 0) { mesActual = 11; anioActual--; }
    else { mesActual--; }
    renderCalendario();
}

function mesSiguiente() {
    if (mesActual === 11) { mesActual = 0; anioActual++; }
    else { mesActual++; }
    renderCalendario();
}

cargarEventos();