import os
import secrets
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="Tokyo Noodles - Orders")

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


class ItemPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(pattern=r"^[0-9]+$")
    quantity: int = Field(gt=0, le=30)


class NuevoPedido(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ItemPedido] = Field(min_length=1)
    modalidad: Literal["retiro", "delivery"]
    direccion: str | None = None


class Anulacion(BaseModel):
    motivo: str = Field(min_length=5)


class ConfirmacionPago(BaseModel):
    referencia: str = Field(min_length=4)


class CambioEstado(BaseModel):
    estado: Literal["en_preparacion", "listo", "en_reparto", "entregado"]


def verificar_gateway(
    x_gateway_secret: str = Header(default=""),
    x_authenticated_client: str = Header(default=""),
    x_authenticated_roles: str = Header(default="")
):
    if not secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET):
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
    if not auth["admin"] and pedido["client_id"] != auth["id"]:
        raise HTTPException(
            status_code=403,
            detail="Pedido de otro cliente"
        )


async def buscar_pedido(pedido_id):
    pedido = await pedidos_db.find_one(
        {"id": pedido_id},
        {"_id": 0}
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
    filtro = {} if auth["admin"] else {
        "client_id": auth["id"]
    }

    pedidos = await pedidos_db.find(
        filtro,
        {"_id": 0}
    ).to_list(length=200)

    return {"orders": pedidos}


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
    auth=Depends(verificar_gateway)
):
    if nuevo.modalidad == "delivery" and not (nuevo.direccion or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Direccion requerida para delivery"
        )

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
                    "X-Authenticated-Client": auth["id"]
                }
            )

            if registro.status_code != 200 or not registro.json().get("activo", False):
                raise HTTPException(
                    status_code=403,
                    detail="Cliente no registrado o inactivo"
                )

            for item in nuevo.items:
                respuesta = await cliente.get(
                    f"{INVENTORY_URL}/products/{item.product_id}",
                    headers={
                        "X-Gateway-Secret": INTERNAL_GATEWAY_SECRET
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
        "motivo_anulacion": None
    }

    await pedidos_db.insert_one(pedido)
    pedido.pop("_id", None)

    return pedido


@app.post("/orders/{pedido_id}/cancel")
async def anular_pedido(
    pedido_id: str,
    solicitud: Anulacion,
    auth=Depends(verificar_gateway)
):
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


@app.post("/orders/{pedido_id}/confirm-payment")
async def confirmar_pago(
    pedido_id: str,
    confirmacion: ConfirmacionPago,
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
                "referencia_pago": confirmacion.referencia
            }
        }
    )

    if resultado.modified_count == 0:
        raise HTTPException(
            status_code=409,
            detail="El estado del pedido cambio"
        )

    return await buscar_pedido(pedido_id)


@app.put("/orders/{pedido_id}/status")
async def cambiar_estado(
    pedido_id: str,
    cambio: CambioEstado,
    auth=Depends(verificar_gateway)
):
    if not auth["admin"]:
        raise HTTPException(
            status_code=403,
            detail="Permiso de administrador requerido"
        )

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
