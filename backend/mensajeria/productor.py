"""Productor STOMP directo PR10. Publica un pedido real confirmado.
La aceptación local de send() NO garantiza entrega broker-consumidor; se conserva opción de reintento.
"""
import json
import logging
import os
import stomp

logger = logging.getLogger("tokyo_noodles.stomp")

def publicar_pedido_pagado(pedido: dict, operacion_id: str) -> None:
    if pedido.get("estado") not in {"pagado", "en_preparacion", "listo", "en_reparto", "entregado"}:
        raise ValueError("No se puede preparar un pedido sin pago confirmado")
    evento = {
        "event_id": "ORDER_PAID:" + pedido["id"],
        "event_type": "order.paid",
        "order_id": pedido["id"],
        "total_clp": pedido["total"],
        "modalidad": pedido["modalidad"],
        "paid_reference": pedido["referencia_pago"],
        "operacion_id": operacion_id,
    }
    conexion = stomp.Connection12([(os.getenv("ACTIVEMQ_HOST", "127.0.0.1"),
                                     int(os.getenv("ACTIVEMQ_PORT", "61613")))], timeout=2)
    try:
        conexion.connect(os.getenv("ACTIVEMQ_USER", "admin"),
                         os.getenv("ACTIVEMQ_PASSWORD", "admin"), wait=True)
        conexion.send("/queue/tokyo.orders", json.dumps(evento),
                     headers={"persistent": "true", "content-type": "application/json"})
        logger.info("operacion_id=%s event_id=%s stomp=send_called", operacion_id, evento["event_id"])
    finally:
        try:
            if conexion.is_connected():conexion.disconnect()
        except Exception:pass

def main():
    raise SystemExit("El productor ahora se invoca directamente al confirmar pago o reintentar desde Orders")

if __name__ == "__main__": main()
