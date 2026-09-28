from fastapi import FastAPI

app = FastAPI(title="Backend API Productos")


@app.get("/products")
def products():
    return {
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