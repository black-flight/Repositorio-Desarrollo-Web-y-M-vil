import os
import re
import secrets
import hashlib
import json
import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import DuplicateKeyError

from backend.common.tracing import instalar_trazabilidad
from backend.domain.delivery import verificar_cobertura
from backend.mensajeria.productor import publicar_pedido_pagado


app = FastAPI(title="Tokyo Noodles - Orders")
instalar_trazabilidad(app, "orders")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
PAYMENTS_TO_ORDERS_SECRET = os.getenv("PAYMENTS_TO_ORDERS_SECRET")
INVENTORY_URL = os.getenv("INVENTORY_URL", "http://127.0.0.1:9001")
CLIENTS_URL = os.getenv("CLIENTS_URL", "http://127.0.0.1:9004")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("Configurar INTERNAL_GATEWAY_SECRET")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)

pedidos_db = mongo["tokyo_noodles_eval2"]["orders"]
logger = logging.getLogger("tokyo_noodles.orders")
DELIVERY_STORE_LAT = os.getenv("DELIVERY_STORE_LAT")
DELIVERY_STORE_LON = os.getenv("DELIVERY_STORE_LON")
DELIVERY_RADIUS_KM = float(os.getenv("DELIVERY_RADIUS_KM", "3"))


@app.on_event("startup")
async def inicializar_indices():
    await mongo.admin.command("ping")
    await pedidos_db.create_index("id", unique=True)
    await pedidos_db.create_index([("client_id", 1), ("codigo_compra", 1)], unique=True, partialFilterExpression={"codigo_compra": {"$type": "string"}})


class ItemPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(pattern=r"^[0-9]+$")
    quantity: int = Field(gt=0, le=30)


class NuevoPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    codigo_compra: str = Field(pattern=r"^[A-Za-z0-9._:-]{16,128}$")
    items: list[ItemPedido] = Field(min_length=1)
    modalidad: Literal["retiro", "delivery"]
    direccion: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class Anulacion(BaseModel):
    motivo: str = Field(min_length=5)


class ConfirmacionPago(BaseModel):
    referencia: str = Field(min_length=4)


class CambioEstado(BaseModel):
    estado: Literal["en_preparacion", "listo", "en_reparto", "entregado"]


def verificar_gateway(
    request: Request,
    x_gateway_secret: str = Header(default=""),
    x_authenticated_client: str = Header(default=""),
    x_authenticated_roles: str = Header(default="")
):
    permitido = secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET)
    logger.info("operacion_id=%s service=orders secret_check=%s", request.state.operacion_id, "ok" if permitido else "rejected")
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

    return {
        "id": x_authenticated_client,
        "roles": x_authenticated_roles.split(","),
        "admin": "admin" in x_authenticated_roles.split(",")
    }


def verificar_propiedad(pedido, auth):
    if not auth["admin"] and "staff" not in auth["roles"] and pedido["client_id"] != auth["id"]:
        raise HTTPException(
            status_code=403,
            detail="Pedido de otro cliente"
        )


async def buscar_pedido(pedido_id):
    pedido = await pedidos_db.find_one(
        {"id": pedido_id},
        {"_id": 0, "compra_payload_hash": 0}
    )

    if pedido is None:
        raise HTTPException(
            status_code=404,
            detail="Pedido no encontrado"
        )

    return pedido


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "orders"
    }


@app.get("/orders")
async def listar_pedidos(auth=Depends(verificar_gateway)):
    filtro = {} if (auth["admin"] or "staff" in auth["roles"]) else {
        "client_id": auth["id"]
    }

    pedidos = await pedidos_db.find(
        filtro,
        {"_id": 0, "compra_payload_hash": 0}
    ).to_list(length=200)

    return {"orders": pedidos}


@app.get("/orders/reporte-ventas")
async def reporte_ventas(
    desde: date,
    hasta: date,
    auth=Depends(verificar_gateway)
):
    if not auth["admin"]:
        raise HTTPException(
            status_code=403,
            detail="Permiso de administrador requerido"
        )

    if desde > hasta or (hasta - desde).days > 366 or hasta.year == 9999:
        raise HTTPException(
            status_code=400,
            detail="Periodo invalido (maximo 366 dias)"
        )

    estados_contabilizados = [
        "pagado", "en_preparacion", "listo", "en_reparto", "entregado", "anulacion_solicitada"
    ]

    filas = await pedidos_db.aggregate([
        {
            "$match": {
                "fecha": {
                    "$gte": desde.isoformat(),
                    "$lt": (hasta + timedelta(days=1)).isoformat()
                },
                "estado": {"$in": estados_contabilizados}
            }
        },
        {
            "$group": {
                "_id": "$estado",
                "cantidad_pedidos": {"$sum": 1},
                "monto_clp": {"$sum": "$total"}
            }
        }
    ]).to_list(length=10)

    desglose = {
        fila["_id"]: {
            "cantidad_pedidos": fila["cantidad_pedidos"],
            "monto_clp": fila["monto_clp"]
        }
        for fila in filas
    }

    return {
        "periodo": {
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "criterio_fecha": "creacion_del_pedido"
        },
        "cantidad_pedidos": sum(
            x["cantidad_pedidos"] for x in desglose.values()
        ),
        "monto_total_clp": sum(
            x["monto_clp"] for x in desglose.values()
        ),
        "ventas_por_estado": desglose,
        "estados_contabilizados": estados_contabilizados
    }




@app.get("/orders/eventos")
async def estado_eventos(auth=Depends(verificar_gateway)):
    if not auth["admin"]:
        raise HTTPException(status_code=403, detail="Solo admin")
    total = await pedidos_db.count_documents({})
    pendientes = await pedidos_db.count_documents({"event_status": {"$in": ["pendiente", "fallido"]}})
    return {"total_pedidos": total, "eventos_sin_publicar": pendientes,
            "explicacion": "Publicación directa al pagar; fallo puede reintentarse en /orders/{id}/publish-event"}


@app.get("/orders/{pedido_id}")
async def consultar_pedido(
    pedido_id: str,
    auth=Depends(verificar_gateway)
):
    pedido = await buscar_pedido(pedido_id)
    verificar_propiedad(pedido, auth)
    return pedido


@app.post("/orders", status_code=201)
async def crear_pedido(
    nuevo: NuevoPedido,
    request: Request,
    auth=Depends(verificar_gateway)
):
    # Un intento lógico se identifica mediante el código dentro del documento MongoDB.
    # No se confía en el total enviado por el navegador.
    payload = nuevo.model_dump(mode="json", exclude={"codigo_compra"})
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    existente = await pedidos_db.find_one({"client_id": auth["id"], "codigo_compra": nuevo.codigo_compra}, {"_id": 0})
    if existente:
        if existente.get("compra_payload_hash") != payload_hash:
            raise HTTPException(status_code=409, detail="Código de compra reutilizado para una compra diferente")
        existente.pop("compra_payload_hash", None)
        return JSONResponse(status_code=200, content=existente)

    distancia_delivery = None
    if nuevo.modalidad == "delivery":
        if not (nuevo.direccion or "").strip() or len((nuevo.direccion or "").strip()) < 5:
            raise HTTPException(status_code=400, detail="Direccion requerida para delivery")
        if nuevo.latitude is None or nuevo.longitude is None:
            raise HTTPException(status_code=422,
                detail="Se requieren coordenadas verificables para validar los 3 km")
        try:
            cubierto, distancia_delivery = verificar_cobertura(
                nuevo.latitude, nuevo.longitude,
                float(DELIVERY_STORE_LAT) if DELIVERY_STORE_LAT else None,
                float(DELIVERY_STORE_LON) if DELIVERY_STORE_LON else None,
                DELIVERY_RADIUS_KM
            )
        except ValueError:
            raise HTTPException(status_code=503, detail="Sucursal sin coordenadas configuradas")
        if not cubierto:
            raise HTTPException(status_code=422,
                detail=f"Destino fuera del radio de {DELIVERY_RADIUS_KM:g} km; distancia recta {distancia_delivery:.3f} km")

    ids = [item.product_id for item in nuevo.items]

    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=400,
            detail="Productos repetidos"
        )

    detalles = []
    total = 0

    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            registro = await cliente.get(
                f"{CLIENTS_URL}/clients/{auth['id']}",
                headers={
                    "X-Gateway-Secret": INTERNAL_GATEWAY_SECRET,
                    "X-Authenticated-Client": auth["id"],
                    "X-Operacion": request.state.operacion_id
                }
            )

            if registro.status_code != 200 or not registro.json().get("activo", False):
                raise HTTPException(
                    status_code=403,
                    detail="Cliente no registrado o inactivo"
                )

            if os.getenv("EMAIL_REQUIRE_VERIFIED", "0") == "1" and not registro.json().get("correo_verificado"):
                raise HTTPException(status_code=403, detail="Verifica el correo antes de comprar")

            for item in nuevo.items:
                respuesta = await cliente.get(
                    f"{INVENTORY_URL}/products/{item.product_id}",
                    headers={
                        "X-Gateway-Secret": INTERNAL_GATEWAY_SECRET,
                        "X-Operacion": request.state.operacion_id
                    }
                )

                if respuesta.status_code == 404:
                    raise HTTPException(
                        status_code=400,
                        detail="Producto inexistente"
                    )

                if respuesta.status_code != 200:
                    raise HTTPException(
                        status_code=503,
                        detail="Inventario no disponible"
                    )

                producto = respuesta.json()

                if not producto.get("available", False):
                    raise HTTPException(
                        status_code=409,
                        detail="Producto no disponible"
                    )

                subtotal = producto["precio"] * item.quantity

                detalles.append({
                    "product_id": item.product_id,
                    "nombre": producto["nombre"],
                    "cantidad": item.quantity,
                    "precio_unitario": producto["precio"],
                    "subtotal": subtotal
                })

                total += subtotal

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Inventario no disponible"
        )

    pedido = {
        "id": "ORD-" + secrets.token_hex(6).upper(),
        "client_id": auth["id"],
        "items": detalles,
        "total": total,
        "modalidad": nuevo.modalidad,
        "direccion": nuevo.direccion if nuevo.modalidad == "delivery" else None,
        "estado": "pendiente_pago",
        "fecha": datetime.now(timezone.utc).isoformat(),
        "referencia_pago": None,
        "motivo_anulacion": None,
        "delivery_latitude": nuevo.latitude if nuevo.modalidad == "delivery" else None,
        "delivery_longitude": nuevo.longitude if nuevo.modalidad == "delivery" else None,
        "delivery_distance_km": distancia_delivery,
        "event_published": False,
        "event_status": "esperando_pago",
        "codigo_compra": nuevo.codigo_compra,
        "compra_payload_hash": payload_hash
    }

    try:
        await pedidos_db.insert_one(pedido)
    except DuplicateKeyError:
        existente = await pedidos_db.find_one({"client_id": auth["id"], "codigo_compra": nuevo.codigo_compra}, {"_id": 0})
        if not existente:
            raise HTTPException(status_code=409, detail="Conflicto de unicidad de pedido")
        if existente.get("compra_payload_hash") != payload_hash:
            raise HTTPException(status_code=409, detail="Código de compra reutilizado para compra distinta")
        existente.pop("compra_payload_hash", None)
        return JSONResponse(status_code=200, content=existente)

    pedido.pop("_id", None)
    pedido.pop("compra_payload_hash", None)
    logger.info("operacion_id=%s db=mongo action=insert_order order_id=%s", request.state.operacion_id, pedido["id"])
    return pedido


@app.post("/orders/{pedido_id}/cancel")
async def anular_pedido(
    pedido_id: str,
    solicitud: Anulacion,
    auth=Depends(verificar_gateway)
):
    if "staff" in auth["roles"] and not auth["admin"]:
        raise HTTPException(status_code=403, detail="Operador no puede anular pedidos")
    pedido = await buscar_pedido(pedido_id)
    verificar_propiedad(pedido, auth)

    estado = pedido["estado"]

    if estado == "pendiente_pago":
        nuevo_estado = "anulado"
    elif estado == "pagado":
        nuevo_estado = "anulacion_solicitada"
    else:
        raise HTTPException(
            status_code=409,
            detail="No se puede anular en este estado"
        )

    resultado = await pedidos_db.update_one(
        {
            "id": pedido_id,
            "estado": estado
        },
        {
            "$set": {
                "estado": nuevo_estado,
                "motivo_anulacion": solicitud.motivo
            }
        }
    )

    if resultado.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail="El estado del pedido cambio"
        )

    return await buscar_pedido(pedido_id)


async def intentar_publicar_evento(pedido_id: str, operacion_id: str) -> dict:
    """Entrega mejor esfuerzo: no cambia el pago si broker no está disponible."""
    from pymongo import ReturnDocument
    pedido = await pedidos_db.find_one_and_update(
        {"id": pedido_id, "estado": {"$in": ["pagado", "en_preparacion", "listo", "en_reparto", "entregado"]},
         "event_status": {"$in": ["pendiente", "fallido"]}},
        {"$set": {"event_status": "publicando"}},
        return_document=ReturnDocument.AFTER)
    if not pedido:
        return await buscar_pedido(pedido_id)
    try:
        await asyncio.to_thread(publicar_pedido_pagado, pedido, operacion_id)
    except Exception as error:
        await pedidos_db.update_one({"id": pedido_id, "event_status": "publicando"},
            {"$set": {"event_status": "fallido", "event_published": False,
                      "event_error": type(error).__name__}})
        logger.warning("operacion_id=%s db=mongo event=publish_failed order_id=%s error_type=%s",
                       operacion_id, pedido_id, type(error).__name__)
    else:
        await pedidos_db.update_one({"id": pedido_id, "event_status": "publicando"},
            {"$set": {"event_status": "enviado_sin_confirmacion_de_consumo", "event_published": True,
                      "event_error": None, "event_sent_at": datetime.now(timezone.utc).isoformat()}})
        logger.info("operacion_id=%s db=mongo event=send_registered order_id=%s", operacion_id, pedido_id)
    return await buscar_pedido(pedido_id)


@app.post("/orders/{pedido_id}/publish-event")
async def reintentar_publicacion(pedido_id: str, request: Request, auth=Depends(verificar_gateway)):
    if not auth["admin"] and "staff" not in auth["roles"]:
        raise HTTPException(status_code=403, detail="Solo personal autorizado")
    pedido = await buscar_pedido(pedido_id)
    if pedido["estado"] == "pendiente_pago":
        raise HTTPException(status_code=409, detail="Pago no confirmado")
    if pedido.get("event_status") == "publicando":
        raise HTTPException(status_code=409, detail="Publicación en curso")
    if pedido.get("event_published"):
        return pedido
    return await intentar_publicar_evento(pedido_id, request.state.operacion_id)


@app.post("/orders/{pedido_id}/confirm-payment")
async def confirmar_pago(
    pedido_id: str,
    confirmacion: ConfirmacionPago,
    request: Request,
    x_payments_secret: str = Header(default=""),
    auth=Depends(verificar_gateway)
):
    if (
        "payments" not in auth["roles"]
        or not PAYMENTS_TO_ORDERS_SECRET
        or not secrets.compare_digest(
            x_payments_secret,
            PAYMENTS_TO_ORDERS_SECRET
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Servicio de pagos no autorizado"
        )

    pedido = await buscar_pedido(pedido_id)

    if (
        pedido["estado"] == "pagado"
        and pedido["referencia_pago"] == confirmacion.referencia
    ):
        if pedido.get("event_status") in ("pendiente", "fallido"):
            return await intentar_publicar_evento(pedido_id, request.state.operacion_id)
        return pedido

    if pedido["estado"] != "pendiente_pago":
        raise HTTPException(
            status_code=409,
            detail="Pedido no pendiente"
        )

    resultado = await pedidos_db.update_one(
        {
            "id": pedido_id,
            "estado": "pendiente_pago"
        },
        {
            "$set": {
                "estado": "pagado",
                "referencia_pago": confirmacion.referencia,
                "event_status": "pendiente"
            }
        }
    )

    if resultado.modified_count == 0:
        actual = await buscar_pedido(pedido_id)
        if actual.get("referencia_pago") == confirmacion.referencia and actual["estado"] == "pagado":
            return actual
        raise HTTPException(status_code=409, detail="El estado del pedido cambio")

    logger.info("operacion_id=%s db=mongo action=confirm_paid_order order_id=%s",request.state.operacion_id,pedido_id)
    return await intentar_publicar_evento(pedido_id, request.state.operacion_id)


@app.put("/orders/{pedido_id}/status")
async def cambiar_estado(
    pedido_id: str,
    cambio: CambioEstado,
    auth=Depends(verificar_gateway)
):
    if not auth["admin"] and "staff" not in auth["roles"]:
        raise HTTPException(status_code=403, detail="Permiso de operador requerido")

    pedido = await buscar_pedido(pedido_id)

    transiciones = {
        "pagado": ["en_preparacion"],
        "en_preparacion": ["listo"],
        "listo": ["en_reparto"] if pedido["modalidad"] == "delivery" else ["entregado"],
        "en_reparto": ["entregado"]
    }

    if cambio.estado not in transiciones.get(pedido["estado"], []):
        raise HTTPException(
            status_code=409,
            detail="Transicion no permitida"
        )

    resultado = await pedidos_db.update_one(
        {
            "id": pedido_id,
            "estado": pedido["estado"]
        },
        {
            "$set": {
                "estado": cambio.estado
            }
        }
    )

    if resultado.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail="El estado del pedido cambio"
        )

    return await buscar_pedido(pedido_id)


@app.get("/orders/{pedido_id}/comprobante")
async def comprobante_no_tributario(pedido_id: str, auth=Depends(verificar_gateway)):
    """Comprobante comercial informativo; NO es boleta tributaria SII."""
    pedido = await buscar_pedido(pedido_id)
    verificar_propiedad(pedido, auth)
    if pedido["estado"] not in {"pagado", "en_preparacion", "listo", "en_reparto", "entregado", "anulacion_solicitada"}:
        raise HTTPException(status_code=409, detail="El pedido aún no registra pago confirmado")
    return {
        "tipo": "COMPROBANTE_COMERCIAL_NO_TRIBUTARIO",
        "leyenda": "Documento informativo; no es boleta ni factura electrónica autorizada por SII",
        "pedido_id": pedido["id"], "cliente_id": pedido["client_id"],
        "fecha": pedido["fecha"], "modalidad": pedido["modalidad"],
        "items": pedido["items"], "total_clp": pedido["total"],
        "estado": pedido["estado"], "referencia_pago": pedido.get("referencia_pago")
    }
