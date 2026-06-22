from fastapi import APIRouter
from fastapi.responses import Response
from xhtml2pdf import pisa
import io
import base64
import requests as req_lib

from app.services.eventos_service import obtener_evento

router = APIRouter()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def imagen_a_base64(url: str) -> str:
    """Descarga una imagen desde Cloudinary y la convierte a base64
    para incrustarla en el PDF (xhtml2pdf no carga URLs externas)."""
    if not url:
        return ""
    try:
        r = req_lib.get(url, timeout=8)
        if r.status_code == 200:
            media_type = r.headers.get("Content-Type", "image/jpeg").split(";")[0]
            b64 = base64.b64encode(r.content).decode()
            return f"data:{media_type};base64,{b64}"
    except Exception:
        pass
    return ""


def calcular_distribucion_cliente(evento):
    """Prorratea precio_venta entre arreglos. Flete/montaje se muestran a costo."""

    precio_venta  = float(evento.get("precio_venta") or 0)
    costo_flete   = float(evento.get("costo_flete")  or 0)
    costo_montaje = float(evento.get("costo_montaje") or 0)
    arreglos      = evento.get("arreglos", [])

    costo_arreglos = sum(float(a["subtotal"]) for a in arreglos)
    residuo = precio_venta - costo_flete - costo_montaje

    items = []
    for a in arreglos:
        peso = float(a["subtotal"]) / costo_arreglos if costo_arreglos else 0
        precio_total    = residuo * peso
        precio_unitario = precio_total / float(a["cantidad"]) if a["cantidad"] else 0
        items.append({
            "nombre":          a["nombre"],
            "descripcion":     a.get("observaciones") or "",
            "imagen_b64":      imagen_a_base64(a.get("imagen_url")),
            "cantidad":        a["cantidad"],
            "precio_unitario": round(precio_unitario, 2),
            "total":           round(precio_total, 2),
        })

    return {
        "items":   items,
        "flete":   costo_flete,
        "montaje": costo_montaje,
        "total":   precio_venta,
    }


# ──────────────────────────────────────────────
# PDF Cliente
# ──────────────────────────────────────────────

def construir_html_cliente(evento, dist):
    items_html = ""
    for item in dist["items"]:
        img_html = (
            f'<img src="{item["imagen_b64"]}" class="item-img">'
            if item["imagen_b64"]
            else '<div class="item-img-placeholder">Sin imagen</div>'
        )
        items_html += f"""
        <tr>
            <td class="td-img">{img_html}</td>
            <td class="td-desc">
                <strong>{item["nombre"]}</strong>
                <div class="item-obs">{item["descripcion"]}</div>
            </td>
            <td class="td-num">{int(item["cantidad"])}</td>
            <td class="td-num">${item["precio_unitario"]:,.2f}</td>
            <td class="td-num total">${item["total"]:,.2f}</td>
        </tr>"""

    gastos_html = ""
    if dist["flete"] > 0:
        gastos_html += f"""
        <tr>
            <td class="td-img"><div class="item-img-placeholder">Flete</div></td>
            <td class="td-desc"><strong>Flete</strong></td>
            <td class="td-num">1</td>
            <td class="td-num">${dist["flete"]:,.2f}</td>
            <td class="td-num total">${dist["flete"]:,.2f}</td>
        </tr>"""
    if dist["montaje"] > 0:
        gastos_html += f"""
        <tr>
            <td class="td-img"><div class="item-img-placeholder">Montaje</div></td>
            <td class="td-desc"><strong>Montaje / Desmontaje</strong></td>
            <td class="td-num">1</td>
            <td class="td-num">${dist["montaje"]:,.2f}</td>
            <td class="td-num total">${dist["montaje"]:,.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: letter; margin: 0; }}
  * {{ margin: 0; padding: 0; }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #1a2e1e; }}

  .header {{ background-color: #1a2e1e; color: white; padding: 24px 32px; }}
  .header-brand {{ font-size: 22px; font-weight: bold; }}
  .header-sub {{ font-size: 10px; color: #b8ccbe; margin-top: 2px; }}
  .header-order {{ font-size: 16px; font-weight: bold; margin-top: 6px; }}

  .event-info {{ padding: 14px 32px; background-color: #f7fbf7; }}
  .event-info table {{ width: 100%; }}
  .event-info td {{ padding: 3px 8px; font-size: 10px; }}
  .ei-label {{ font-weight: bold; color: #7aaa82; text-transform: uppercase; }}

  .section-title {{ padding: 12px 32px 6px; font-size: 10px; font-weight: bold;
                    color: #4a7a5a; text-transform: uppercase; }}

  table.items {{ width: 100%; border-collapse: collapse; }}
  table.items thead td {{ background-color: #2b5c3c; color: white; padding: 8px 12px;
                          font-size: 9px; font-weight: bold; text-transform: uppercase; }}
  table.items tbody td {{ padding: 8px 12px; border-bottom: 1px solid #f0f5f0;
                          vertical-align: middle; }}
  .td-img {{ width: 70px; padding-left: 32px; }}
  .td-num {{ text-align: right; }}
  .item-img {{ width: 60px; height: 60px; }}
  .item-img-placeholder {{ width: 60px; height: 60px; background-color: #f0f5f0;
                           color: #9ca3af; text-align: center; font-size: 8px; }}
  .item-obs {{ font-size: 9px; color: #6b7280; }}
  .total {{ font-weight: bold; color: #2b5c3c; }}

  .totales {{ padding: 16px 32px; }}
  .totales table {{ width: 260px; float: right; }}
  .totales td {{ padding: 6px 0; font-size: 14px; font-weight: bold; }}
  .totales .t-label {{ color: #1a2e1e; }}
  .totales .t-value {{ text-align: right; color: #2b5c3c; }}

  .footer {{ clear: both; padding: 16px 32px; background-color: #f7fbf7;
             font-size: 9px; color: #6b7280; text-align: center; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-brand">BloomLab</div>
  <div class="header-sub">Sistema de Gestion Floral</div>
  <div class="header-order">Cotizacion #{evento["id"]:04d}</div>
</div>

<div class="event-info">
  <table>
    <tr>
      <td><span class="ei-label">Cliente:</span> {evento["cliente"]}</td>
      <td><span class="ei-label">Evento:</span> {evento["nombre"]}</td>
    </tr>
    <tr>
      <td><span class="ei-label">Fecha:</span> {evento["fecha_evento"]}</td>
      <td><span class="ei-label">Lugar:</span> {evento.get("lugar") or "-"}</td>
    </tr>
  </table>
</div>

<div class="section-title">Propuesta de arreglos florales</div>

<table class="items">
  <thead>
    <tr>
      <td>Imagen</td>
      <td>Descripcion</td>
      <td class="td-num">Cant.</td>
      <td class="td-num">P. Unitario</td>
      <td class="td-num">Total</td>
    </tr>
  </thead>
  <tbody>
    {items_html}
    {gastos_html}
  </tbody>
</table>

<div class="totales">
  <table>
    <tr>
      <td class="t-label">TOTAL</td>
      <td class="t-value">${dist["total"]:,.2f}</td>
    </tr>
  </table>
</div>

<div class="footer">
  Todos los precios estan en MXN &middot; Cotizacion generada por BloomLab
</div>

</body></html>"""


# ──────────────────────────────────────────────
# PDF Interno
# ──────────────────────────────────────────────

def construir_html_interno(evento):
    arreglos = evento.get("arreglos", [])

    filas_html = ""
    for a in arreglos:
        filas_html += f"""
        <tr>
            <td>{a["codigo"]}</td>
            <td>{a["nombre"]}</td>
            <td class="num">{int(a["cantidad"])}</td>
            <td class="num">${float(a["costo_unitario"]):,.2f}</td>
            <td class="num">${float(a["subtotal"]):,.2f}</td>
            <td>{a.get("observaciones") or ""}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  @page {{ size: letter; margin: 0; }}
  * {{ margin: 0; padding: 0; }}
  body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11px; color: #1a2e1e; }}

  .header {{ background-color: #1a2e1e; color: white; padding: 20px 32px; }}
  .header-brand {{ font-size: 18px; font-weight: bold; }}
  .header-tag {{ font-size: 10px; color: #fca5a5; font-weight: bold; margin-top: 4px; }}

  .event-info {{ padding: 12px 32px; background-color: #f7fbf7; }}
  .event-info td {{ padding: 3px 8px; font-size: 10px; }}
  .ei-label {{ font-weight: bold; color: #7aaa82; text-transform: uppercase; }}

  .section {{ padding: 10px 32px 4px; font-size: 10px; font-weight: bold;
              color: #4a7a5a; text-transform: uppercase; }}

  table.items {{ width: 100%; border-collapse: collapse; }}
  table.items thead td {{ background-color: #2b5c3c; color: white; padding: 7px 12px;
                          font-size: 9px; font-weight: bold; text-transform: uppercase; }}
  table.items tbody td {{ padding: 7px 12px; border-bottom: 1px solid #f0f5f0; }}
  .num {{ text-align: right; }}

  .kpis {{ padding: 16px 32px; }}
  .kpis table {{ width: 100%; border-collapse: collapse; }}
  .kpis td {{ width: 25%; padding: 8px; }}
  .kpi-box {{ background-color: #f7fbf7; padding: 10px; }}
  .kpi-label {{ font-size: 8px; font-weight: bold; color: #7aaa82; text-transform: uppercase; }}
  .kpi-value {{ font-size: 15px; font-weight: bold; color: #1a2e1e; }}
  .kpi-final {{ background-color: #d3eccc; }}
  .kpi-precio {{ background-color: #1a2e1e; }}
  .kpi-precio .kpi-label {{ color: #b8ccbe; }}
  .kpi-precio .kpi-value {{ color: white; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-brand">BloomLab - Reporte Interno</div>
  <div class="header-tag">CONFIDENCIAL - NO COMPARTIR CON EL CLIENTE</div>
</div>

<div class="event-info">
  <table>
    <tr>
      <td><span class="ei-label">Cliente:</span> {evento["cliente"]}</td>
      <td><span class="ei-label">Evento:</span> {evento["nombre"]}</td>
      <td><span class="ei-label">Comision:</span> {evento["comision_porcentaje"]}%</td>
    </tr>
    <tr>
      <td><span class="ei-label">Fecha:</span> {evento["fecha_evento"]}</td>
      <td><span class="ei-label">Lugar:</span> {evento.get("lugar") or "-"}</td>
      <td><span class="ei-label">Estatus:</span> {evento["estatus"]}</td>
    </tr>
  </table>
</div>

<div class="section">Arreglos del evento</div>
<table class="items">
  <thead>
    <tr>
      <td>Codigo</td><td>Nombre</td><td class="num">Cant.</td>
      <td class="num">Costo Unit.</td><td class="num">Subtotal</td><td>Observaciones</td>
    </tr>
  </thead>
  <tbody>{filas_html}</tbody>
</table>

<div class="kpis">
  <table>
    <tr>
      <td><div class="kpi-box">
        <div class="kpi-label">Costo arreglos</div>
        <div class="kpi-value">${evento["costo_arreglos"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box">
        <div class="kpi-label">Comision ({evento["comision_porcentaje"]}%)</div>
        <div class="kpi-value">${evento["importe_comision"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box">
        <div class="kpi-label">Flete</div>
        <div class="kpi-value">${evento["costo_flete"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box">
        <div class="kpi-label">Montaje</div>
        <div class="kpi-value">${evento["costo_montaje"]:,.2f}</div>
      </div></td>
    </tr>
    <tr>
      <td><div class="kpi-box kpi-final">
        <div class="kpi-label">Costo final</div>
        <div class="kpi-value">${evento["costo_final"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box">
        <div class="kpi-label">Precio minimo</div>
        <div class="kpi-value">${evento["precio_minimo"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box">
        <div class="kpi-label">Precio sugerido</div>
        <div class="kpi-value">${evento["precio_sugerido"]:,.2f}</div>
      </div></td>
      <td><div class="kpi-box kpi-precio">
        <div class="kpi-label">Precio acordado</div>
        <div class="kpi-value">${float(evento["precio_venta"] or 0):,.2f}</div>
      </div></td>
    </tr>
  </table>
</div>

</body></html>"""


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────

@router.get("/eventos/{evento_id}/pdf")
def generar_pdf(evento_id: int, tipo: str = "cliente"):
    evento = obtener_evento(evento_id)

    if "error" in evento:
        return {"error": evento["error"]}

    if tipo == "cliente":
        dist = calcular_distribucion_cliente(evento)
        html = construir_html_cliente(evento, dist)
        filename = f"cotizacion_{evento_id}.pdf"
    else:
        html = construir_html_interno(evento)
        filename = f"interno_{evento_id}.pdf"

    buffer = io.BytesIO()
    resultado = pisa.CreatePDF(html, dest=buffer)

    if resultado.err:
        return {"error": "No se pudo generar el PDF"}

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )