from fastapi import FastAPI

app = FastAPI(title="Backend API Productos")


@app.get("/products")
def products():
    return {
        "products": [
            {
                "id": 1,
                "name": "Ramen",
                "available": True
            },
            {
                "id": 2,
                "name": "Gyozas",
                "available": True
            }
        ]
    }