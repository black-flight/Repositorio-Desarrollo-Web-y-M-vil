import os
import secrets
from datetime import date

from fastapi import Depends, FastAPI, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

app = FastAPI(title="Tokyo Noodles - Clients")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("Configurar INTERNAL_GATEWAY_SECRET")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)
clientes_db = mongo["tokyo_noodles_eval2"]["clients"]


class Cliente(BaseModel):
    id: str = Field(pattern=r"^USR-[0-9]+$")
    run: str = Field(min_length=7)
    nombre: str = Field(min_length=3)
    direccion: str = Field(min_length=5)
    comuna: str = Field(min_length=2)
    provincia: str = Field(min_length=2)
    region: str = Field(min_length=2)
    fecha_nacimiento: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    sexo: str = Field(min_length=1)
    correo: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    telefono: str = Field(min_length=8)


def verificar_gateway(
    x_gateway_secret: str = Header(default=""),
    x_authenticated_client: str = Header(default=""),
    x_authenticated_roles: str = Header(default="")
):
    if not secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET):
        raise HTTPException(status_code=403, detail="Gateway no autorizado")
    if not x_authenticated_client:
        raise HTTPException(status_code=401, detail="Identidad requerida")
    return {
        "id": x_authenticated_client,
        "admin": "admin" in x_authenticated_roles.split(",")
    }


def comprobar_propietario(auth, client_id):
    if not auth["admin"] and auth["id"] != client_id:
        raise HTTPException(status_code=403, detail="No tiene permiso sobre este cliente")


def validar_fecha(fecha):
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha de nacimiento invalida")


@app.get("/health")
def health():
    return {"status": "OK", "service": "clients"}


@app.get("/clients")
async def listar_clientes(auth=Depends(verificar_gateway)):
    if not auth["admin"]:
        raise HTTPException(status_code=403, detail="Permiso de administrador requerido")
    return {"clients": await clientes_db.find({}, {"_id": 0}).to_list(length=200)}


@app.get("/clients/{client_id}")
async def consultar_cliente(client_id: str, auth=Depends(verificar_gateway)):
    comprobar_propietario(auth, client_id)
    cliente = await clientes_db.find_one({"id": client_id}, {"_id": 0})
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@app.post("/clients", status_code=201)
async def registrar_cliente(cliente: Cliente, auth=Depends(verificar_gateway)):
    comprobar_propietario(auth, cliente.id)
    validar_fecha(cliente.fecha_nacimiento)
    duplicado = await clientes_db.find_one({
        "$or": [{"id": cliente.id}, {"run": cliente.run}, {"correo": cliente.correo}]
    })
    if duplicado is not None:
        raise HTTPException(status_code=409, detail="Cliente, RUN o correo ya registrado")
    documento = cliente.model_dump()
    documento["activo"] = True
    documento["correo_verificado"] = False
    await clientes_db.insert_one(documento)
    documento.pop("_id", None)
    return documento


@app.put("/clients/{client_id}")
async def modificar_cliente(client_id: str, cliente: Cliente, auth=Depends(verificar_gateway)):
    comprobar_propietario(auth, client_id)
    if cliente.id != client_id:
        raise HTTPException(status_code=400, detail="El ID no coincide")
    validar_fecha(cliente.fecha_nacimiento)
    repetido = await clientes_db.find_one({
        "id": {"$ne": client_id},
        "$or": [{"run": cliente.run}, {"correo": cliente.correo}]
    })
    if repetido is not None:
        raise HTTPException(status_code=409, detail="RUN o correo ya registrado")
    documento = cliente.model_dump()
    documento["correo_verificado"] = False
    resultado = await clientes_db.update_one({"id": client_id}, {"$set": documento})
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return await clientes_db.find_one({"id": client_id}, {"_id": 0})


@app.delete("/clients/{client_id}")
async def desactivar_cliente(client_id: str, auth=Depends(verificar_gateway)):
    if not auth["admin"]:
        raise HTTPException(status_code=403, detail="Permiso de administrador requerido")
    resultado = await clientes_db.update_one({"id": client_id}, {"$set": {"activo": False}})
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente desactivado", "id": client_id}