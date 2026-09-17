from fastapi import FastAPI

app = FastAPI(title="Backend API Pedidos")


@app.get("/orders")
def orders():
    return {
        "orders": [
            {
                "id": 1001,
                "status": "preparando"
            },
            {
                "id": 1002,
                "status": "pendiente"
            }
        ]
    }