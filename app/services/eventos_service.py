from app.database.connection import get_connection
from app.services.compras_service import (
    calcular_costo_sobrante,
    copiar_insumos_congelados
)
from app.services.configuracion_service import obtener_parametros
from app.services.precios import (
    precio_para_margen,
    resultado_para_precio,
    repartir_por_arreglo
)

def obtener_eventos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,

            e.cliente_id,

            c.nombre AS cliente,

            e.nombre,

            e.tipo_evento,

            e.fecha_evento,

            e.lugar,

            e.descripcion,

            e.estatus,

            e.comision_porcentaje,

            e.costo_base,

            e.costo_final,

            e.precio_minimo,

            e.precio_sugerido,

            e.activo,

            e.fecha_creacion

        FROM eventos e

        INNER JOIN clientes c
            ON e.cliente_id = c.id

        WHERE e.activo = TRUE

        ORDER BY e.fecha_evento
    """)

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
        
    ]

    cur.close()
    conn.close()

    return resultado

def crear_evento(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO eventos (

            cliente_id,
            nombre,
            tipo_evento,
            fecha_evento,
            lugar,
            descripcion,
            estatus,
            comision_porcentaje,
            activo

        )
        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            TRUE

        )
        RETURNING id
    """, (

        data.cliente_id,
        data.nombre,
        data.tipo_evento,
        data.fecha_evento,
        data.lugar,
        data.descripcion,
        data.estatus,
        data.comision_porcentaje

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Evento creado",
        "id": nuevo_id
    }

def actualizar_evento(evento_id, data, usuario=None):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT estatus FROM eventos WHERE id = %s", (evento_id,))
    fila = cur.fetchone()
    estatus_anterior = fila[0] if fila else None

    cur.execute("""
        UPDATE eventos
        SET
            cliente_id = %s,
            nombre = %s,
            tipo_evento = %s,
            fecha_evento = %s,
            lugar = %s,
            descripcion = %s,
            estatus = %s
        WHERE id = %s
    """, (

        data.cliente_id,
        data.nombre,
        data.tipo_evento,
        data.fecha_evento,
        data.lugar,
        data.descripcion,
        data.estatus,
        evento_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    if data.estatus == "Confirmado" and estatus_anterior != "Confirmado":
        guardar_foto(evento_id, "confirmado", usuario)

    return {
        "mensaje": "Evento actualizado"
    }

def eliminar_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE eventos
        SET activo = FALSE
        WHERE id = %s
    """, (evento_id,))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Evento eliminado"
    }

def _calcular_totales(cur, evento_id):
    """Totales del evento con la fórmula de services/precios.py.

    No escribe nada. El precio de referencia es el acordado si existe; si
    no, el sugerido. Ganancia y margen se miden a ese precio; la comisión
    no depende del precio.
    """
    cur.execute("""
        SELECT costo_flete, costo_montaje, comision_porcentaje, precio_venta
        FROM eventos
        WHERE id = %s
    """, (evento_id,))
    fila = cur.fetchone()
    if not fila:
        return None

    costo_flete   = float(fila[0] or 0)
    costo_montaje = float(fila[1] or 0)
    comision_pct  = float(fila[2] or 0)
    precio_venta  = float(fila[3]) if fila[3] is not None else None

    cur.execute("""
        SELECT COALESCE(SUM(subtotal), 0)
        FROM evento_arreglos
        WHERE evento_id = %s
    """, (evento_id,))
    costo_arreglos = float(cur.fetchone()[0])

    # Paquetes incompletos: costo de material de los arreglos
    costo_sobrante = calcular_costo_sobrante(cur, evento_id)

    parametros = obtener_parametros(cur)
    comision   = comision_pct / 100
    traslados  = costo_flete + costo_montaje

    precio_minimo = precio_para_margen(
        costo_arreglos, costo_sobrante, traslados, comision,
        parametros["margen_minimo"] / 100
    )
    precio_sugerido = precio_para_margen(
        costo_arreglos, costo_sobrante, traslados, comision,
        parametros["margen_objetivo"] / 100
    )

    if precio_venta is not None and precio_venta > 0:
        precio_referencia, tipo_precio = precio_venta, "acordado"
    elif precio_sugerido is not None:
        precio_referencia, tipo_precio = precio_sugerido, "sugerido"
    else:
        precio_referencia, tipo_precio = None, None

    resultado = (
        resultado_para_precio(
            costo_arreglos, costo_sobrante, traslados, comision, precio_referencia
        )
        if precio_referencia is not None else None
    )

    # Montos en centavos, iguales a la suma de las partidas
    sobrante_cent = round(costo_sobrante, 2)
    comision_cent = round(resultado["comision"], 2) if resultado else 0.0
    arreglos_cent = round(resultado["precio_arreglos"], 2) if resultado else 0.0
    ganancia_cent = (
        round(arreglos_cent - round(costo_arreglos, 2) - sobrante_cent - comision_cent, 2)
        if resultado else None
    )

    costo_directo = costo_arreglos + costo_sobrante + traslados

    return {
        "costo_arreglos":    costo_arreglos,
        "costo_flete":       costo_flete,
        "costo_montaje":     costo_montaje,
        "costo_sobrante":    costo_sobrante,
        "costo_directo":     costo_directo,
        "comision_pct":      comision_pct,
        "comision_importe":  comision_cent,
        # Todo lo que no es ganancia: costos + comisión.
        # Reportes y utilidad real usan precio - costo_final.
        "costo_final":       costo_directo + comision_cent,
        "precio_minimo":     precio_minimo,
        "precio_sugerido":   precio_sugerido,
        "precio_venta":      precio_venta,
        "precio_referencia": precio_referencia,
        "tipo_precio":       tipo_precio,
        "precio_arreglos":   arreglos_cent if resultado else None,
        "ganancia":          ganancia_cent,
        # Margen sobre el precio de los arreglos (la ganancia solo va en arreglos)
        "margen":            resultado["margen"] if resultado else None,
        "parametros":        parametros,
        "advertencia":       None,
    }


def _partidas_evento(cur, evento_id, t):
    """Arreglos del evento con su desglose: sobrante, comisión, ganancia y precio final."""
    cur.execute("""
        SELECT

            ea.id,
            ea.arreglo_id,
            a.codigo,
            a.nombre,
            a.imagen_url,
            ea.cantidad,
            ea.costo_unitario,
            ea.subtotal,
            ea.observaciones

        FROM evento_arreglos ea

        INNER JOIN arreglos a
            ON ea.arreglo_id = a.id

        WHERE ea.evento_id = %s

        ORDER BY ea.id

    """, (evento_id,))

    columnas = [desc[0] for desc in cur.description]
    arreglos = [dict(zip(columnas, fila)) for fila in cur.fetchall()]

    desglose = repartir_por_arreglo(
        [float(a["subtotal"] or 0) for a in arreglos],
        t["costo_sobrante"],
        t["comision_pct"] / 100,
        t["precio_arreglos"] or 0.0,
    )

    for arreglo, d in zip(arreglos, desglose):
        cantidad = float(arreglo["cantidad"] or 0)
        arreglo["sobrante_asignado"]     = d["sobrante"]
        arreglo["comision_porcentaje"]   = _redondear(t["comision_pct"])
        arreglo["comision_importe"]      = d["comision"]
        arreglo["ganancia_importe"]      = d["ganancia"]
        arreglo["precio_final"]          = d["precio_final"]
        arreglo["precio_final_unitario"] = round(d["precio_final"] / cantidad, 2) if cantidad else 0.0

    return arreglos


def actualizar_totales_evento(evento_id):
    """Recalcula y guarda los totales del evento y el desglose de sus partidas."""

    conn = get_connection()
    cur = conn.cursor()

    t = _calcular_totales(cur, evento_id)
    if t is None:
        cur.close()
        conn.close()
        return None

    cur.execute("""
        UPDATE eventos
        SET
            costo_base       = %s,
            costo_sobrante   = %s,
            comision_importe = %s,
            costo_final      = %s,
            precio_minimo    = %s,
            precio_sugerido  = %s,
            ganancia_importe = %s,
            margen_arreglos  = %s
        WHERE id = %s
    """, (
        t["costo_arreglos"],
        t["costo_sobrante"],
        t["comision_importe"],
        t["costo_final"],
        t["precio_minimo"],
        t["precio_sugerido"],
        t["ganancia"] or 0,
        t["margen"],
        evento_id,
    ))

    # Valores vigentes por partida: se recalculan con cada cambio del evento
    partidas = _partidas_evento(cur, evento_id, t)
    cur.executemany("""
        UPDATE evento_arreglos
        SET
            sobrante_asignado     = %s,
            comision_importe      = %s,
            ganancia_importe      = %s,
            precio_final          = %s,
            precio_final_unitario = %s
        WHERE id = %s
    """, [
        (p["sobrante_asignado"], p["comision_importe"], p["ganancia_importe"],
         p["precio_final"], p["precio_final_unitario"], p["id"])
        for p in partidas
    ])

    conn.commit()
    cur.close()
    conn.close()
    return t


def _redondear(valor, decimales=2):
    return round(valor, decimales) if valor is not None else None


def obtener_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,
            e.cliente_id,
            c.nombre AS cliente,
            e.nombre,
            e.tipo_evento,
            e.fecha_evento,
            e.lugar,
            e.descripcion,
            e.estatus,
            e.nota_autorizacion,
            e.activo,
            e.fecha_creacion

        FROM eventos e

        INNER JOIN clientes c
            ON e.cliente_id = c.id

        WHERE e.id = %s

    """, (evento_id,))

    evento = cur.fetchone()

    if not evento:
        cur.close()
        conn.close()
        return {"error": "Evento no encontrado"}

    columnas = [desc[0] for desc in cur.description]
    resultado = dict(zip(columnas, evento))

    # Totales al momento, con la fórmula de margen
    t = _calcular_totales(cur, evento_id)

    resultado.update({
        "costo_arreglos":      _redondear(t["costo_arreglos"]),
        # costo_base se conserva por compatibilidad: es el costo de arreglos
        "costo_base":          _redondear(t["costo_arreglos"]),
        "costo_flete":         _redondear(t["costo_flete"]),
        "costo_montaje":       _redondear(t["costo_montaje"]),
        "costo_sobrante":      _redondear(t["costo_sobrante"]),
        "costo_directo":       _redondear(t["costo_directo"]),
        "comision_porcentaje": _redondear(t["comision_pct"]),
        "importe_comision":    t["comision_importe"],
        "costo_final":         _redondear(t["costo_final"]),
        "precio_minimo":       _redondear(t["precio_minimo"]),
        "precio_sugerido":     _redondear(t["precio_sugerido"]),
        "precio_venta":        _redondear(t["precio_venta"]),
        "precio_referencia":   _redondear(t["precio_referencia"]),
        "precio_arreglos":     t["precio_arreglos"],
        "tipo_precio":         t["tipo_precio"],
        "ganancia":            t["ganancia"],
        "margen_efectivo":     _redondear(t["margen"] * 100) if t["margen"] is not None else None,
        "parametros":          t["parametros"],
        "advertencia":         t["advertencia"],
        "arreglos":            _partidas_evento(cur, evento_id, t),
    })

    cur.close()
    conn.close()

    return resultado


# ── Fotografías de la cotización ──────────────

MOTIVOS_FOTO = {
    "precio_acordado":        "Precio acordado",
    "comision":               "Cambio de comisión",
    "confirmado":             "Evento confirmado",
    "autorizacion_aprobada":  "Precio autorizado",
    "autorizacion_rechazada": "Precio rechazado",
    "manual":                 "Fotografía manual",
}


def guardar_foto(evento_id, motivo, usuario=None):
    """Guarda el estado completo de la cotización y sus partidas.

    Queda fija aunque después cambien el evento, el catálogo o los
    márgenes: sirve para reportes de lo que realmente se cotizó.
    """
    conn = get_connection()
    cur = conn.cursor()

    t = _calcular_totales(cur, evento_id)
    if t is None:
        cur.close()
        conn.close()
        return None

    cur.execute("SELECT estatus FROM eventos WHERE id = %s", (evento_id,))
    estatus = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO evento_fotos (
            evento_id, motivo, creado_por, estatus, tipo_precio, precio_total,
            costo_arreglos, costo_sobrante, costo_flete, costo_montaje,
            comision_porcentaje, comision_importe, ganancia_importe,
            margen_arreglos, margen_minimo, margen_objetivo
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        evento_id, motivo, usuario["nombre"] if usuario else None, estatus,
        t["tipo_precio"], _redondear(t["precio_referencia"]),
        t["costo_arreglos"], t["costo_sobrante"], t["costo_flete"], t["costo_montaje"],
        t["comision_pct"], t["comision_importe"], t["ganancia"],
        t["margen"], t["parametros"]["margen_minimo"], t["parametros"]["margen_objetivo"],
    ))
    foto_id = cur.fetchone()[0]

    partidas = _partidas_evento(cur, evento_id, t)
    cur.executemany("""
        INSERT INTO evento_foto_partidas (
            foto_id, evento_arreglo_id, arreglo_id, codigo, nombre, cantidad,
            costo, sobrante, comision, ganancia, precio_final, precio_final_unitario
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        (foto_id, p["id"], p["arreglo_id"], p["codigo"], p["nombre"], p["cantidad"],
         p["subtotal"], p["sobrante_asignado"], p["comision_importe"], p["ganancia_importe"],
         p["precio_final"], p["precio_final_unitario"])
        for p in partidas
    ])

    conn.commit()
    cur.close()
    conn.close()
    return foto_id


def listar_fotos(evento_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, motivo, creado_en, creado_por, estatus, tipo_precio, precio_total,
               comision_porcentaje, comision_importe, ganancia_importe, margen_arreglos
        FROM evento_fotos
        WHERE evento_id = %s
        ORDER BY creado_en DESC, id DESC
    """, (evento_id,))
    columnas = [desc[0] for desc in cur.description]
    fotos = [dict(zip(columnas, fila)) for fila in cur.fetchall()]
    cur.close()
    conn.close()
    for f in fotos:
        f["motivo_texto"] = MOTIVOS_FOTO.get(f["motivo"], f["motivo"])
    return fotos


def obtener_foto(evento_id, foto_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM evento_fotos
        WHERE id = %s AND evento_id = %s
    """, (foto_id, evento_id))
    fila = cur.fetchone()
    if not fila:
        cur.close()
        conn.close()
        return None
    foto = dict(zip([d[0] for d in cur.description], fila))
    cur.execute("""
        SELECT evento_arreglo_id, arreglo_id, codigo, nombre, cantidad, costo, sobrante,
               comision, ganancia, precio_final, precio_final_unitario
        FROM evento_foto_partidas
        WHERE foto_id = %s
        ORDER BY id
    """, (foto_id,))
    columnas = [desc[0] for desc in cur.description]
    foto["partidas"] = [dict(zip(columnas, f)) for f in cur.fetchall()]
    foto["motivo_texto"] = MOTIVOS_FOTO.get(foto["motivo"], foto["motivo"])
    cur.close()
    conn.close()
    return foto


def _revisar_autorizacion(evento_id, usuario):
    """Si un vendedor deja el margen bajo el umbral, el evento espera autorización.

    Aplica cuando hay precio acordado; con precio sugerido no hay nada que
    autorizar todavía. Devuelve (requiere_autorizacion, totales).
    """
    conn = get_connection()
    cur = conn.cursor()

    t = _calcular_totales(cur, evento_id)
    umbral = t["parametros"]["margen_autorizacion"] / 100
    # Sin precio de arreglos (precio menor que flete + montaje) no hay margen
    margen = t["margen"] if t["margen"] is not None else float("-inf")

    requiere = (
        t["tipo_precio"] == "acordado"
        and usuario["rol"] == "vendedor"
        and margen < umbral
    )

    if requiere:
        cur.execute("""
            UPDATE eventos
            SET estatus = 'Pendiente Autorización'
            WHERE id = %s
        """, (evento_id,))
        conn.commit()

    cur.close()
    conn.close()
    return requiere, t


def _margen_pct(t):
    return round(t["margen"] * 100, 2) if t["margen"] is not None else None


def fijar_precio_venta(evento_id, precio_venta, usuario):

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE eventos
        SET precio_venta = %s
        WHERE id = %s
        RETURNING id
    """, (precio_venta, evento_id))
    existe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not existe:
        return {"error": "Evento no encontrado"}

    actualizar_totales_evento(evento_id)
    requiere, t = _revisar_autorizacion(evento_id, usuario)
    guardar_foto(evento_id, "precio_acordado", usuario)

    return {
        "mensaje": "Precio guardado",
        "requiere_autorizacion": requiere,
        "margen": _margen_pct(t),
        "ganancia": t["ganancia"],
        "comision": t["comision_importe"],
    }


def actualizar_comision(evento_id, porcentaje, usuario):

    if porcentaje < 0 or porcentaje >= 100:
        return {"error": "La comisión debe estar entre 0 y 99.99%."}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE eventos
        SET comision_porcentaje = %s
        WHERE id = %s
        RETURNING id
    """, (porcentaje, evento_id))
    existe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not existe:
        return {"error": "Evento no encontrado"}

    actualizar_totales_evento(evento_id)

    # Más comisión = menos ganancia al precio ya acordado
    requiere, t = _revisar_autorizacion(evento_id, usuario)
    guardar_foto(evento_id, "comision", usuario)

    return {
        "mensaje": "Comisión actualizada",
        "requiere_autorizacion": requiere,
        "margen": _margen_pct(t),
    }


def duplicar_evento(evento_id: int):

    """Crea una cotización nueva a partir de otro evento.

    Se copian cliente, datos descriptivos, gastos operativos y los
    arreglos con su costo_unitario tal como quedó guardado, sin
    recalcularlo desde el catálogo: el duplicado conserva los precios
    con los que se coticó el original.

    No se copian fecha, precio de venta, pagos, gastos reales ni la
    nota de autorización.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            cliente_id,
            nombre,
            tipo_evento,
            lugar,
            descripcion,
            costo_flete,
            costo_montaje,
            comision_porcentaje
        FROM eventos
        WHERE id = %s
          AND activo = TRUE
    """, (evento_id,))

    original = cur.fetchone()

    if not original:

        cur.close()
        conn.close()

        return {
            "error": "Evento no encontrado"
        }

    (cliente_id, nombre, tipo_evento, lugar,
     descripcion, costo_flete, costo_montaje, comision_porcentaje) = original

    # Los totales entran en cero y los recalcula
    # actualizar_totales_evento() al final.
    cur.execute("""
        INSERT INTO eventos (
            cliente_id,
            nombre,
            tipo_evento,
            lugar,
            descripcion,
            estatus,
            costo_flete,
            costo_montaje,
            comision_porcentaje,
            costo_base,
            costo_final,
            precio_minimo,
            precio_sugerido,
            activo
        )
        VALUES (
            %s, %s, %s, %s, %s, 'Cotizacion', %s, %s, %s, 0, 0, 0, 0, TRUE
        )
        RETURNING id
    """, (
        cliente_id,
        nombre + " (copia)",
        tipo_evento,
        lugar,
        descripcion,
        costo_flete,
        costo_montaje,
        comision_porcentaje
    ))

    nuevo_id = cur.fetchone()[0]

    # Renglón por renglón para copiar también la foto de insumos
    # (factor, costo de paquete) con la que se cotizó el original.
    cur.execute("""
        SELECT id, arreglo_id, cantidad, costo_unitario, subtotal, observaciones
        FROM evento_arreglos
        WHERE evento_id = %s
        ORDER BY id
    """, (evento_id,))

    for (ea_id, arreglo_id, cantidad, costo_unitario,
         subtotal, observaciones) in cur.fetchall():

        cur.execute("""
            INSERT INTO evento_arreglos (
                evento_id,
                arreglo_id,
                cantidad,
                costo_unitario,
                subtotal,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nuevo_id, arreglo_id, cantidad, costo_unitario,
              subtotal, observaciones))

        copiar_insumos_congelados(cur, ea_id, cur.fetchone()[0])

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(nuevo_id)

    return {
        "mensaje": "Evento duplicado",
        "id": nuevo_id
    }
