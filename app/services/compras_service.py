"""Lista de compras de un evento: cuánto se usa vs cuánto se compra.

Los arreglos se costean en proporción a la unidad de uso (12 tallos de un
paquete de 24 cuestan medio paquete). El redondeo a paquetes completos se
hace aquí, a nivel evento, después de sumar el mismo insumo en todos los
arreglos: 10 centros de mesa con 3 rosas son 30 rosas y 2 paquetes, no 10.

La diferencia entre los paquetes completos y lo usado es el costo de
sobrante. Solo aplica a insumos marcados con cobrar_paquete_completo
(perecederos); los consumibles que se reutilizan se cobran en proporción.

Todo sale de evento_arreglo_insumos, la foto que se toma al agregar el
arreglo al evento: editar el catálogo no cambia cotizaciones hechas.
"""

import math

from app.database.connection import get_connection

# Tolerancia para no pedir un paquete extra por ruido de punto flotante
# (24 tallos / 24 = 1.0000000000000002 no deben ser 2 paquetes).
_EPSILON = 1e-9


def congelar_insumos_arreglo(cur, evento_arreglo_id, arreglo_id):
    """Guarda la foto de los insumos del arreglo para un renglón del evento.

    Corre dentro de la transacción del llamador (no hace commit).
    """

    cur.execute("""
        INSERT INTO evento_arreglo_insumos (
            evento_arreglo_id,
            insumo_id,
            cantidad_uso,
            costo_unitario_uso,
            piezas_por_paquete,
            costo_paquete,
            porcentaje_merma,
            cobrar_paquete_completo,
            unidad_compra,
            unidad_uso
        )
        SELECT
            %s,
            ad.insumo_id,
            ad.cantidad,
            ad.costo_real,
            i.piezas_por_paquete,
            i.costo_referencia,
            i.porcentaje_merma,
            i.cobrar_paquete_completo,
            i.unidad,
            COALESCE(NULLIF(TRIM(i.unidad_uso), ''), i.unidad)
        FROM arreglo_detalle ad
        INNER JOIN insumos i
            ON i.id = ad.insumo_id
        WHERE ad.arreglo_id = %s
    """, (evento_arreglo_id, arreglo_id))


def copiar_insumos_congelados(cur, origen_evento_arreglo_id, destino_evento_arreglo_id):
    """Copia la foto de un renglón a otro (duplicar cotización)."""

    cur.execute("""
        INSERT INTO evento_arreglo_insumos (
            evento_arreglo_id,
            insumo_id,
            cantidad_uso,
            costo_unitario_uso,
            piezas_por_paquete,
            costo_paquete,
            porcentaje_merma,
            cobrar_paquete_completo,
            unidad_compra,
            unidad_uso
        )
        SELECT
            %s,
            insumo_id,
            cantidad_uso,
            costo_unitario_uso,
            piezas_por_paquete,
            costo_paquete,
            porcentaje_merma,
            cobrar_paquete_completo,
            unidad_compra,
            unidad_uso
        FROM evento_arreglo_insumos
        WHERE evento_arreglo_id = %s
        ORDER BY id
    """, (destino_evento_arreglo_id, origen_evento_arreglo_id))


def _renglones_planeados(cur, evento_id):
    """Suma cada insumo en todos los arreglos del evento y lo redondea.

    Si el mismo insumo quedó congelado con factores distintos (se editó el
    catálogo entre un arreglo y otro), manda la foto más reciente.
    """

    cur.execute("""
        SELECT
            s.insumo_id,
            i.codigo,
            i.nombre,
            SUM(ea.cantidad * s.cantidad_uso)                        AS uso_total,
            SUM(ea.cantidad * s.cantidad_uso * s.costo_unitario_uso) AS costo_uso,
            (ARRAY_AGG(s.piezas_por_paquete      ORDER BY s.id DESC))[1] AS piezas_por_paquete,
            (ARRAY_AGG(s.costo_paquete           ORDER BY s.id DESC))[1] AS costo_paquete,
            (ARRAY_AGG(s.porcentaje_merma        ORDER BY s.id DESC))[1] AS porcentaje_merma,
            (ARRAY_AGG(s.cobrar_paquete_completo ORDER BY s.id DESC))[1] AS cobrar_paquete_completo,
            (ARRAY_AGG(s.unidad_compra           ORDER BY s.id DESC))[1] AS unidad_compra,
            (ARRAY_AGG(s.unidad_uso              ORDER BY s.id DESC))[1] AS unidad_uso
        FROM evento_arreglos ea
        INNER JOIN evento_arreglo_insumos s
            ON s.evento_arreglo_id = ea.id
        INNER JOIN insumos i
            ON i.id = s.insumo_id
        WHERE ea.evento_id = %s
        GROUP BY s.insumo_id, i.codigo, i.nombre
        ORDER BY i.nombre
    """, (evento_id,))

    columnas = [desc[0] for desc in cur.description]
    renglones = []

    for fila in cur.fetchall():
        r = dict(zip(columnas, fila))

        uso_total  = float(r["uso_total"] or 0)
        costo_uso  = float(r["costo_uso"] or 0)
        factor     = float(r["piezas_por_paquete"] or 1) or 1
        costo_paq  = float(r["costo_paquete"] or 0)
        merma      = float(r["porcentaje_merma"] or 0)
        cobrar     = bool(r["cobrar_paquete_completo"])

        # La merma es física: con 10% de merma, 24 tallos usados piden 26.4
        uso_con_merma     = uso_total * (1 + merma)
        paquetes_exactos  = uso_con_merma / factor

        if cobrar:
            paquetes      = max(0, math.ceil(paquetes_exactos - _EPSILON))
            costo_compra  = paquetes * costo_paq
            costo_sobrante = max(0.0, costo_compra - costo_uso)
            piezas_sobrantes = max(0.0, paquetes * factor - uso_con_merma)
        else:
            paquetes      = paquetes_exactos
            costo_sobrante = 0.0
            piezas_sobrantes = 0.0

        renglones.append({
            "insumo_id":               r["insumo_id"],
            "codigo":                  r["codigo"],
            "nombre":                  r["nombre"],
            "unidad_compra":           r["unidad_compra"],
            "unidad_uso":              r["unidad_uso"],
            "piezas_por_paquete":      factor,
            "costo_paquete":           round(costo_paq, 2),
            "porcentaje_merma":        round(merma * 100, 2),
            "cobrar_paquete_completo": cobrar,
            "uso_total":               round(uso_total, 4),
            "uso_con_merma":           round(uso_con_merma, 4),
            "paquetes_planeados":      round(paquetes, 4),
            "piezas_sobrantes":        round(piezas_sobrantes, 4),
            "costo_uso":               round(costo_uso, 2),
            "costo_sobrante":          round(costo_sobrante, 2),
            "costo_planeado":          round(costo_uso + costo_sobrante, 2),
        })

    return renglones


def calcular_costo_sobrante(cur, evento_id):
    """Total del costo de paquetes incompletos del evento."""

    return round(
        sum(r["costo_sobrante"] for r in _renglones_planeados(cur, evento_id)),
        2
    )


def obtener_plan_compras(evento_id):
    """Lista de compras planeada del evento contra lo comprado.

    Lo comprado sale de los gastos reales ligados a un insumo.
    """

    conn = get_connection()
    cur = conn.cursor()

    renglones = _renglones_planeados(cur, evento_id)

    cur.execute("""
        SELECT
            gr.insumo_id,
            i.codigo,
            i.nombre,
            i.unidad AS unidad_compra,
            COALESCE(NULLIF(TRIM(i.unidad_uso), ''), i.unidad) AS unidad_uso,
            COALESCE(SUM(gr.paquetes_comprados), 0) AS paquetes_comprados,
            SUM(gr.monto)                           AS monto_comprado,
            COUNT(*)                                AS num_compras
        FROM evento_gastos_reales gr
        INNER JOIN insumos i
            ON i.id = gr.insumo_id
        WHERE gr.evento_id = %s
          AND gr.insumo_id IS NOT NULL
        GROUP BY gr.insumo_id, i.codigo, i.nombre, i.unidad, i.unidad_uso
    """, (evento_id,))

    columnas = [desc[0] for desc in cur.description]
    compras = {
        fila[0]: dict(zip(columnas, fila))
        for fila in cur.fetchall()
    }

    cur.close()
    conn.close()

    por_insumo = {r["insumo_id"]: r for r in renglones}

    # Comprado sin estar en la cotización: se lista con planeado en cero
    for insumo_id, c in compras.items():
        if insumo_id not in por_insumo:
            nuevo = {
                "insumo_id":               insumo_id,
                "codigo":                  c["codigo"],
                "nombre":                  c["nombre"],
                "unidad_compra":           c["unidad_compra"],
                "unidad_uso":              c["unidad_uso"],
                "piezas_por_paquete":      None,
                "costo_paquete":           None,
                "porcentaje_merma":        None,
                "cobrar_paquete_completo": False,
                "uso_total":               0,
                "uso_con_merma":           0,
                "paquetes_planeados":      0,
                "piezas_sobrantes":        0,
                "costo_uso":               0,
                "costo_sobrante":          0,
                "costo_planeado":          0,
                "no_planeado":             True,
            }
            renglones.append(nuevo)
            por_insumo[insumo_id] = nuevo

    for r in renglones:
        c = compras.get(r["insumo_id"])
        r.setdefault("no_planeado", False)
        if c:
            r["paquetes_comprados"] = round(float(c["paquetes_comprados"] or 0), 4)
            r["monto_comprado"]     = round(float(c["monto_comprado"] or 0), 2)
            r["num_compras"]        = int(c["num_compras"])
            r["diferencia"]         = round(r["monto_comprado"] - r["costo_planeado"], 2)
        else:
            r["paquetes_comprados"] = None
            r["monto_comprado"]     = None
            r["num_compras"]        = 0
            r["diferencia"]         = None

    con_compra = [r for r in renglones if r["num_compras"] > 0]

    totales = {
        "costo_uso":          round(sum(r["costo_uso"] for r in renglones), 2),
        "costo_sobrante":     round(sum(r["costo_sobrante"] for r in renglones), 2),
        "costo_planeado":     round(sum(r["costo_planeado"] for r in renglones), 2),
        "monto_comprado":     round(sum(r["monto_comprado"] for r in con_compra), 2),
        # Planeado solo de lo que ya se compró, para comparar peras con peras
        "planeado_comprado":  round(sum(r["costo_planeado"] for r in con_compra), 2),
        "insumos_planeados":  len([r for r in renglones if not r["no_planeado"]]),
        "insumos_comprados":  len(con_compra),
    }
    totales["diferencia"] = round(
        totales["monto_comprado"] - totales["planeado_comprado"], 2
    )

    return {
        "insumos": renglones,
        "totales": totales,
    }
