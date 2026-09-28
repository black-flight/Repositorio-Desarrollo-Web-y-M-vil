import os
import secrets

from fastapi import FastAPI, Header, HTTPException, Depends

app = FastAPI(title="Backend API Productos")

INTERNAL_GATEWAY_SECRET = os.getenv("INTERNAL_GATEWAY_SECRET")

if not INTERNAL_GATEWAY_SECRET:
    raise RuntimeError("INTERNAL_GATEWAY_SECRET no está configurado")


def verify_gateway(
    x_gateway_secret: str = Header(default="")
):
    valid = secrets.compare_digest(
        x_gateway_secret,
        INTERNAL_GATEWAY_SECRET
    )

    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Solicitud no autorizada desde Gateway"
        )


@app.get("/health")
def health():
    return {
        "status": "OK",
        "service": "Backend API Productos"
    }


@app.get(
    "/products",
    dependencies=[Depends(verify_gateway)]
)
def products(
    x_authenticated_client: str | None = Header(default=None)
):
    return {
        "authenticated_client": x_authenticated_client,
        "products": [
            {
                "id": 1,
                "name": "Shio Ramen",
                "price": 13800,
                "available": True
            },
            {
                "id": 2,
                "name": "Miso Ramen",
                "price": 14200,
                "available": True
            },
            {
                "id": 3,
                "name": "Tantan Ramen",
                "price": 14900,
                "available": True
            },
            {
                "id": 4,
                "name": "Veggie Miso Especial",
                "price": 15510,
                "available": True
            },
            {
                "id": 5,
                "name": "Coca Cola Zero",
                "price": 2900,
                "available": True
            },
            {
                "id": 6,
                "name": "Aka Natsu",
                "price": 7800,
                "available": True
            },
            {
                "id": 7,
                "name": "Natsu No Hikari",
                "price": 9900,
                "available": True
            },
            {
                "id": 8,
                "name": "Soukai",
                "price": 9400,
                "available": True
            }
        ]
    }