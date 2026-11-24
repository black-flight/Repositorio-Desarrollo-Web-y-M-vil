import os
import re
import logging

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.common.tracing import instalar_trazabilidad

app = FastAPI(title="Tokyo Noodles - API Gateway")
logger = logging.getLogger("tokyo_noodles.gateway")
security = HTTPBearer(auto_error=False)
instalar_trazabilidad(app, "api-gateway")

ORIGENES_FRONTEND = [
    origen.strip()
    for origen in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost,http://127.0.0.1,http://localhost:80,"
        "http://127.0.0.1:80,http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if origen.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_FRONTEND,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Operacion"],
    max_age=600
)

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:9003")
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://127.0.0.1:9001")
ORDERS_URL = os.getenv("ORDERS_URL", "http://127.0.0.1:9002")
CLIENTS_URL = os.getenv("CLIENTS_URL", "http://127.0.0.1:9004")
PAYMENTS_URL = os.getenv("PAYMENTS_URL", "http://127.0.0.1:9005")
GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://127.0.0.1:8090")

if not VAULT_TOKEN:
    raise RuntimeError("Configurar VAULT_TOKEN")


async def secretos_gateway(operacion_id: str = ""):
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.get(
                f"{VAULT_ADDR}/v1/secret/data/gateway",
                headers={
                    "X-Vault-Token": VAULT_TOKEN,
                    "X-Operacion": operacion_id
                }
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Vault no disponible"
        )

    if respuesta.status_code != 200:
        raise HTTPException(
            status_code=503,
            detail="No se pudo consultar Vault"
        )

    datos = respuesta.json().get("data", {}).get("data", {})

    if (
        not datos.get("backend_shared_secret")
        or not datos.get("auth_introspection_secret")
    ):
        raise HTTPException(
            status_code=503,
            detail="Secretos incompletos en Vault"
        )

    logger.info("operacion_id=%s service=vault action=kv_read path=secret/data/gateway status=ok", operacion_id)
    return datos


async def autenticar(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer token requerido"
        )

    operacion_id = request.state.operacion_id
    secretos = await secretos_gateway(operacion_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.post(
                f"{AUTH_SERVICE_URL}/introspect",
                json={
                    "token": credentials.credentials
                },
                headers={
                    "X-Gateway-Auth-Secret": secretos["auth_introspection_secret"],
                    "X-Operacion": operacion_id
                }
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Auth Service no disponible"
        )

    if respuesta.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="No se pudo validar la identidad"
        )

    identidad = respuesta.json()
    logger.info("operacion_id=%s service=auth action=introspect authorized=%s", operacion_id, bool(identidad.get("active")))

    if not identidad.get("active"):
        raise HTTPException(
            status_code=401,
            detail="Token invalido o expirado"
        )

    return {
        "id": identidad["user_id"],
        "usuario": identidad["username"],
        "roles": identidad["roles"],
        "secret": secretos["backend_shared_secret"]
    }


def destino_autorizado(metodo, path, roles):
    admin = "admin" in roles
    staff = "staff" in roles

    if re.fullmatch(r"products", path) and metodo == "GET":
        return INVENTORY_URL

    if re.fullmatch(r"products/[0-9]+", path) and metodo == "GET":
        return INVENTORY_URL

    if re.fullmatch(r"products", path) and metodo == "POST" and admin:
        return INVENTORY_URL

    if (
        re.fullmatch(r"products/[0-9]+", path)
        and metodo in ("PUT", "DELETE")
        and admin
    ):
        return INVENTORY_URL

    if re.fullmatch(r"clients/USR-[0-9]+/email/(send-code|verify)", path) and metodo == "POST":
        return CLIENTS_URL

    if path == "clients" and metodo == "GET" and admin:
        return CLIENTS_URL

    if path == "clients" and metodo == "POST":
        return CLIENTS_URL

    if re.fullmatch(r"clients/USR-[0-9]+", path):
        if metodo in ("GET", "PUT"):
            return CLIENTS_URL

        if metodo == "DELETE" and admin:
            return CLIENTS_URL

    if re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/publish-event", path) and metodo == "POST" and (admin or staff):
        return ORDERS_URL

    if path == "orders/reporte-ventas" and metodo == "GET" and admin:
        return ORDERS_URL

    if re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/comprobante", path) and metodo == "GET":
        return ORDERS_URL

    if path == "orders" and metodo == "GET":
        return ORDERS_URL
    if path == "orders" and metodo == "POST" and "user" in roles:
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+", path)
        and metodo == "GET"
    ):
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/cancel", path)
        and metodo == "POST"
        and "user" in roles
    ):
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/status", path)
        and metodo == "PUT"
        and (admin or staff)
    ):
        return ORDERS_URL

    if re.fullmatch(r"payments/order/ORD-[A-Za-z0-9-]+", path) and metodo == "GET":
        return PAYMENTS_URL

    if path == "payments" and metodo == "POST":
        return PAYMENTS_URL

    if (
        re.fullmatch(r"payments/PAY-[A-Za-z0-9-]+", path)
        and metodo == "GET"
    ):
        return PAYMENTS_URL

    if path == "orders/eventos" and metodo == "GET" and admin:
        return ORDERS_URL

    return None


class RegistroCompleto(BaseModel):
    username: str = Field(pattern=r"^[a-z][a-z0-9_]{2,31}$")
    password: str = Field(min_length=8, max_length=128)
    run: str = Field(min_length=7)
    nombre: str = Field(min_length=3)
    direccion: str = Field(min_length=5)
    comuna: str = Field(min_length=2)
    provincia: str = Field(min_length=2)
    region: str = Field(min_length=2)
    fecha_nacimiento: str
    sexo: str = Field(min_length=1)
    correo: str = Field(min_length=5)
    telefono: str = Field(min_length=8)


@app.post("/api/auth/register", status_code=201)
async def registrar_cliente_completo(datos: RegistroCompleto, request: Request):
    """Registro orquestado: Auth + Clients, con compensación en fallo."""
    secretos = await secretos_gateway(request.state.operacion_id)
    auth_headers = {
        "X-Gateway-Auth-Secret": secretos["auth_introspection_secret"],
        "X-Operacion": request.state.operacion_id
    }
    async with httpx.AsyncClient(timeout=8.0) as cliente:
        try:
            creacion = await cliente.post(
                f"{AUTH_SERVICE_URL}/register", headers=auth_headers,
                json={"username": datos.username, "password": datos.password}
            )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth no disponible")
        if creacion.status_code != 201:
            return Response(content=creacion.content,
                            status_code=creacion.status_code,
                            media_type="application/json")
        user_id = creacion.json()["user_id"]
        perfil = datos.model_dump(exclude={"username", "password"})
        perfil["id"] = user_id
        headers = {
            "X-Gateway-Secret": secretos["backend_shared_secret"],
            "X-Authenticated-Client": user_id,
            "X-Authenticated-Roles": "user",
            "X-Operacion": request.state.operacion_id
        }
        try:
            respuesta = await cliente.post(
                f"{CLIENTS_URL}/clients", json=perfil, headers=headers
            )
            if respuesta.status_code != 201:
                raise HTTPException(status_code=respuesta.status_code,
                                    detail="El perfil no pudo registrarse; se revirtió la cuenta Auth")
        except (httpx.RequestError, HTTPException) as error:
            try:
                revertir = await cliente.delete(
                    f"{AUTH_SERVICE_URL}/internal/registration/{user_id}",
                    headers=auth_headers
                )
                if revertir.status_code != 200:
                    raise RuntimeError("Rollback sin confirmar")
            except (httpx.RequestError, RuntimeError):
                raise HTTPException(status_code=503,
                    detail="Registro incompleto: contactar soporte para conciliación")
            if isinstance(error, HTTPException):
                raise error
            raise HTTPException(status_code=503, detail="Clients no disponible; cuenta revertida")
    codigo_status = {"estado": "no_intentado", "detalle": "Requiere solicitar código desde el perfil"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as cliente:
            aviso = await cliente.post(f"{CLIENTS_URL}/clients/{user_id}/email/send-code", headers=headers)
        if aviso.status_code == 200:
            codigo_status = aviso.json()
        else:
            codigo_status = {"estado": "fallido", "detalle": "Perfil creado; no se pudo generar notificación"}
    except httpx.RequestError:
        codigo_status = {"estado": "fallido", "detalle": "Perfil creado; servicio de correo no disponible"}
    return {"user_id": user_id, "username": datos.username, "perfil_registrado": True,
            "verificacion_correo": codigo_status}


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "API Gateway"
    }


@app.post("/api/auth/login")
async def login(request: Request):
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.post(
                f"{AUTH_SERVICE_URL}/login",
                content=await request.body(),
                headers={
                    "Content-Type": "application/json",
                    "X-Operacion": request.state.operacion_id
                }
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Auth Service no disponible"
        )

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        media_type="application/json"
    )


@app.post("/api/auth/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth=Depends(autenticar)
):
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.post(
                f"{AUTH_SERVICE_URL}/logout",
                json={
                    "token": credentials.credentials
                },
                headers={"X-Operacion": request.state.operacion_id}
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Auth Service no disponible"
        )

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        media_type="application/json"
    )


@app.get("/api/auth/me")
async def obtener_sesion_actual(auth=Depends(autenticar)):
    """Devuelve solo la identidad validada por Auth Service."""
    return {
        "user_id": auth["id"],
        "username": auth["usuario"],
        "roles": auth["roles"]
    }


@app.post("/api/payments/{payment_id}/test-confirm")
async def confirmar_pago_demo(payment_id: str, request: Request, auth=Depends(autenticar)):
    if "admin" not in auth["roles"]:
        raise HTTPException(status_code=403, detail="Solo administrador de pruebas")
    if not re.fullmatch(r"PAY-[A-Za-z0-9-]+", payment_id):
        raise HTTPException(status_code=400, detail="ID de pago inválido")
    secretos = await secretos_gateway(request.state.operacion_id)
    clave = secretos.get("payment_test_secret")
    if not clave:
        raise HTTPException(status_code=503, detail="Confirmación demo no configurada en Vault")
    try:
        async with httpx.AsyncClient(timeout=20.0) as cliente:
            respuesta = await cliente.post(
                f"{PAYMENTS_URL}/payments/{payment_id}/test-confirm",
                headers={"X-Payment-Test-Secret": clave, "X-Operacion": request.state.operacion_id}
            )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Payments no disponible")
    return Response(content=respuesta.content, status_code=respuesta.status_code,
                    media_type="application/json")


@app.get("/api/public/products")
async def catalogo_publico(request: Request):
    """Expone el catálogo sin token de usuario, pero nunca sin secreto interno."""
    secretos = await secretos_gateway(request.state.operacion_id)
    try:
        async with httpx.AsyncClient(timeout=8.0) as cliente:
            respuesta = await cliente.get(
                f"{INVENTORY_URL}/products",
                params=request.query_params,
                headers={
                    "X-Gateway-Secret": secretos["backend_shared_secret"],
                    "X-Operacion": request.state.operacion_id
                }
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Inventario no disponible")

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        media_type="application/json"
    )


@app.post("/api/graphql")
async def graphql_proxy(
    request: Request,
    auth=Depends(autenticar)
):
    contenido = await request.body()

    if len(contenido) > 8192:
        raise HTTPException(
            status_code=413,
            detail="Consulta demasiado grande"
        )

    secretos = await secretos_gateway(request.state.operacion_id)
    graphql_secret = secretos.get("graphql_shared_secret")

    if not graphql_secret:
        raise HTTPException(
            status_code=503,
            detail="Secreto GraphQL no configurado"
        )

    cabeceras = {
        "Content-Type": "application/json",
        "X-Graphql-Secret": graphql_secret,
        "X-Authenticated-Client": auth["id"],
        "X-Authenticated-Roles": ",".join(auth["roles"]),
        "X-Operacion": request.state.operacion_id
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.post(
                f"{GRAPHQL_URL}/graphql",
                content=contenido,
                headers=cabeceras
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="GraphQL no disponible"
        )

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        media_type="application/json"
    )


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def proxy(
    path: str,
    request: Request,
    auth=Depends(autenticar)
):
    destino = destino_autorizado(
        request.method,
        path,
        auth["roles"]
    )

    if destino is None:
        raise HTTPException(
            status_code=403,
            detail="Operacion no autorizada"
        )

    headers = {
        "X-Gateway-Secret": auth["secret"],
        "X-Authenticated-Client": auth["id"],
        "X-Authenticated-User": auth["usuario"],
        "X-Authenticated-Roles": ",".join(auth["roles"]),
        "X-Operacion": request.state.operacion_id
    }

    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]

    logger.info("operacion_id=%s service=api-gateway action=route target=%s path=%s", request.state.operacion_id, destino, path)
    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.request(
                request.method,
                f"{destino}/{path}",
                params=request.query_params,
                content=await request.body(),
                headers=headers
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Servicio interno no disponible"
        )

    tipo = respuesta.headers.get(
        "content-type",
        "application/json"
    )

    return Response(
        content=respuesta.content,
        status_code=respuesta.status_code,
        headers={
            "Content-Type": tipo
        }
    )