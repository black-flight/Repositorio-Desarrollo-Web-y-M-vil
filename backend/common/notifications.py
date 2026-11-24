"""Notificaciones por HTTP REST o registro DEMO en MongoDB. Nunca SMTP.
Un HTTP 2xx significa aceptación de la API, NO entrega en buzón.
"""
import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx

logger = logging.getLogger("tokyo_noodles.notifications")

def modo_correo():
    url, token = os.getenv("EMAIL_API_URL", "").strip(), os.getenv("EMAIL_API_KEY", "").strip()
    if url and token:
        return "http"
    if url or token:
        return "configuracion_incompleta"
    return "demo"

async def enviar_notificacion(base, tipo: str, destinatario: str,
                             asunto: str, cuerpo: str, operacion_id: str,
                             codigo_demo: str | None = None) -> dict:
    """Registra resultado sin exponer credenciales, sin prometer entrega externa."""
    modo = modo_correo()
    registro = {
        "tipo": tipo, "destino": destinatario, "asunto": asunto,
        "operacion_id": operacion_id, "modo": modo,
        "creado_en": datetime.now(timezone.utc).isoformat(),
        "estado": "pendiente"
    }
    if modo == "demo":
        registro["estado"] = "registrado_demo_sin_entrega"
        # En la demo académica sintética se almacena el código para pruebas locales.
        if codigo_demo is not None and os.getenv("EMAIL_DEMO_MODE", "1") == "1":
            registro["codigo_demo"] = codigo_demo
    elif modo == "configuracion_incompleta":
        registro["estado"] = "configuracion_incompleta_sin_entrega"
    else:
        # URL configurada por el operador, contrato REST de adaptación descrito en README.
        # Nunca se imprime el cuerpo: puede contener código de verificación.
        url = os.environ["EMAIL_API_URL"].strip()
        parsed = urlparse(url)
        http_local = (os.getenv("EMAIL_ALLOW_HTTP_LOCAL") == "1"
                      and parsed.scheme == "http"
                      and parsed.hostname in {"127.0.0.1", "localhost", "host.docker.internal"})
        if parsed.scheme != "https" and not http_local:
            registro["estado"] = "url_http_no_permitida"
        else:
            try:
                async with httpx.AsyncClient(timeout=8) as cliente:
                    respuesta = await cliente.post(
                        url,
                        headers={"Authorization": "Bearer " + os.environ["EMAIL_API_KEY"],
                                 "Content-Type": "application/json"},
                        json={"from": os.getenv("EMAIL_FROM", "noreply@tokyonoodles.test"),
                              "to": destinatario, "subject": asunto, "text": cuerpo})
                registro["estado"] = ("aceptado_por_api_entrega_no_confirmada"
                                      if 200 <= respuesta.status_code < 300 else "rechazado_por_api")
                registro["http_status"] = respuesta.status_code
            except httpx.HTTPError as error:
                registro["estado"] = "error_de_transporte"
                registro["error_tipo"] = type(error).__name__
    await base["notifications"].insert_one(registro)
    registro.pop("_id", None)
    logger.info("operacion_id=%s service=notifications tipo=%s modo=%s estado=%s",
                operacion_id, tipo, modo, registro["estado"])
    return registro

async def notificar_pago(base, payment_id: str, pago: dict, operacion_id: str):
    """El pago NO se revierte si falla el correo opcional."""
    import os
    internal = os.environ["INTERNAL_GATEWAY_SECRET"]
    from httpx import AsyncClient, HTTPError
    try:
        async with AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.get(
                f"{os.getenv('CLIENTS_URL','http://127.0.0.1:9004')}/clients/{pago['client_id']}",
                headers={"X-Gateway-Secret": internal,
                         "X-Authenticated-Client": pago["client_id"],
                         "X-Authenticated-Roles": "user", "X-Operacion": operacion_id})
        respuesta.raise_for_status()
        destino = respuesta.json().get("correo")
        if not destino:
            raise ValueError("Cliente sin correo")
    except (HTTPError, ValueError, KeyError) as error:
        await base["payments"].update_one({"id":payment_id}, {"$set":{"email_status":"perfil_no_disponible"}})
        logger.warning("operacion_id=%s notification=profile_unavailable reason=%s",operacion_id,type(error).__name__)
        return
    # Obtener copia del comprobante desde Orders, sin delegar cálculos al navegador.
    try:
        async with AsyncClient(timeout=5.0) as cliente:
            r_pedido = await cliente.get(
                f"{os.getenv('ORDERS_URL','http://127.0.0.1:9002')}/orders/{pago['order_id']}/comprobante",
                headers={"X-Gateway-Secret": internal,
                         "X-Authenticated-Client": pago["client_id"],
                         "X-Authenticated-Roles": "user", "X-Operacion": operacion_id})
        r_pedido.raise_for_status()
        comprobante = r_pedido.json()
        lineas = [f"{x['nombre']} x{x['cantidad']}: ${x['subtotal']} CLP" for x in comprobante["items"]]
        cuerpo = (
            "Comprobante COMERCIAL NO TRIBUTARIO\n"
            f"Pedido: {pago['order_id']}\n"
            + "\n".join(lineas)
            + f"\nTotal: ${comprobante['total_clp']} CLP\n"
            + "Pago SIMULADO confirmado. Este documento NO es boleta tributaria SII."
        )
    except (HTTPError, ValueError, KeyError, TypeError) as error:
        logger.warning("operacion_id=%s notification=receipt_unavailable reason=%s",operacion_id,type(error).__name__)
        await base["payments"].update_one({"id":payment_id}, {"$set":{"email_status":"comprobante_no_disponible"}})
        return
    r = await enviar_notificacion(base, "comprobante_compra", destino,
        f"Tokyo Noodles - Comprobante {pago['order_id']}", cuerpo, operacion_id)
    await base["payments"].update_one({"id":payment_id}, {"$set":{"email_status":r["estado"]}})
