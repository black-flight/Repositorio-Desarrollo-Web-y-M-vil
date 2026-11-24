import os
import secrets
import logging
from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from backend.common.tracing import instalar_trazabilidad
from backend.common.notifications import notificar_pago


app = FastAPI(title="Tokyo Noodles - Payments")
instalar_trazabilidad(app, "payments")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
PAYMENTS_TO_ORDERS_SECRET = os.getenv("PAYMENTS_TO_ORDERS_SECRET")
PAYMENT_TEST_SECRET = os.getenv("PAYMENT_TEST_SECRET")
PAYMENT_TEST_MODE = os.getenv("PAYMENT_TEST_MODE") == "1"
ORDERS_URL = os.getenv("ORDERS_URL", "http://127.0.0.1:9002")

if not INTERNAL_GATEWAY_SECRET or not PAYMENTS_TO_ORDERS_SECRET:
    raise RuntimeError("Configurar los secretos internos de Payments")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)

base = mongo["tokyo_noodles_eval2"]
pagos_db = base["payments"]
logger = logging.getLogger("tokyo_noodles.payments")


class SolicitudPago(BaseModel):
    order_id: str = Field(min_length=5)


def verificar_gateway(
    request: Request,
    x_gateway_secret: str = Header(default=""),
    x_authenticated_client: str = Header(default=""),
    x_authenticated_roles: str = Header(default="")
):
    permitido = secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET)
    logger.info("operacion_id=%s service=payments secret_check=%s",request.state.operacion_id,"ok" if permitido else "rejected")
    if not permitido:
        raise HTTPException(
            status_code=403,
            detail="Gateway no autorizado"
        )

    if not x_authenticated_client:
        raise HTTPException(
            status_code=401,
            detail="Identidad requerida"
        )

    return {"id": x_authenticated_client, "admin": "admin" in x_authenticated_roles.split(",")}


@app.on_event("startup")
async def iniciar():
    await mongo.admin.command("ping")
    await pagos_db.create_index("order_id", unique=True)
    await pagos_db.create_index("id", unique=True)


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "payments"
    }


@app.post("/payments", status_code=201)
async def iniciar_pago(
    solicitud: SolicitudPago,
    request: Request,
    auth=Depends(verificar_gateway)
):
    client_id = auth["id"]
    existente = await pagos_db.find_one({"order_id": solicitud.order_id}, {"_id": 0})
    if existente:
        if existente["client_id"] != client_id:
            raise HTTPException(status_code=403, detail="Pago de otro cliente")
        return existente
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.get(
                f"{ORDERS_URL}/orders/{solicitud.order_id}",
                headers={
                    "X-Gateway-Secret": INTERNAL_GATEWAY_SECRET,
                    "X-Authenticated-Client": client_id,
                    "X-Authenticated-Roles": "user",
                    "X-Operacion": request.state.operacion_id
                }
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Orders no disponible"
        )

    if respuesta.status_code == 403:
        raise HTTPException(
            status_code=403,
            detail="Pedido de otro cliente"
        )

    if respuesta.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    if respuesta.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar el pedido"
        )

    pedido = respuesta.json()

    if pedido["estado"] != "pendiente_pago":
        raise HTTPException(
            status_code=409,
            detail="El pedido no admite nuevos pagos"
        )

    existente = await pagos_db.find_one(
        {"order_id": solicitud.order_id},
        {"_id": 0}
    )

    if existente:
        return existente

    pago = {
        "id": "PAY-" + secrets.token_hex(6).upper(),
        "order_id": solicitud.order_id,
        "client_id": client_id,
        "monto": pedido["total"],
        "estado": "pendiente",
        "fecha": datetime.now(timezone.utc).isoformat(),
        "confirmado_en": None,
        "email_status": "no_intentado"
    }

    try:
        await pagos_db.insert_one(pago)
    except DuplicateKeyError:
        return await pagos_db.find_one(
            {"order_id": solicitud.order_id},
            {"_id": 0}
        )

    pago.pop("_id", None)

    return pago


@app.get("/payments/order/{order_id}")
async def pago_de_pedido(order_id: str, auth=Depends(verificar_gateway)):
    pago = await pagos_db.find_one({"order_id": order_id}, {"_id": 0})
    if pago is None:
        raise HTTPException(status_code=404, detail="Pago no registrado")
    if pago["client_id"] != auth["id"] and not auth["admin"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    return pago


@app.get("/payments/{payment_id}")
async def consultar_pago(
    payment_id: str,
    auth=Depends(verificar_gateway)
):
    pago = await pagos_db.find_one(
        {"id": payment_id},
        {"_id": 0}
    )

    if pago is None:
        raise HTTPException(
            status_code=404,
            detail="Pago no encontrado"
        )

    if pago["client_id"] != auth["id"] and not auth["admin"]:
        raise HTTPException(
            status_code=403,
            detail="Pago de otro cliente"
        )

    return pago


@app.post("/payments/{payment_id}/test-confirm")
async def confirmar_pago_de_prueba(
    payment_id: str,
    request: Request,
    x_payment_test_secret: str = Header(default="")
):
    if not PAYMENT_TEST_MODE:
        raise HTTPException(
            status_code=404,
            detail="Ruta de prueba deshabilitada"
        )

    if (
        not PAYMENT_TEST_SECRET
        or not secrets.compare_digest(
            x_payment_test_secret,
            PAYMENT_TEST_SECRET
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Credencial de prueba incorrecta"
        )

    pago = await pagos_db.find_one(
        {"id": payment_id},
        {"_id": 0}
    )

    if pago is None:
        raise HTTPException(
            status_code=404,
            detail="Pago no encontrado"
        )

    if pago["estado"] == "pagado":
        return pago

    if pago["estado"] != "pendiente":
        raise HTTPException(
            status_code=409,
            detail="Estado de pago invalido"
        )

    try:
        async with httpx.AsyncClient(timeout=12.0) as cliente:
            respuesta = await cliente.post(
                f"{ORDERS_URL}/orders/{pago['order_id']}/confirm-payment",
                json={
                    "referencia": pago["id"]
                },
                headers={
                    "X-Gateway-Secret": INTERNAL_GATEWAY_SECRET,
                    "X-Payments-Secret": PAYMENTS_TO_ORDERS_SECRET,
                    "X-Authenticated-Client": "payments-service",
                    "X-Authenticated-Roles": "payments",
                    "X-Operacion": request.state.operacion_id
                }
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Orders no disponible"
        )

    if respuesta.status_code != 200:
        raise HTTPException(
            status_code=409,
            detail="No se pudo confirmar el pedido"
        )

    actualizado = await pagos_db.update_one(
        {"id": payment_id, "estado": "pendiente"},
        {"$set": {"estado": "pagado", "confirmado_en": datetime.now(timezone.utc).isoformat()}}
    )
    # Notificación REST opcional o registro demo; nunca equivale a entrega confirmada.
    if actualizado.modified_count:
        logger.info("operacion_id=%s db=mongo action=confirm_payment payment_id=%s",request.state.operacion_id,payment_id)
        try:
            await notificar_pago(base, payment_id, pago, request.state.operacion_id)
        except Exception as error:
            logger.warning("operacion_id=%s notification=error type=%s",request.state.operacion_id,type(error).__name__)
            await pagos_db.update_one({"id":payment_id},{"$set":{"email_status":"error_de_notificacion"}})
    return await pagos_db.find_one({"id": payment_id}, {"_id": 0})