"""Medicion reproducible de operaciones de lectura de Tokyo Noodles."""

from __future__ import annotations

import getpass
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
CONCURRENCIA = 6
SOLICITUDES = 160
TIMEOUT_SEGUNDOS = 10.0
REPORTE = Path(__file__).resolve().parents[2] / "docs" / "evaluacion" / "REPORTE_CARGA.md"


def muestra_procesos() -> dict[int, dict]:
    """Metricas agregadas aproximadas de procesos Python/Node del equipo Windows."""
    if platform.system() != "Windows":
        return {}
    comando = (
        "$p = @(Get-Process -Name python,python3,node -ErrorAction SilentlyContinue); "
        "$p | Select-Object Id, ProcessName, CPU, WorkingSet64 | ConvertTo-Json -Compress"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", comando],
            capture_output=True, text=True, timeout=12, check=False
        )
        if resultado.returncode != 0 or not resultado.stdout.strip():
            return {}
        objetos = json.loads(resultado.stdout)
        if isinstance(objetos, dict):
            objetos = [objetos]
        return {
            int(p["Id"]): {
                "nombre": str(p.get("ProcessName", "")),
                "cpu": float(p.get("CPU") or 0),
                "ram": int(p.get("WorkingSet64") or 0),
            }
            for p in objetos if p.get("Id") is not None
        }
    except (OSError, ValueError, subprocess.TimeoutExpired, KeyError, TypeError):
        return {}


def percentil(valores: list[float], proporcion: float) -> float:
    if not valores:
        return 0.0
    ordenados = sorted(valores)
    indice = max(0, math.ceil(proporcion * len(ordenados)) - 1)
    return ordenados[indice]


def peticion(cliente: httpx.Client, escenario: dict, token: str) -> dict:
    encabezados = {"Authorization": f"Bearer {token}"}
    inicio = time.perf_counter()
    try:
        respuesta = cliente.request(
            escenario["metodo"],
            escenario["ruta"],
            headers=encabezados,
            json=escenario.get("cuerpo"),
        )
        duracion = (time.perf_counter() - inicio) * 1000
        valido = respuesta.status_code == 200
        if valido:
            try:
                contenido = respuesta.json()
                valido = escenario["comprobar"](contenido)
            except (ValueError, TypeError, KeyError, AttributeError):
                valido = False
        return {"escenario": escenario["nombre"], "ms": duracion,
                "ok": valido, "codigo": respuesta.status_code}
    except httpx.RequestError as exc:
        return {"escenario": escenario["nombre"],
                "ms": (time.perf_counter() - inicio) * 1000,
                "ok": False, "codigo": type(exc).__name__}


def ejecutar() -> int:
    print("TOKYO NOODLES - PRUEBA DE CARGA DE LECTURAS")
    print("Entorno: servicios iniciados en 127.0.0.1; no se realizan pagos.")
    usuario = input("Usuario de prueba [ana]: ").strip() or "ana"
    password = getpass.getpass("Contrasena del usuario: ")

    limites = httpx.Limits(max_connections=CONCURRENCIA + 4, max_keepalive_connections=CONCURRENCIA + 2)
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_SEGUNDOS,
                      trust_env=False, limits=limites) as cliente:
        try:
            auth = cliente.post("/api/auth/login", json={"username": usuario, "password": password})
        except httpx.RequestError:
            print("ERROR: no se puede contactar al API Gateway.")
            return 1
        finally:
            password = None
        if auth.status_code != 200:
            print(f"ERROR: autenticacion rechazada (HTTP {auth.status_code}).")
            return 1
        token = auth.json().get("access_token")
        if not token:
            print("ERROR: el inicio de sesion no devolvio un token.")
            return 1

        headers = {"Authorization": f"Bearer {token}"}
        try:
            productos = cliente.get("/api/products", headers=headers)
            pedidos = cliente.get("/api/orders", headers=headers)
        except httpx.RequestError:
            print("ERROR: no se pudieron verificar catalogo y pedidos.")
            return 1
        if productos.status_code != 200 or pedidos.status_code != 200:
            print("ERROR: el usuario debe poder consultar productos y pedidos.")
            return 1
        lista_pedidos = pedidos.json().get("orders", [])
        if not lista_pedidos:
            print("ERROR: no hay pedidos para el usuario. Ejecuta primero pruebas_evaluacion2.py.")
            return 1
        pedido_id = lista_pedidos[-1].get("id")
        if not pedido_id:
            print("ERROR: pedido sin identificador.")
            return 1

        # Las respuestas GraphQL se validan, no basta con obtener HTTP 200.
        graphql = {
            "query": "query Resumen($id: ID!) { resumenPedido(id: $id) { id total estado items { nombre cantidad disponibleActual } advertencias } }",
            "variables": {"id": pedido_id},
        }
        escenarios = [
            {"nombre": "Catalogo", "metodo": "GET", "ruta": "/api/products",
             "comprobar": lambda d: isinstance(d.get("products"), list)},
            {"nombre": "Listado de pedidos", "metodo": "GET", "ruta": "/api/orders",
             "comprobar": lambda d: isinstance(d.get("orders"), list)},
            {"nombre": "Pedido propio", "metodo": "GET", "ruta": f"/api/orders/{pedido_id}",
             "comprobar": lambda d: d.get("id") == pedido_id},
            {"nombre": "Resumen GraphQL", "metodo": "POST", "ruta": "/api/graphql",
             "cuerpo": graphql, "comprobar": lambda d: bool((d.get("data") or {}).get("resumenPedido")) and not d.get("errors")},
        ]

        print("Verificando los cuatro escenarios antes de medir...")
        for escenario in escenarios:
            chequeo = peticion(cliente, escenario, token)
            if not chequeo["ok"]:
                print(f"ERROR: {escenario['nombre']} fallo durante verificacion: {chequeo['codigo']}")
                return 1

        for indice in range(8):
            peticion(cliente, escenarios[indice % len(escenarios)], token)

        inicial = muestra_procesos()
        resultados = []
        print(f"Ejecutando {SOLICITUDES} solicitudes, concurrencia {CONCURRENCIA}...")
        inicio = time.perf_counter()
        with ThreadPoolExecutor(max_workers=CONCURRENCIA) as pool:
            futuros = [pool.submit(peticion, cliente, escenarios[i % 4], token)
                       for i in range(SOLICITUDES)]
            for futuro in as_completed(futuros):
                resultados.append(futuro.result())
        duracion = time.perf_counter() - inicio
        final = muestra_procesos()

    latencias = [r["ms"] for r in resultados]
    errores = [r for r in resultados if not r["ok"]]
    throughput = len(resultados) / duracion if duracion else 0
    detalle = defaultdict(list)
    for registro in resultados:
        detalle[registro["escenario"]].append(registro)

    cpu_delta = sum(max(0, final[pid]["cpu"] - data["cpu"])
                    for pid, data in inicial.items() if pid in final)
    cpu_pct = 100 * cpu_delta / (duracion * max(1, os.cpu_count() or 1)) if inicial and final and duracion else None
    ram_inicio = sum(p["ram"] for p in inicial.values()) / (1024 ** 2) if inicial else None
    ram_final = sum(p["ram"] for p in final.values()) / (1024 ** 2) if final else None
    suma_codigos = Counter(str(r["codigo"]) for r in resultados)

    lineas = [
        "# Reporte de rendimiento - Tokyo Noodles", "",
        f"- **Fecha y hora local:** {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"- **Entorno:** {platform.system()} {platform.release()}; Python {platform.python_version()}; {os.cpu_count()} procesadores logicos.",
        "- **Topologia:** API Gateway en `127.0.0.1:8000` y microservicios/GraphQL en loopback; MongoDB y Vault locales.",
        f"- **Concurrencia:** {CONCURRENCIA} clientes concurrentes (hilos).",
        f"- **Solicitudes medidas:** {len(resultados)}; calentamiento: 8 (excluidas).",
        "- **Carga:** consultas de catalogo, listado de pedidos, pedido propio y resumen GraphQL; proporcion 25 % cada una.",
        "- **Datos:** usuarios y pedidos ficticios persistidos previamente; solo solicitudes de lectura durante la medicion.",
        "- **Alcance:** medicion local de laboratorio, no una proyeccion certificada de trafico de produccion.",
        "", "## Indicadores medidos", "",
        "| Indicador | Resultado |", "|---|---:|",
        f"| Duracion total | {duracion:.2f} s |",
        f"| Solicitudes | {len(resultados)} |",
        f"| Concurrencia | {CONCURRENCIA} |",
        f"| Throughput | {throughput:.2f} solicitudes/s |",
        f"| Latencia media | {statistics.mean(latencias):.2f} ms |",
        f"| Latencia mediana | {statistics.median(latencias):.2f} ms |",
        f"| Latencia p95 | {percentil(latencias, .95):.2f} ms |",
        f"| Latencia maxima | {max(latencias):.2f} ms |",
        f"| Errores funcionales o HTTP | {len(errores)} ({100*len(errores)/len(resultados):.2f} %) |",
        "", "## Desglose por operacion", "",
        "| Operacion | Solicitudes | p95 (ms) | Errores |", "|---|---:|---:|---:|",
    ]
    for nombre in [e["nombre"] for e in escenarios]:
        grupo = detalle[nombre]
        lineas.append(f"| {nombre} | {len(grupo)} | {percentil([r['ms'] for r in grupo], .95):.2f} | {sum(not r['ok'] for r in grupo)} |")

    lineas.extend(["", "## Recursos del equipo de laboratorio", ""])
    if inicial and final:
        lineas.extend([
            f"- **CPU acumulada por procesos Python/Node detectados:** +{cpu_delta:.3f} segundos de CPU durante la medicion.",
            f"- **CPU aproximada sobre capacidad logica del equipo:** {cpu_pct:.2f} %.",
            f"- **Memoria agregada al inicio:** {ram_inicio:.1f} MiB.",
            f"- **Memoria agregada al final:** {ram_final:.1f} MiB.",
            "- **Metodo:** instantaneas de `Get-Process` (Python y Node.js) antes y despues.",
            "- **Limitacion de atribucion:** cifras agregadas; pueden incluir otros procesos Python/Node. Memoria instantanea, no pico.",
        ])
    else:
        lineas.append("- No fue posible obtener instantaneas de procesos; registrar medicion externa de CPU/RAM para completar esta seccion.")
    lineas.extend([
        "", "## Codigos y respuestas observados", "",
        "| Codigo o error | Cantidad |", "|---|---:|",
    ])
    for codigo, cantidad in sorted(suma_codigos.items()):
        lineas.append(f"| {codigo} | {cantidad} |")
    lineas.extend([
        "", "## Criterios operativos de referencia", "",
        "| Criterio | Umbral de laboratorio | Resultado |",
        "|---|---:|---|",
        f"| Latencia p95 | <= 1.000 ms | {'Cumple' if percentil(latencias,.95) <= 1000 else 'Revisar'} |",
        f"| Throughput | >= 8 solicitudes/s | {'Cumple' if throughput >= 8 else 'Revisar'} |",
        f"| Errores | <= 1 % | {'Cumple' if len(errores)/len(resultados) <= .01 else 'Revisar'} |",
        "", "## Interpretacion", "",
        "Los indicadores anteriores corresponden unicamente a la ejecucion registrada. No permiten inferir capacidad maxima de produccion ni comparar tecnologias sin una prueba A/B equivalente.",
        "Las decisiones de comunicacion y separacion se documentan en `docs/decisiones/ADR_001_ANALITICA_GRPC.md`.",
        "", "## Reproduccion", "",
        "Desde la raiz del repositorio y con todos los servicios encendidos:", "",
        "```powershell", "python backend/pruebas/prueba_carga.py", "```", "",
        "No se registran contrasenas ni tokens en este informe.",
    ])

    REPORTE.parent.mkdir(parents=True, exist_ok=True)
    REPORTE.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Resultado: {len(resultados)} solicitudes, {len(errores)} errores, p95 {percentil(latencias,.95):.1f} ms, {throughput:.1f} req/s")
    print(f"CPU y RAM: {'registradas' if inicial and final else 'no disponibles en este entorno'}")
    print(f"Reporte generado: {REPORTE}")
    return 0 if not errores else 2


if __name__ == "__main__":
    try:
        sys.exit(ejecutar())
    except KeyboardInterrupt:
        print("Prueba interrumpida por el operador.")
        sys.exit(130)
