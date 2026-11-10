import getpass
import sys
from datetime import datetime
from pathlib import Path

import httpx

GATEWAY = "http://127.0.0.1:8000"
INVENTORY = "http://127.0.0.1:9001"
GRAPHQL = "http://127.0.0.1:8090"

resultados = []


def solicitar(metodo, ruta, token=None, datos=None, servidor=GATEWAY):
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        respuesta = httpx.request(
            metodo,
            servidor + ruta,
            headers=headers,
            json=datos,
            timeout=10,
            trust_env=False
        )

        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = {}

        return respuesta.status_code, contenido

    except httpx.RequestError:
        return 0, {}


def comprobar(nombre, condicion, detalle):
    estado = "COINCIDE" if condicion else "NO COINCIDE"
    resultados.append((nombre, estado, detalle))
    print(f"{nombre}: {estado} ({detalle})")


def generar_informe():
    raiz = Path(__file__).resolve().parents[2]
    carpeta = raiz / "docs" / "evaluacion"
    carpeta.mkdir(parents=True, exist_ok=True)

    archivo = carpeta / "RESULTADOS_PRUEBAS.md"

    aprobadas = sum(
        1 for _, estado, _ in resultados
        if estado == "COINCIDE"
    )

    lineas = [
        "# Registro de pruebas funcionales - Tokyo Noodles",
        "",
        f"Fecha de ejecucion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Resultado: {aprobadas}/{len(resultados)} comprobaciones coincidentes.",
        "",
        "| Prueba | Resultado | Detalle |",
        "|---|---|---|"
    ]

    for nombre, estado, detalle in resultados:
        lineas.append(f"| {nombre} | {estado} | {detalle} |")

    lineas.extend([
        "",
        "## Alcance",
        "",
        "Pruebas funcionales de autenticacion, autorizacion,",
        "catalogo, clientes, pedidos, pagos y agregacion GraphQL.",
        "",
        "Se requiere MongoDB, Vault y los servicios locales activos.",
        "",
        "Estas pruebas no representan pagos bancarios reales,",
        "pruebas de carga ni integracion con el frontend."
    ])

    archivo.write_text(
        "\n".join(lineas) + "\n",
        encoding="utf-8"
    )

    print()
    print(f"RESULTADO FINAL: {aprobadas}/{len(resultados)}")
    print(f"INFORME: {archivo}")

    return aprobadas == len(resultados)


def main():
    codigo, datos = solicitar("GET", "/health")

    comprobar(
        "T01 Gateway disponible",
        codigo == 200 and datos.get("status") == "OK",
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar("GET", "/api/products")

    comprobar(
        "T02 Acceso anonimo rechazado",
        codigo == 401,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        "/products",
        servidor=INVENTORY
    )

    comprobar(
        "T03 Inventory privado",
        codigo == 403,
        f"HTTP {codigo}"
    )

    print()
    print("AUTENTICACION DE USUARIOS DE PRUEBA")

    clave_ana = getpass.getpass("Contrasena de Ana: ")

    codigo, login_ana = solicitar(
        "POST",
        "/api/auth/login",
        datos={
            "username": "ana",
            "password": clave_ana
        }
    )

    clave_ana = None

    token_ana = login_ana.get("access_token")

    comprobar(
        "T04 Login Ana",
        codigo == 200 and bool(token_ana),
        f"HTTP {codigo}"
    )

    clave_pedro = getpass.getpass("Contrasena de Pedro: ")

    codigo, login_pedro = solicitar(
        "POST",
        "/api/auth/login",
        datos={
            "username": "pedro",
            "password": clave_pedro
        }
    )

    clave_pedro = None

    token_pedro = login_pedro.get("access_token")

    comprobar(
        "T05 Login Pedro",
        codigo == 200 and bool(token_pedro),
        f"HTTP {codigo}"
    )

    if not token_ana or not token_pedro:
        comprobar(
            "Prerequisito de autenticacion",
            False,
            "No es posible continuar sin ambos usuarios"
        )
        return

    codigo, catalogo = solicitar(
        "GET",
        "/api/products",
        token_ana
    )

    productos = catalogo.get("products", [])

    comprobar(
        "T06 Catalogo completo",
        codigo == 200 and len(productos) == 10,
        f"HTTP {codigo}, productos {len(productos)}"
    )

    codigo, cliente = solicitar(
        "GET",
        "/api/clients/USR-001",
        token_ana
    )

    comprobar(
        "T07 Consultar perfil propio",
        codigo == 200 and cliente.get("id") == "USR-001",
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        "/api/clients/USR-001",
        token_pedro
    )

    comprobar(
        "T08 Bloquear perfil ajeno",
        codigo == 403,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        "/api/clients",
        token_ana
    )

    comprobar(
        "T09 Bloquear listado administrativo",
        codigo == 403,
        f"HTTP {codigo}"
    )

    nuevo_pedido = {
        "modalidad": "retiro",
        "items": [
            {"product_id": "1", "quantity": 2}
        ]
    }

    codigo, pedido = solicitar(
        "POST",
        "/api/orders",
        token_ana,
        nuevo_pedido
    )

    pedido_id = pedido.get("id")

    comprobar(
        "T10 Crear pedido",
        codigo == 201 and bool(pedido_id),
        f"HTTP {codigo}"
    )

    comprobar(
        "T11 Total calculado por backend",
        pedido.get("total") == 27600,
        f"Total {pedido.get('total')}"
    )

    if not pedido_id:
        comprobar(
            "Prerequisito de pedidos",
            False,
            "No fue posible crear el pedido"
        )
        return

    codigo, pedido_guardado = solicitar(
        "GET",
        f"/api/orders/{pedido_id}",
        token_ana
    )

    comprobar(
        "T12 Recuperar pedido",
        codigo == 200 and pedido_guardado.get("id") == pedido_id,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        f"/api/orders/{pedido_id}",
        token_pedro
    )

    comprobar(
        "T13 Bloquear pedido ajeno",
        codigo == 403,
        f"HTTP {codigo}"
    )

    codigo, pago = solicitar(
        "POST",
        "/api/payments",
        token_ana,
        {"order_id": pedido_id}
    )

    pago_id = pago.get("id")

    comprobar(
        "T14 Crear solicitud de pago",
        codigo == 201
        and pago.get("monto") == 27600
        and pago.get("estado") == "pendiente",
        f"HTTP {codigo}"
    )

    if not pago_id:
        comprobar(
            "Prerequisito de pagos",
            False,
            "No fue posible crear el pago"
        )
        return

    codigo, repetido = solicitar(
        "POST",
        "/api/payments",
        token_ana,
        {"order_id": pedido_id}
    )

    comprobar(
        "T15 Evitar pago duplicado",
        codigo == 201 and repetido.get("id") == pago_id,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        f"/api/payments/{pago_id}",
        token_pedro
    )

    comprobar(
        "T16 Bloquear pago ajeno",
        codigo == 403,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "POST",
        f"/api/orders/{pedido_id}/confirm-payment",
        token_ana,
        {"referencia": "PAGO-NO-AUTORIZADO"}
    )

    comprobar(
        "T17 Prohibir confirmacion de pago desde cliente",
        codigo == 403,
        f"HTTP {codigo}"
    )

    consulta_graphql = {
        "query": (
            "query Resumen($id: ID!) { "
            "resumenPedido(id: $id) { "
            "id estado total "
            "items { nombre cantidad disponibleActual } "
            "advertencias "
            "} }"
        ),
        "variables": {
            "id": pedido_id
        }
    }

    codigo, graphql = solicitar(
        "POST",
        "/api/graphql",
        token_ana,
        consulta_graphql
    )

    resumen = graphql.get("data", {}).get("resumenPedido") or {}
    items = resumen.get("items") or []

    comprobar(
        "T18 Agregacion GraphQL Orders e Inventory",
        codigo == 200
        and resumen.get("total") == 27600
        and len(items) == 1
        and items[0].get("disponibleActual") is True
        and not graphql.get("errors"),
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "POST",
        "/graphql",
        datos=consulta_graphql,
        servidor=GRAPHQL
    )

    comprobar(
        "T19 Bloquear GraphQL directo",
        codigo == 403,
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "POST",
        "/api/graphql",
        datos=consulta_graphql
    )

    comprobar(
        "T20 Bloquear GraphQL sin token",
        codigo == 401,
        f"HTTP {codigo}"
    )

    consulta_excesiva = {
        "query": "{ a { b { c { d { e { f } } } } } }"
    }

    codigo, _ = solicitar(
        "POST",
        "/api/graphql",
        token_ana,
        consulta_excesiva
    )

    comprobar(
        "T21 Limitar consulta GraphQL",
        codigo == 400,
        f"HTTP {codigo}"
    )

    codigo, salida = solicitar(
        "POST",
        "/api/auth/logout",
        token_ana
    )

    comprobar(
        "T22 Cerrar sesion",
        codigo == 200
        and salida.get("message") == "Sesion finalizada",
        f"HTTP {codigo}"
    )

    codigo, _ = solicitar(
        "GET",
        "/api/products",
        token_ana
    )

    comprobar(
        "T23 Revocar token",
        codigo == 401,
        f"HTTP {codigo}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        comprobar(
            "Error durante la ejecucion",
            False,
            type(error).__name__
        )
    finally:
        correcto = generar_informe()

    sys.exit(0 if correcto else 1)
