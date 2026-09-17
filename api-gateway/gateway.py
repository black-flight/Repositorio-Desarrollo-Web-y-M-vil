from fastapi import FastAPI
import httpx

app = FastAPI(title="API Gateway Tokyo Noodles")

PRODUCTOS_URL = "http://127.0.0.1:9001"
PEDIDOS_URL = "http://127.0.0.1:9002"


@app.get("/api/products")
async def products():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PRODUCTOS_URL}/products"
        )

    return response.json()


@app.get("/api/orders")
async def orders():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PEDIDOS_URL}/orders"
        )

    return response.json()