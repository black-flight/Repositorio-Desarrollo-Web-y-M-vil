import json
import stomp

class Consumidor(stomp.ConnectionListener):

    def on_message(self, frame):
        pedido = json.loads(frame.body)

        print("Pedido recibido")
        print("ID:", pedido["id"])
        print("Cliente:", pedido["cliente"])
        print("Producto:", pedido["producto"])
        print("Cantidad:", pedido["cantidad"])
        print("Total:", pedido["total"])


conexion = stomp.Connection([
    ("localhost", 61613)
])

conexion.set_listener(
    "",
    Consumidor()
)

conexion.connect(
    "admin",
    "admin",
    wait=True
)

conexion.subscribe(
    destination="/queue/pedidos",
    id=1,
    ack="auto"
)

print("Esperando pedidos...")
input("Presiona Enter para finalizar")

conexion.disconnect()