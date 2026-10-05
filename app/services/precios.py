"""Precios del evento: comisión y ganancia como MARGEN, en ese orden, solo sobre arreglos.

Cómo se arma el precio final de cada arreglo:
  1. Costo: cantidad × costo unitario, más su parte del sobrante de paquetes.
  2. Comisión del cliente, margen c, se suma primero:
        costo con comisión = costo ÷ (1 − c)
     La comisión es c sobre ese monto: comisión = c × (costo + comisión).
  3. Ganancia del negocio, margen m, una vez sumada la comisión:
        precio final = costo con comisión ÷ (1 − m)
     La ganancia es m del precio final.

Flete y montaje se cobran a costo: no llevan comisión ni ganancia.

Totales del evento:
  C  costo de los arreglos         S  sobrante de paquetes
  T  flete + montaje (a costo)     P  precio total del evento
  B  costo con comisión  = (C + S) / (1 − c)
  K  comisión            = B − C − S
  A  precio de arreglos  = P − T
  G  ganancia            = A − B
  m  margen efectivo     = G / A      (sobre el precio de los arreglos)

Precio para lograr un margen m:  P = T + B / (1 − m)

La comisión no depende del precio negociado: si se baja el precio, lo
que se reduce es la ganancia. El precio final de cada arreglo es su
parte de A, proporcional a su costo: así la ganancia del evento queda
diluida entre sus arreglos con el mismo margen en todos.
"""


def costo_con_comision(costo_arreglos, sobrante, comision):
    """Costo de arreglos más la comisión del cliente (paso 2). None si c >= 100%."""
    if comision >= 1:
        return None
    return (costo_arreglos + sobrante) / (1 - comision)


def precio_para_margen(costo_arreglos, sobrante, traslados, comision, margen):
    """Precio total del evento con el que los arreglos dejan `margen`.

    comision y margen van como fracción (0.30 = 30%). None si alguno es >= 100%.
    """
    base = costo_con_comision(costo_arreglos, sobrante, comision)
    if base is None or margen >= 1:
        return None
    return traslados + base / (1 - margen)


def resultado_para_precio(costo_arreglos, sobrante, traslados, comision, precio):
    """Comisión, ganancia y margen efectivo para un precio total dado."""
    base = costo_con_comision(costo_arreglos, sobrante, comision) or 0.0
    precio_arreglos = max(precio - traslados, 0.0)
    ganancia = precio_arreglos - base
    return {
        "precio": precio,
        "precio_arreglos": precio_arreglos,
        "costo_con_comision": base,
        "comision": base - costo_arreglos - sobrante,
        "ganancia": ganancia,
        # Margen sobre lo que sí lleva ganancia: el precio de los arreglos
        "margen": ganancia / precio_arreglos if precio_arreglos > 0 else None,
        "margen_total": ganancia / precio if precio > 0 else None,
    }


def precio_para_ganancia(costo_arreglos, sobrante, traslados, comision, ganancia):
    """Precio total con el que se obtiene una ganancia en pesos."""
    base = costo_con_comision(costo_arreglos, sobrante, comision)
    if base is None:
        return None
    return traslados + base + ganancia


def _centavos_que_suman(valores, total):
    """Redondea cada valor a centavos de modo que la suma sea round(total, 2).

    Redondear partida por partida puede dejar el pie de la tabla un centavo
    arriba o abajo del total del evento. El centavo que falta o sobra se
    asigna a las partidas con mayor residuo, como en una factura.
    """
    centavos_total = round(total * 100)
    exactos = [v * 100 for v in valores]
    base = [int(e // 1) for e in exactos]
    faltan = centavos_total - sum(base)
    orden = sorted(range(len(valores)), key=lambda i: exactos[i] - base[i], reverse=True)
    for i in orden[:max(faltan, 0)]:
        base[i] += 1
    return [b / 100 for b in base]


def repartir_por_arreglo(subtotales, sobrante, comision, precio_arreglos):
    """Desglose de cada partida del evento, en centavos exactos.

    subtotales: costo de cada partida (cantidad × costo unitario).
    Cada partida recibe su parte del sobrante y del precio de arreglos en
    proporción a su costo. Su comisión es c × (costo + comisión) de la
    partida y su ganancia es lo que queda. Las columnas suman exacto los
    totales del evento.

    Devuelve una lista de diccionarios con sobrante, comision, ganancia y
    precio_final por partida.
    """
    total = sum(subtotales)
    if total <= 0:
        return [{"sobrante": 0.0, "comision": 0.0, "ganancia": 0.0, "precio_final": 0.0}
                for _ in subtotales]

    factor_comision = comision / (1 - comision) if comision < 1 else 0.0
    sobrantes_exactos = [sobrante * s / total for s in subtotales]
    comisiones_exactas = [(s + so) * factor_comision for s, so in zip(subtotales, sobrantes_exactos)]

    sobrantes = _centavos_que_suman(sobrantes_exactos, sobrante)
    comisiones = _centavos_que_suman(comisiones_exactas, (total + sobrante) * factor_comision)
    precios = _centavos_que_suman([precio_arreglos * s / total for s in subtotales], precio_arreglos)

    partidas = []
    for subtotal, so, k, p in zip(subtotales, sobrantes, comisiones, precios):
        partidas.append({
            "sobrante": so,
            "comision": k,
            "ganancia": round(p - subtotal - so - k, 2),
            "precio_final": p,
        })
    return partidas
