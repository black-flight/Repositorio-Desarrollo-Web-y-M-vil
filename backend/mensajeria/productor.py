import json
import stomp

conexion = stomp.Connection([
    ("localhost", 61613)
])

conexion.connect(
    "admin",
    "admin",
    wait=True
)

pedido = {
    "id": 1001,
    "cliente": "Ana",
    "producto": "Shio Ramen",
    "cantidad": 1,
    "total": 13800
}

mensaje = json.dumps(pedido)

conexion.send(
    destination="/queue/pedidos",
    body=mensaje
)

print("Pedido enviado")
print(mensaje)

conexion.disconnect()