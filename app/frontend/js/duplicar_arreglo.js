// ============================================================
//  BloomLab · Duplicar un arreglo del catálogo
//  Lo usan la tabla de arreglos y el detalle del arreglo.
//  Pide el nombre del nuevo, lo crea con la misma receta, foto y
//  descripción, y abre su detalle para ajustarlo.
// ============================================================

let _duplicandoArreglo = false;

async function duplicarArregloCatalogo(arreglo) {

    if (!arreglo || _duplicandoArreglo) return;

    const datos = await ui.formulario({
        titulo: "Duplicar arreglo",
        descripcion: `Se crea un arreglo nuevo con la receta, la foto y la descripción de ${arreglo.codigo}. ` +
            "Después lo puedes cambiar sin tocar el original ni los eventos que lo usan.",
        textoAceptar: "Duplicar",
        campos: [
            { nombre: "nombre", etiqueta: "Nombre del arreglo nuevo", valor: `${arreglo.nombre} (copia)`,
              requerido: true, completo: true },
        ],
        validar: d => (d.nombre || "").trim() ? null : "Escribe el nombre del arreglo nuevo",
    });
    if (!datos) return;

    _duplicandoArreglo = true;
    let respuesta;
    try {
        respuesta = await fetchAuth(`${API_URL}/arreglos/${arreglo.id}/duplicar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nombre: datos.nombre.trim() }),
        });
    } finally {
        _duplicandoArreglo = false;
    }

    if (!respuesta.ok) {
        ui.aviso("Error al duplicar el arreglo");
        return;
    }

    const nuevo = await respuesta.json();
    const insumos = nuevo.insumos === 1 ? "1 insumo" : `${nuevo.insumos} insumos`;
    ui.avisoAlLlegar(
        `Se creó ${nuevo.codigo} · ${datos.nombre.trim()}, copia de ${nuevo.codigo_original} con ${insumos}`,
        "ok"
    );
    window.location.href = `detalle_arreglo.html?id=${nuevo.id}`;
}
