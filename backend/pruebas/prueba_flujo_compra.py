import getpass
import os
from datetime import datetime
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
PAYMENTS = "http://127.0.0.1:9005"
resultados = []


def comprobar(numero, nombre, condicion, codigo):
    estado = "COINCIDE" if condicion else "NO COINCIDE"
    resultados.append((f"T{numero}", nombre, estado, f"HTTP {codigo}"))
    print(f"T{numero} {nombre}: {estado} (HTTP {codigo})")


def solicitar(cliente, metodo, ruta, token=None, datos=None, destino=BASE, extra=None):
    cabeceras = dict(extra or {})
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    return cliente.request(
        metodo, destino + ruta, headers=cabeceras, json=datos
    )


def contenido(respuesta):
    try:
        return respuesta.json()
    except ValueError:
        return {}


def iniciar_sesion(cliente, usuario):
    clave = getpass.getpass(f"Contraseña de {usuario}: ")
    respuesta = solicitar(
        cliente, "POST", "/api/auth/login",
        datos={"username": usuario, "password": clave}
    )
    clave = None

    token = contenido(respuesta).get("access_token")
    if respuesta.status_code != 200 or not token:
        raise RuntimeError(
            f"Login de {usuario} no disponible: HTTP {respuesta.status_code}"
        )
    return token


def nuevo_pedido(cliente, token):
    return solicitar(cliente, "POST", "/api/orders", token, {
        "modalidad": "retiro",
        "items": [{"product_id": "1", "quantity": 1}]
    })


def confirmar_prueba(cliente, pago_id, secreto=None):
    cabeceras = {"X-Payment-Test-Secret": secreto} if secreto else {}
    return solicitar(
        cliente,
        "POST",
        f"/payments/{pago_id}/test-confirm",
        destino=PAYMENTS,
        extra=cabeceras
    )


def ejecutar():
    secreto = os.environ.get("PAYMENT_TEST_SECRET")
    if not secreto:
        secreto = getpass.getpass("Secreto de prueba de Payments: ")

    if not secreto:
        raise RuntimeError("Falta la credencial de prueba de Payments")

    with httpx.Client(timeout=15.0, trust_env=False) as cliente:
        ana = iniciar_sesion(cliente, "ana")
        admin = iniciar_sesion(cliente, "ernesto")

        r = nuevo_pedido(cliente, ana)
        pedido = contenido(r)
        id_pedido = pedido.get("id")

        comprobar(
            28, "Crear pedido pendiente",
            r.status_code == 201 and bool(id_pedido),
            r.status_code
        )
        if not id_pedido:
            return

        r = solicitar(
            cliente, "POST", "/api/payments", ana,
            {"order_id": id_pedido}
        )
        pago = contenido(r)
        id_pago = pago.get("id")

        comprobar(
            29, "Iniciar pago con importe del pedido",
            r.status_code == 201
            and bool(id_pago)
            and pago.get("monto") == pedido.get("total"),
            r.status_code
        )
        if not id_pago:
            return

        r = solicitar(
            cliente, "POST", "/api/payments", ana,
            {"order_id": id_pedido}
        )
        comprobar(
            30, "Evitar solicitud duplicada",
            r.status_code == 201
            and contenido(r).get("id") == id_pago,
            r.status_code
        )

        r = confirmar_prueba(cliente, id_pago)
        comprobar(
            31, "Rechazar confirmacion sin credencial",
            r.status_code == 403,
            r.status_code
        )

        r = confirmar_prueba(cliente, id_pago, secreto)
        comprobar(
            32, "Confirmar pago con credencial tecnica",
            r.status_code == 200
            and contenido(r).get("estado") == "pagado",
            r.status_code
        )

        r = solicitar(
            cliente, "GET", f"/api/orders/{id_pedido}", ana
        )
        pedido_confirmado = contenido(r)

        comprobar(
            33, "Pedido queda pagado",
            r.status_code == 200
            and pedido_confirmado.get("estado") == "pagado"
            and pedido_confirmado.get("referencia_pago") == id_pago,
            r.status_code
        )

        r = confirmar_prueba(cliente, id_pago, secreto)
        comprobar(
            34, "Confirmacion repetida idempotente",
            r.status_code == 200
            and contenido(r).get("id") == id_pago,
            r.status_code
        )

        r = solicitar(
            cliente, "POST", "/api/payments", ana,
            {"order_id": id_pedido}
        )
        comprobar(
            35, "No crear pago nuevo sobre pedido pagado",
            r.status_code == 409,
            r.status_code
        )

        r = solicitar(
            cliente, "PUT",
            f"/api/orders/{id_pedido}/status",
            admin, {"estado": "en_preparacion"}
        )
        comprobar(
            36, "Preparacion despues del pago",
            r.status_code == 200
            and contenido(r).get("estado") == "en_preparacion",
            r.status_code
        )

        r = solicitar(
            cliente, "PUT",
            f"/api/orders/{id_pedido}/status",
            admin, {"estado": "entregado"}
        )
        comprobar(
            37, "Rechazar salto de estado",
            r.status_code == 409,
            r.status_code
        )

        r = solicitar(
            cliente, "POST",
            f"/api/orders/{id_pedido}/cancel",
            ana,
            {"motivo": "Anulacion solicitada despues de preparacion"}
        )
        comprobar(
            38, "Rechazar anulacion despues de preparar",
            r.status_code == 409,
            r.status_code
        )

        r = solicitar(
            cliente, "PUT",
            f"/api/orders/{id_pedido}/status",
            admin, {"estado": "listo"}
        )
        comprobar(
            39, "Pedido pasa a listo",
            r.status_code == 200
            and contenido(r).get("estado") == "listo",
            r.status_code
        )

        r = solicitar(
            cliente, "PUT",
            f"/api/orders/{id_pedido}/status",
            admin, {"estado": "entregado"}
        )
        comprobar(
            40, "Pedido de retiro entregado",
            r.status_code == 200
            and contenido(r).get("estado") == "entregado",
            r.status_code
        )

        r = nuevo_pedido(cliente, ana)
        otro_id = contenido(r).get("id")

        comprobar(
            41, "Crear otro pedido pendiente",
            r.status_code == 201 and bool(otro_id),
            r.status_code
        )
        if not otro_id:
            return

        r = solicitar(
            cliente, "PUT",
            f"/api/orders/{otro_id}/status",
            admin, {"estado": "en_preparacion"}
        )
        comprobar(
            42, "Impedir preparar antes de pagar",
            r.status_code == 409,
            r.status_code
        )

        r = solicitar(
            cliente, "POST",
            f"/api/orders/{otro_id}/cancel",
            ana,
            {"motivo": "Cliente cancela antes de pagar"}
        )
        comprobar(
            43, "Anular pedido pendiente con motivo",
            r.status_code == 200
            and contenido(r).get("estado") == "anulado",
            r.status_code
        )

        r = solicitar(
            cliente, "POST", "/api/payments", ana,
            {"order_id": otro_id}
        )
        comprobar(
            44, "No pagar pedido anulado",
            r.status_code == 409,
            r.status_code
        )

        r = nuevo_pedido(cliente, ana)
        tercero_id = contenido(r).get("id")

        comprobar(
            45, "Crear pedido para anulacion posterior al pago",
            r.status_code == 201 and bool(tercero_id),
            r.status_code
        )
        if not tercero_id:
            return

        r = solicitar(
            cliente, "POST", "/api/payments", ana,
            {"order_id": tercero_id}
        )
        tercero_pago = contenido(r).get("id")

        if r.status_code != 201 or not tercero_pago:
            comprobar(
                46, "Preparar pago para anulacion",
                False, r.status_code
            )
            return

        r = confirmar_prueba(cliente, tercero_pago, secreto)
        comprobar(
            46, "Confirmar pago previo a solicitud de anulacion",
            r.status_code == 200
            and contenido(r).get("estado") == "pagado",
            r.status_code
        )

        r = solicitar(
            cliente, "POST",
            f"/api/orders/{tercero_id}/cancel",
            ana,
            {"motivo": "Solicitud de anulacion de compra pagada"}
        )
        comprobar(
            47, "Registrar solicitud de anulacion pagada",
            r.status_code == 200
            and contenido(r).get("estado") == "anulacion_solicitada"
            and bool(contenido(r).get("motivo_anulacion")),
            r.status_code
        )


def guardar_informe():
    ruta = Path("docs/evaluacion/RESULTADOS_FLUJO_COMPRA.md")
    ruta.parent.mkdir(parents=True, exist_ok=True)

    coincidentes = sum(
        resultado[2] == "COINCIDE"
        for resultado in resultados
    )

    lineas = [
        "# Comprobaciones de pedidos, pagos y anulaciones - Tokyo Noodles",
        "",
        f"Fecha local: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Resultado: {coincidentes}/{len(resultados)} comprobaciones coincidentes.",
        "",
        "| ID | Operacion | Resultado | Codigo |",
        "|---|---|---|---|"
    ]

    for fila in resultados:
        lineas.append("| " + " | ".join(fila) + " |")

    lineas.extend([
        "",
        "**Entorno:** backend local con confirmacion de pago simulada y protegida.",
        "",
        "Las pruebas crean pedidos y pagos de prueba persistentes en MongoDB.",
        "",
        "No se realizaron transacciones bancarias externas.",
        ""
    ])

    ruta.write_text(
        "\n".join(lineas),
        encoding="utf-8"
    )

    print()
    print(f"RESULTADO FINAL: {coincidentes}/{len(resultados)}")
    print(f"REPORTE: {ruta}")

    return (
        coincidentes == len(resultados)
        and len(resultados) == 20
    )


if __name__ == "__main__":
    try:
        ejecutar()
    except Exception as error:
        print(f"ERROR DE EJECUCION: {type(error).__name__}")

    correcto = guardar_informe()
    raise SystemExit(0 if correcto else 1)
