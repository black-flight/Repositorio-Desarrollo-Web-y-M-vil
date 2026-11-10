import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

app = FastAPI(title="Tokyo Noodles - Auth Service")

AUTH_INTROSPECTION_SECRET = os.getenv("AUTH_INTROSPECTION_SECRET")

if not AUTH_INTROSPECTION_SECRET:
    raise RuntimeError("Configurar AUTH_INTROSPECTION_SECRET")

mongo = AsyncIOMotorClient(
    os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017"),
    serverSelectionTimeoutMS=3000
)

base = mongo["tokyo_noodles_eval2"]
usuarios_db = base["auth_users"]
sesiones_db = base["auth_sessions"]

TOKEN_LIFETIME_MINUTES = 15


def crear_hash(clave, sal=None):
    if sal is None:
        sal = secrets.token_bytes(16)

    resultado = hashlib.pbkdf2_hmac(
        "sha256",
        clave.encode("utf-8"),
        sal,
        250000
    )

    return sal.hex(), resultado.hex()


def clave_valida(clave, usuario):
    try:
        sal = bytes.fromhex(usuario["salt"])
        _, recibido = crear_hash(clave, sal)

        return secrets.compare_digest(
            recibido,
            usuario["password_hash"]
        )
    except (KeyError, ValueError):
        return False


def fecha_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistroRequest(BaseModel):
    username: str = Field(pattern=r"^[a-z][a-z0-9_]{2,31}$")
    password: str = Field(min_length=8, max_length=128)


class TokenRequest(BaseModel):
    token: str


@app.on_event("startup")
async def inicializar():
    await mongo.admin.command("ping")

    await usuarios_db.create_index("username", unique=True)
    await usuarios_db.create_index("user_id", unique=True)

    await sesiones_db.create_index("token_hash", unique=True)
    await sesiones_db.create_index("expires_at", expireAfterSeconds=0)

    ejemplos = (
        ("ana", "USR-001", ["user"], "AUTH_PASSWORD_ANA"),
        ("pedro", "USR-002", ["user"], "AUTH_PASSWORD_PEDRO"),
        ("ernesto", "USR-003", ["user", "admin"], "AUTH_PASSWORD_ERNESTO")
    )

    for nombre, identificador, roles, variable in ejemplos:
        clave = os.getenv(variable)

        if clave and len(clave) < 8:
            raise RuntimeError(f"{variable} requiere al menos 8 caracteres")

        if clave and not await usuarios_db.find_one({"username": nombre}):
            sal, clave_hash = crear_hash(clave)

            try:
                await usuarios_db.insert_one({
                    "username": nombre,
                    "user_id": identificador,
                    "roles": roles,
                    "salt": sal,
                    "password_hash": clave_hash,
                    "active": True
                })
            except DuplicateKeyError:
                pass


@app.post("/register", status_code=201)
async def registro(datos: RegistroRequest):
    sal, clave_hash = crear_hash(datos.password)

    identificador = "USR-" + str(
        secrets.randbelow(900000000) + 100000000
    )

    try:
        await usuarios_db.insert_one({
            "username": datos.username,
            "user_id": identificador,
            "roles": ["user"],
            "salt": sal,
            "password_hash": clave_hash,
            "active": True
        })
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Usuario ya registrado"
        )

    return {
        "username": datos.username,
        "user_id": identificador
    }


@app.post("/login")
async def login(datos: LoginRequest):
    usuario = await usuarios_db.find_one({
        "username": datos.username
    })

    if (
        not usuario
        or not usuario.get("active")
        or not clave_valida(datos.password, usuario)
    ):
        raise HTTPException(
            status_code=401,
            detail="Credenciales incorrectas"
        )

    token = secrets.token_urlsafe(32)

    vencimiento = fecha_utc() + timedelta(
        minutes=TOKEN_LIFETIME_MINUTES
    )

    await sesiones_db.insert_one({
        "token_hash": hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest(),
        "user_id": usuario["user_id"],
        "username": usuario["username"],
        "roles": usuario["roles"],
        "expires_at": vencimiento
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_LIFETIME_MINUTES * 60
    }


@app.post("/introspect")
async def introspect(
    datos: TokenRequest,
    x_gateway_auth_secret: str = Header(default="")
):
    if not secrets.compare_digest(
        x_gateway_auth_secret,
        AUTH_INTROSPECTION_SECRET
    ):
        raise HTTPException(
            status_code=403,
            detail="Gateway no autorizado"
        )

    token_hash = hashlib.sha256(
        datos.token.encode("utf-8")
    ).hexdigest()

    sesion = await sesiones_db.find_one({
        "token_hash": token_hash
    })

    if not sesion:
        return {"active": False}

    if sesion["expires_at"] <= fecha_utc():
        await sesiones_db.delete_one({
            "token_hash": token_hash
        })

        return {"active": False}

    usuario = await usuarios_db.find_one({
        "user_id": sesion["user_id"],
        "active": True
    })

    if not usuario:
        return {"active": False}

    return {
        "active": True,
        "user_id": usuario["user_id"],
        "username": usuario["username"],
        "roles": usuario["roles"]
    }


@app.post("/logout")
async def logout(datos: TokenRequest):
    token_hash = hashlib.sha256(
        datos.token.encode("utf-8")
    ).hexdigest()

    await sesiones_db.delete_one({
        "token_hash": token_hash
    })

    return {"message": "Sesion finalizada"}


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "Authentication Service"
    }