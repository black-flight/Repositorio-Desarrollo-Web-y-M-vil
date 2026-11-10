import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

app = FastAPI(title="Tokyo Noodles - Inventory")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("Configurar INTERNAL_GATEWAY_SECRET")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)
productos_db = mongo["tokyo_noodles_eval2"]["products"]

catalogo_inicial = [
    {"id": "1", "nombre": "Shio Ramen", "descripcion": "Caldo ligero a base de almeja y pollo con aceite de camarón, chashu de cerdo, ajitama, wakame, nori, cebollín, sésamo y noodles.", "precio": 13800, "imagen": "img/shio.png", "categoria": "ramen", "available": True},
    {"id": "2", "nombre": "Miso Ramen", "descripcion": "Caldo consistente de miso, pollo y almeja, chashu de cerdo, ajitama, choclo, nori, cebollín, sésamo y noodles.", "precio": 14200, "imagen": "img/miso.png", "categoria": "ramen", "available": True},
    {"id": "3", "nombre": "Tantan Ramen", "descripcion": "Caldo de miso picante, pollo y almeja con sésamo, pulpa de cerdo molido picante, karaage, ajitama, nori y noodles.", "precio": 14900, "imagen": "img/tantan.png", "categoria": "ramen", "available": True},
    {"id": "4", "nombre": "Veggie Miso Especial", "descripcion": "Caldo de miso y verduras con aceite de hongos, tofu, shiitake grillado, choclo, kikurage, nori y fideos de la casa.", "precio": 15510, "imagen": "img/veggie-miso.png", "categoria": "ramen", "available": True},
    {"id": "5", "nombre": "Coca Cola Zero", "descripcion": "Coca Cola Zero", "precio": 2900, "imagen": "img/coca-zero.png", "categoria": "barra", "available": True},
    {"id": "6", "nombre": "Aka Natsu", "descripcion": "Syrup de betarraga, pulpa de maracuyá y jugo fresco de naranja en un mocktail dulce y cítrico.", "precio": 7800, "imagen": "img/aka-natsu.png", "categoria": "barra", "available": True},
    {"id": "7", "nombre": "Natsu No Hikari", "descripcion": "Cóctel refrescante con tamarindo, sake y pisco, equilibrado con goma y zumo de limón.", "precio": 9900, "imagen": "img/natsu-hikari.png", "categoria": "barra", "available": True},
    {"id": "8", "nombre": "Soukai", "descripcion": "Sake, vodka, kiwi, esferas de kiwi, pomelo, limón y syrup.", "precio": 9400, "imagen": "img/soukai.png", "categoria": "barra", "available": True},
    {"id": "9", "nombre": "Tokyo Classic", "descripcion": "Shio Ramen acompañado de una bebida clásica.", "precio": 15500, "imagen": "img/shio.png", "categoria": "promocion", "available": True},
    {"id": "10", "nombre": "Tokyo Experience", "descripcion": "Tantan Ramen acompañado de un Aka Natsu.", "precio": 20500, "imagen": "img/tantan.png", "categoria": "promocion", "available": True}
]


class Producto(BaseModel):
    id: str = Field(pattern=r"^[0-9]+$")
    nombre: str = Field(min_length=2)
    descripcion: str
    precio: int = Field(gt=0)
    imagen: str
    categoria: str
    available: bool = True


def verificar_gateway(x_gateway_secret: str = Header(default="")):
    if not secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET):
        raise HTTPException(status_code=403, detail="Gateway no autorizado")


def verificar_admin(
    x_authenticated_roles: str = Header(default=""),
    auth=Depends(verificar_gateway)
):
    if "admin" not in x_authenticated_roles.split(","):
        raise HTTPException(status_code=403, detail="Permiso de administrador requerido")


@app.on_event("startup")
async def inicializar():
    await mongo.admin.command("ping")
    for producto in catalogo_inicial:
        await productos_db.update_one(
            {"id": producto["id"]},
            {"$setOnInsert": producto},
            upsert=True
        )


@app.get("/health")
def health():
    return {"status": "OK", "service": "inventory"}


@app.get("/products", dependencies=[Depends(verificar_gateway)])
async def listar_productos(
    available: bool | None = None,
    x_authenticated_client: str | None = Header(default=None),
    x_authenticated_user: str | None = Header(default=None),
    x_authenticated_roles: str | None = Header(default=None)
):
    filtro = {} if available is None else {"available": available}
    productos = await productos_db.find(filtro, {"_id": 0}).to_list(length=200)
    productos.sort(key=lambda p: int(p["id"]))
    return {
        "identity": {
            "client_id": x_authenticated_client,
            "username": x_authenticated_user,
            "roles": x_authenticated_roles
        },
        "products": productos
    }


@app.get("/products/{product_id}", dependencies=[Depends(verificar_gateway)])
async def consultar_producto(product_id: str):
    producto = await productos_db.find_one({"id": product_id}, {"_id": 0})
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@app.post("/products", status_code=201, dependencies=[Depends(verificar_admin)])
async def crear_producto(producto: Producto):
    if await productos_db.find_one({"id": producto.id}):
        raise HTTPException(status_code=409, detail="Producto ya existe")
    await productos_db.insert_one(producto.model_dump())
    return producto.model_dump()


@app.put("/products/{product_id}", dependencies=[Depends(verificar_admin)])
async def modificar_producto(product_id: str, producto: Producto):
    if product_id != producto.id:
        raise HTTPException(status_code=400, detail="El ID no coincide")
    resultado = await productos_db.update_one(
        {"id": product_id}, {"$set": producto.model_dump()}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto.model_dump()


@app.delete("/products/{product_id}", dependencies=[Depends(verificar_admin)])
async def desactivar_producto(product_id: str):
    resultado = await productos_db.update_one(
        {"id": product_id}, {"$set": {"available": False}}
    )
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto desactivado", "id": product_id}
