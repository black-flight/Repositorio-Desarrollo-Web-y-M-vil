"""Pruebas de integración de Evaluación 3. No registra contraseñas ni tokens."""
from __future__ import annotations

import getpass
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

API_BASE = os.getenv("TOKYO_API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "docs" / "evaluacion" / "evidencias"


def operacion_id() -> str:
    return str(uuid.uuid4())


def ejecutar() -> int:
    usuario = input("Usuario de prueba [ana]: ").strip() or "ana"
    clave = getpass.getpass("Contraseña de prueba: ")
    resultados = []
    token = None
    pedido = None
    pago = None
    codigo_compra = str(uuid.uuid4())
    cliente = httpx.Client(timeout=12.0)

    def registrar(test_id, descripcion, estado, detalle="", response=None):
        resultados.append({
            "id": test_id,
            "descripcion": descripcion,
            "estado": estado,
            "detalle": detalle,
            "operacion_id": response.headers.get("X-Operacion") if response else None,
            "http_status": response.status_code if response else None
        })
        print(f"[{estado}] {test_id} - {descripcion}" + (f": {detalle}" if detalle else ""))

    def llamada(method, path, *, auth=True, **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["X-Operacion"] = operacion_id()
        if auth and token:
            headers["Authorization"] = f"Bearer {token}"
        return cliente.request(method, API_BASE + path, headers=headers, **kwargs)

    try:
        # P01: catálogo público por Gateway -> Vault -> Inventory.
        try:
            r = llamada("GET", "/public/products", auth=False)
            data = r.json()
            count = len(data.get("products", [])) if isinstance(data, dict) else 0
            ok = r.status_code == 200 and count >= 1
            registrar("P01", "Catálogo público servido por Inventory a través del Gateway",
                      "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; productos={count}", r)
        except Exception as exc:
            registrar("P01", "Catálogo público servido por Inventory a través del Gateway", "FALLIDA", str(exc))

        # P02: rechazo de ruta protegida sin token.
        try:
            r = llamada("GET", "/products", auth=False)
            ok = r.status_code == 401
            registrar("P02", "Ruta protegida rechaza una sesión ausente",
                      "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; esperado 401", r)
        except Exception as exc:
            registrar("P02", "Ruta protegida rechaza una sesión ausente", "FALLIDA", str(exc))

        # P03: login.
        try:
            r = llamada("POST", "/auth/login", auth=False,
                        json={"username": usuario, "password": clave})
            data = r.json()
            token = data.get("access_token")
            ok = r.status_code == 200 and bool(token)
            registrar("P03", "Inicio de sesión a través del API Gateway y Auth Service",
                      "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}", r)
        except Exception as exc:
            registrar("P03", "Inicio de sesión a través del API Gateway y Auth Service", "FALLIDA", str(exc))

        # P04: identidad validada por introspección.
        if token:
            try:
                r = llamada("GET", "/auth/me")
                identidad = r.json()
                ok = r.status_code == 200 and identidad.get("username") == usuario
                registrar("P04", "Identidad y roles devueltos por Auth Service",
                          "APROBADA" if ok else "FALLIDA",
                          f"HTTP {r.status_code}; user_id={identidad.get('user_id')}", r)
            except Exception as exc:
                registrar("P04", "Identidad y roles devueltos por Auth Service", "FALLIDA", str(exc))
        else:
            registrar("P04", "Identidad y roles devueltos por Auth Service", "BLOQUEADA", "No hubo token.")

        # P05: catálogo protegido.
        if token:
            try:
                r = llamada("GET", "/products")
                data = r.json()
                count = len(data.get("products", [])) if isinstance(data, dict) else 0
                ok = r.status_code == 200 and count >= 1
                registrar("P05", "Lectura autenticada del catálogo",
                          "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; productos={count}", r)
            except Exception as exc:
                registrar("P05", "Lectura autenticada del catálogo", "FALLIDA", str(exc))
        else:
            registrar("P05", "Lectura autenticada del catálogo", "BLOQUEADA", "No hubo token.")

        # P06: el rol user no puede administrar productos.
        if token:
            try:
                r = llamada("POST", "/products", json={})
                ok = r.status_code == 403
                registrar("P06", "Rol user no puede crear productos administrativos",
                          "APROBADA" if ok else "FALLIDA",
                          f"HTTP {r.status_code}; esperado 403", r)
            except Exception as exc:
                registrar("P06", "Rol user no puede crear productos administrativos", "FALLIDA", str(exc))
        else:
            registrar("P06", "Rol user no puede crear productos administrativos", "BLOQUEADA", "No hubo token.")

        # P07: pedido persistente; requiere perfil Clients activo del usuario.
        if token:
            try:
                r = llamada("POST", "/orders",
                            json={"codigo_compra":codigo_compra, "modalidad": "retiro", "items": [{"product_id": "1", "quantity": 1}]})
                pedido = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                ok = r.status_code == 201 and bool(pedido.get("id"))
                registrar("P07", "Creación de pedido desde el contrato Orders",
                          "APROBADA" if ok else "FALLIDA",
                          f"HTTP {r.status_code}; order_id={pedido.get('id', 'no generado')}", r)
            except Exception as exc:
                registrar("P07", "Creación de pedido desde el contrato Orders", "FALLIDA", str(exc))
        else:
            registrar("P07", "Creación de pedido desde el contrato Orders", "BLOQUEADA", "No hubo token.")

        # P08: el mismo codigo_compra no duplica el pedido.
        if token and pedido and pedido.get("id"):
            try:
                r = llamada("POST", "/orders",
                            json={"codigo_compra":codigo_compra, "modalidad": "retiro", "items": [{"product_id": "1", "quantity": 1}]})
                segundo = r.json()
                ok = r.status_code == 200 and segundo.get("id") == pedido.get("id")
                registrar("P08", "Reintento de creación idempotente sin duplicar pedido",
                          "APROBADA" if ok else "FALLIDA",
                          f"HTTP {r.status_code}; mismo order_id={segundo.get('id') == pedido.get('id')}", r)
            except Exception as exc:
                registrar("P08", "Reintento de creación idempotente sin duplicar pedido", "FALLIDA", str(exc))
        else:
            registrar("P08", "Reintento de creación idempotente sin duplicar pedido", "BLOQUEADA", "No se creó pedido.")

        # P09: lectura posterior e independiente para corroborar persistencia.
        if token and pedido and pedido.get("id"):
            try:
                r = llamada("GET", f"/orders/{pedido['id']}")
                data = r.json()
                ok = r.status_code == 200 and data.get("id") == pedido["id"]
                registrar("P09", "Persistencia del pedido comprobada con una lectura posterior",
                          "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; estado={data.get('estado')}", r)
            except Exception as exc:
                registrar("P09", "Persistencia del pedido comprobada con una lectura posterior", "FALLIDA", str(exc))
        else:
            registrar("P09", "Persistencia del pedido comprobada con una lectura posterior", "BLOQUEADA", "No se creó pedido.")

        # P10/P11: solicitud de pago y repetición idempotente.
        if token and pedido and pedido.get("id"):
            try:
                r = llamada("POST", "/payments", json={"order_id": pedido["id"]})
                pago = r.json()
                ok = r.status_code in (200, 201) and bool(pago.get("id"))
                registrar("P10", "Creación de solicitud de pago asociada al pedido",
                          "APROBADA" if ok else "FALLIDA",
                          f"HTTP {r.status_code}; payment_id={pago.get('id', 'no generado')}", r)
            except Exception as exc:
                registrar("P10", "Creación de solicitud de pago asociada al pedido", "FALLIDA", str(exc))

            if pago and pago.get("id"):
                try:
                    r = llamada("POST", "/payments", json={"order_id": pedido["id"]})
                    segundo = r.json()
                    ok = r.status_code in (200, 201) and segundo.get("id") == pago.get("id")
                    registrar("P11", "Reintento de pago idempotente para el mismo pedido",
                              "APROBADA" if ok else "FALLIDA",
                              f"HTTP {r.status_code}; mismo payment_id={segundo.get('id') == pago.get('id')}", r)
                except Exception as exc:
                    registrar("P11", "Reintento de pago idempotente para el mismo pedido", "FALLIDA", str(exc))
            else:
                registrar("P11", "Reintento de pago idempotente para el mismo pedido", "BLOQUEADA", "No se creó pago.")
        else:
            registrar("P10", "Creación de solicitud de pago asociada al pedido", "BLOQUEADA", "No se creó pedido.")
            registrar("P11", "Reintento de pago idempotente para el mismo pedido", "BLOQUEADA", "No se creó pedido.")

        # P12: GraphQL agrega Orders e Inventory.
        if token and pedido and pedido.get("id"):
            try:
                query = """query Resumen($id: ID!) {
                  resumenPedido(id: $id) { id estado total modalidad
                    items { productId nombre cantidad precioUnitario subtotal disponibleActual }
                    advertencias }
                }"""
                r = llamada("POST", "/graphql", json={"query": query, "variables": {"id": pedido["id"]}})
                data = r.json()
                resumen = data.get("data", {}).get("resumenPedido")
                ok = r.status_code == 200 and bool(resumen) and resumen.get("id") == pedido["id"]
                registrar("P12", "Consulta GraphQL agrega Orders e Inventory",
                          "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; resumen={bool(resumen)}", r)
            except Exception as exc:
                registrar("P12", "Consulta GraphQL agrega Orders e Inventory", "FALLIDA", str(exc))
        else:
            registrar("P12", "Consulta GraphQL agrega Orders e Inventory", "BLOQUEADA", "No se creó pedido.")

        # P13/P14: logout y revocación.
        if token:
            token_anterior = token
            try:
                r = llamada("POST", "/auth/logout", json={})
                ok_logout = r.status_code == 200
                registrar("P13", "Cierre de sesión", "APROBADA" if ok_logout else "FALLIDA", f"HTTP {r.status_code}", r)
            except Exception as exc:
                ok_logout = False
                registrar("P13", "Cierre de sesión", "FALLIDA", str(exc))
            try:
                r = cliente.get(API_BASE + "/auth/me", headers={
                    "Authorization": f"Bearer {token_anterior}", "X-Operacion": operacion_id()
                })
                ok = ok_logout and r.status_code == 401
                registrar("P14", "Token revocado rechazado en una solicitud posterior",
                          "APROBADA" if ok else "FALLIDA", f"HTTP {r.status_code}; esperado 401", r)
            except Exception as exc:
                registrar("P14", "Token revocado rechazado en una solicitud posterior", "FALLIDA", str(exc))
        else:
            registrar("P13", "Cierre de sesión", "BLOQUEADA", "No hubo token.")
            registrar("P14", "Token revocado rechazado en una solicitud posterior", "BLOQUEADA", "No hubo token.")
    finally:
        cliente.close()
        clave = ""

    aprobadas = sum(x["estado"] == "APROBADA" for x in resultados)
    fallidas = sum(x["estado"] == "FALLIDA" for x in resultados)
    bloqueadas = sum(x["estado"] == "BLOQUEADA" for x in resultados)
    informe = {
        "proyecto": "Tokyo Noodles",
        "evaluacion": "Unidad 3 - Integración frontend-backend",
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "api_base": API_BASE,
        "usuario_prueba": usuario,
        "pedido_id": pedido.get("id") if pedido else None,
        "pago_id": pago.get("id") if pago else None,
        "resumen": {"total": len(resultados), "aprobadas": aprobadas,
                    "fallidas": fallidas, "bloqueadas": bloqueadas},
        "resultados": resultados,
        "nota": "Ejecuciones HTTP reales; no sustituyen la validación visual del navegador ni la prueba en viewport móvil."
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    archivo = EVIDENCE_DIR / ("run_e3_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    archivo.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRESUMEN E3: {aprobadas} aprobadas | {fallidas} fallidas | {bloqueadas} bloqueadas")
    print(f"Reporte sin credenciales: {archivo.relative_to(ROOT)}")
    return 0 if fallidas == 0 and bloqueadas == 0 else 1


if __name__ == "__main__":
    sys.exit(ejecutar())
