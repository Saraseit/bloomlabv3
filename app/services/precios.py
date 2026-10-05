"""Precios del evento con MARGEN (sobre el precio), no markup (sobre el costo).

Los dos porcentajes se miden sobre el precio de venta:
- Comisión del cliente: c = comisión / precio de los arreglos.
- Margen de ganancia:   m = ganancia / precio total del evento.

Flete y montaje se cobran a costo: no generan comisión y así los ve el
cliente en su PDF. El sobrante de paquetes es costo de material: va
dentro del precio de los arreglos.

Variables:
  C  costo de los arreglos (suma de subtotales)
  S  sobrante de paquetes
  T  flete + montaje (a costo)
  P  precio total del evento
  A  precio de los arreglos           = P - T
  K  comisión del cliente             = c · A
  G  ganancia                         = A - K - C - S = A(1 - c) - C - S
  m  margen efectivo                  = G / P

Precio para lograr un margen m (despejando G = m·P):
  (P - T)(1 - c) - C - S = m·P
  P = (C + S + T(1 - c)) / (1 - c - m)

Con c = 0 queda P = (C + S + T) / (1 - m), la fórmula que ya se usaba.

Cada arreglo del evento recibe una parte de A proporcional a su costo, y
su comisión es c sobre esa parte: la suma de las comisiones por arreglo
es exactamente K.
"""


def precio_para_margen(costo_arreglos, sobrante, traslados, comision, margen):
    """Precio total del evento con el que se obtiene `margen`.

    comision y margen van como fracción (0.30 = 30%). Devuelve None si
    comisión + margen >= 100%: no queda nada del precio para el costo.
    """
    divisor = 1 - comision - margen
    if divisor <= 0:
        return None
    return (costo_arreglos + sobrante + traslados * (1 - comision)) / divisor


def resultado_para_precio(costo_arreglos, sobrante, traslados, comision, precio):
    """Comisión, ganancia y margen efectivo para un precio total dado."""
    precio_arreglos = max(precio - traslados, 0.0)
    importe_comision = comision * precio_arreglos
    ganancia = precio_arreglos - importe_comision - costo_arreglos - sobrante
    margen = ganancia / precio if precio > 0 else 0.0
    return {
        "precio": precio,
        "precio_arreglos": precio_arreglos,
        "comision": importe_comision,
        "ganancia": ganancia,
        "margen": margen,
    }


def precio_para_ganancia(costo_arreglos, sobrante, traslados, comision, ganancia):
    """Precio total con el que se obtiene una ganancia en pesos."""
    if comision >= 1:
        return None
    return traslados + (ganancia + costo_arreglos + sobrante) / (1 - comision)


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


def repartir_por_arreglo(subtotales, precio_arreglos, comision):
    """Precio y comisión de cada partida, proporcionales a su costo.

    subtotales: costo de cada partida (cantidad × costo unitario).
    Devuelve una lista de (precio_partida, comision_partida) en centavos
    exactos: las partidas suman el precio de arreglos y la comisión total.
    """
    total = sum(subtotales)
    if total <= 0:
        return [(0.0, 0.0) for _ in subtotales]
    precios = [precio_arreglos * (subtotal / total) for subtotal in subtotales]
    comisiones = [p * comision for p in precios]
    return list(zip(
        _centavos_que_suman(precios, precio_arreglos),
        _centavos_que_suman(comisiones, precio_arreglos * comision),
    ))
