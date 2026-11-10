import os
import re

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

app = FastAPI(title="Tokyo Noodles - API Gateway")
security = HTTPBearer(auto_error=False)

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


async def secretos_gateway():
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.get(
                f"{VAULT_ADDR}/v1/secret/data/gateway",
                headers={
                    "X-Vault-Token": VAULT_TOKEN
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

    return datos


async def autenticar(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Bearer token requerido"
        )

    secretos = await secretos_gateway()

    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.post(
                f"{AUTH_SERVICE_URL}/introspect",
                json={
                    "token": credentials.credentials
                },
                headers={
                    "X-Gateway-Auth-Secret": secretos["auth_introspection_secret"]
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

    if path == "clients" and metodo == "GET" and admin:
        return CLIENTS_URL

    if path == "clients" and metodo == "POST":
        return CLIENTS_URL

    if re.fullmatch(r"clients/USR-[0-9]+", path):
        if metodo in ("GET", "PUT"):
            return CLIENTS_URL

        if metodo == "DELETE" and admin:
            return CLIENTS_URL

    if path == "orders/reporte-ventas" and metodo == "GET" and admin:
        return ORDERS_URL

    if path == "orders" and metodo in ("GET", "POST"):
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+", path)
        and metodo == "GET"
    ):
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/cancel", path)
        and metodo == "POST"
    ):
        return ORDERS_URL

    if (
        re.fullmatch(r"orders/ORD-[A-Za-z0-9-]+/status", path)
        and metodo == "PUT"
        and admin
    ):
        return ORDERS_URL

    if path == "payments" and metodo == "POST":
        return PAYMENTS_URL

    if (
        re.fullmatch(r"payments/PAY-[A-Za-z0-9-]+", path)
        and metodo == "GET"
    ):
        return PAYMENTS_URL

    return None


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
                    "Content-Type": "application/json"
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth=Depends(autenticar)
):
    try:
        async with httpx.AsyncClient(timeout=5.0) as cliente:
            respuesta = await cliente.post(
                f"{AUTH_SERVICE_URL}/logout",
                json={
                    "token": credentials.credentials
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

    secretos = await secretos_gateway()
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
        "X-Authenticated-Roles": ",".join(auth["roles"])
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
        "X-Authenticated-Roles": ",".join(auth["roles"])
    }

    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]

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