from fastapi import FastAPI

app = FastAPI()

productos = [
    {
        "id": 1,
        "nombre": "Ramen",
        "disponible": True
    },
    {
        "id": 2,
        "nombre": "Gyozas",
        "disponible": True
    }
]


@app.get("/productos")
def obtener_productos():
    return productos