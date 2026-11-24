import os
import secrets
import hashlib
import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from backend.common.tracing import instalar_trazabilidad
from backend.common.notifications import enviar_notificacion, modo_correo


app = FastAPI(title="Tokyo Noodles - Clients")
instalar_trazabilidad(app, "clients")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")
if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("Configurar INTERNAL_GATEWAY_SECRET")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)
base = mongo["tokyo_noodles_eval2"]
clientes_db = base["clients"]
verificaciones_db = base["email_verifications"]
logger = logging.getLogger("tokyo_noodles.clients")


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
    request: Request,
    x_gateway_secret: str = Header(default=""),
    x_authenticated_client: str = Header(default=""),
    x_authenticated_roles: str = Header(default="")
):
    permitido = secrets.compare_digest(x_gateway_secret, INTERNAL_GATEWAY_SECRET)
    logger.info("operacion_id=%s service=clients secret_check=%s", request.state.operacion_id, "ok" if permitido else "rejected")
    if not permitido:
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


@app.on_event("startup")
async def preparar_datos_demo():
    await mongo.admin.command("ping")
    await clientes_db.create_index("id", unique=True)
    await clientes_db.create_index("run", unique=True)
    await clientes_db.create_index("correo", unique=True)
    await verificaciones_db.create_index("client_id", unique=True)
    if os.getenv("DEMO_SEED_PROFILES") != "1":
        return
    # Todos los registros son FICTICIOS; no representan personas reales.
    for numero, nombre in [(1, "Ana Demo"), (2, "Pedro Demo"), (3, "Ernesto Demo")]:
        cid = f"USR-{numero:03d}"
        registro = {
            "id": cid, "run": f"RUN-FICTICIO-{numero:03d}",
            "nombre": nombre, "direccion": "Calle Ficticia 100", "comuna": "Maipú",
            "provincia": "Santiago", "region": "Metropolitana",
            "fecha_nacimiento": "1995-01-01", "sexo": "X",
            "correo": f"demo{numero}@example.test", "telefono": "000000000",
            "activo": True, "correo_verificado": False
        }
        await clientes_db.update_one({"id": cid}, {"$setOnInsert": registro}, upsert=True)


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
    previo = await clientes_db.find_one({"id": client_id}, {"correo": 1, "correo_verificado": 1})
    documento["correo_verificado"] = bool(previo and previo.get("correo") == cliente.correo and previo.get("correo_verificado"))
    if previo and previo.get("correo") != cliente.correo:
        await verificaciones_db.delete_one({"client_id": client_id})
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

class ValidarCodigo(BaseModel):
    codigo: str = Field(pattern=r"^[0-9]{6}$")


@app.post("/clients/{client_id}/email/send-code")
async def enviar_codigo(client_id: str, request: Request, auth=Depends(verificar_gateway)):
    comprobar_propietario(auth, client_id)
    cliente = await clientes_db.find_one({"id": client_id, "activo": True})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    codigo = f"{secrets.randbelow(1000000):06d}"
    sal = secrets.token_hex(16)
    modo = modo_correo()
    if modo == "configuracion_incompleta":
        raise HTTPException(status_code=503, detail="API de correo incompleta")
    await verificaciones_db.update_one(
        {"client_id":client_id},
        {"$set": {"client_id":client_id,"correo":cliente["correo"],
                  "codigo_hash":hashlib.sha256((sal+codigo).encode()).hexdigest(),
                  "salt":sal,"intentos":0,"modo":modo,"usado":False,
                  "vence_en":datetime.now(timezone.utc)+timedelta(minutes=15)}},upsert=True)
    notificacion = await enviar_notificacion(base,"verificacion_registro",cliente["correo"],
        "Tokyo Noodles - Código de verificación",
        "Código de verificación: " + codigo + ". Válido durante 15 minutos.",
        request.state.operacion_id, codigo_demo=codigo)
    await verificaciones_db.update_one({"client_id":client_id},
        {"$set":{"notificacion_estado":notificacion["estado"]}})
    if modo == "http" and notificacion["estado"] != "aceptado_por_api_entrega_no_confirmada":
        return {"estado": "fallido", "modo":modo, "detalle":"La API de correo no aceptó el mensaje"}
    resultado = {"estado":notificacion["estado"],"modo":modo,
        "detalle":"Aceptar la API no demuestra recepción por destinatario" if modo=="http"
        else "Solo DEMO: no se envió correo y no se acredita su existencia"}
    if modo == "demo" and os.getenv("EMAIL_DEMO_MODE","1") == "1":
        resultado["codigo_demo"] = codigo
    return resultado


@app.post("/clients/{client_id}/email/verify")
async def verificar_codigo(client_id: str, data: ValidarCodigo, request: Request,
                           auth=Depends(verificar_gateway)):
    comprobar_propietario(auth, client_id)
    comprobante = await verificaciones_db.find_one({"client_id":client_id,"usado":False})
    if not comprobante:
        raise HTTPException(status_code=404,detail="No hay código vigente")
    if comprobante["vence_en"] <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=410,detail="Código expirado")
    if comprobante.get("intentos",0)>=5:
        raise HTTPException(status_code=429,detail="Demasiados intentos")
    if comprobante["modo"] == "http" and comprobante.get("notificacion_estado") != "aceptado_por_api_entrega_no_confirmada":
        raise HTTPException(status_code=409, detail="El proveedor no aceptó el envío del código")
    await verificaciones_db.update_one({"client_id":client_id,"usado":False}, {"$inc":{"intentos":1}})
    digest=hashlib.sha256((comprobante["salt"]+data.codigo).encode()).hexdigest()
    if not secrets.compare_digest(digest,comprobante["codigo_hash"]):
        raise HTTPException(status_code=422,detail="Código incorrecto")
    if comprobante["modo"]=="http":
        r=await clientes_db.update_one({"id":client_id,"correo":comprobante["correo"]},
                                       {"$set":{"correo_verificado":True}})
        if not r.matched_count:
            raise HTTPException(status_code=409,detail="Correo del perfil cambió")
        estado="verificado_por_codigo_recibido"
    else:
        await clientes_db.update_one({"id":client_id}, {"$set":{"correo_verificacion_demo":True}})
        estado="codigo_demo_validado_sin_verificacion_externa"
    await verificaciones_db.update_one({"client_id":client_id}, {"$set":{"usado":True}})
    logger.info("operacion_id=%s db=mongo action=email_code_verified mode=%s client_id=%s",
                request.state.operacion_id, comprobante["modo"], client_id)
    return {"estado":estado, "correo_verificado":comprobante["modo"]=="http"}
