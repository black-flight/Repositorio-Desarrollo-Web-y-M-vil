"""Pruebas locales del API Gateway que no requieren MongoDB ni Vault activos."""
import asyncio
import importlib.util
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VAULT_TOKEN", "token-local-solo-para-importacion")

spec = importlib.util.spec_from_file_location(
    "gateway_basico",
    ROOT / "backend" / "api-gateway" / "gateway.py"
)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


class RespuestaFalsa:
    def __init__(self, payload, status_code=200):
        import json
        self.status_code = status_code
        self._payload = payload
        self.content = json.dumps(payload).encode("utf-8")

    def json(self):
        return self._payload


class ClienteFalso:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        if "/v1/secret/data/gateway" in url:
            assert headers.get("X-Vault-Token") == os.getenv("VAULT_TOKEN")
            return RespuestaFalsa({"data": {"data": {
                "backend_shared_secret": "secreto-backend-ficticio",
                "auth_introspection_secret": "secreto-auth-ficticio"
            }}})
        if url.endswith("/products"):
            assert headers.get("X-Gateway-Secret") == "secreto-backend-ficticio"
            return RespuestaFalsa({"products": [{"id": "1", "nombre": "Shio Ramen"}]})
        raise AssertionError("Destino inesperado: " + url)


async def main():
    # Simula Vault e Inventory para comprobar que el endpoint público los usa
    # sin revelar el secreto interno en la respuesta al navegador.
    original_httpx = gateway.httpx
    gateway.httpx = SimpleNamespace(AsyncClient=lambda **kwargs: ClienteFalso(), RequestError=original_httpx.RequestError)
    transport = httpx.ASGITransport(app=gateway.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://gateway.test") as cliente:
        preflight = await cliente.options(
            "/api/public/products",
            headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type"
            }
        )
        assert preflight.status_code == 200
        assert preflight.headers.get("access-control-allow-origin") == "http://localhost"
        assert "authorization" in preflight.headers.get("access-control-allow-headers", "").lower()

        protegido = await cliente.get(
            "/api/products",
            headers={"Origin": "http://localhost"}
        )
        assert protegido.status_code == 401
        assert protegido.headers.get("access-control-allow-origin") == "http://localhost"
        assert protegido.headers.get("X-Operacion")

        publico = await cliente.get("/api/public/products", headers={"Origin": "http://localhost"})
        assert publico.status_code == 200
        assert publico.json()["products"][0]["id"] == "1"
        assert "secreto-backend-ficticio" not in publico.text

    gateway.httpx = original_httpx
    assert gateway.destino_autorizado("GET", "products", ["user"]) == gateway.INVENTORY_URL
    assert gateway.destino_autorizado("POST", "products", ["user"]) is None
    assert gateway.destino_autorizado("POST", "products", ["admin"]) == gateway.INVENTORY_URL
    print("Gateway basic tests: CORS preflight=200; protected route without token=401; public catalogue uses Vault + Inventory; route policies OK.")


if __name__ == "__main__":
    asyncio.run(main())
