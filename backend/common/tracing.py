"""Correlación mínima de solicitudes HTTP sin herramientas externas."""
import logging
import re
import uuid
from fastapi import FastAPI, Request

logger = logging.getLogger("tokyo_noodles")
PATRON = re.compile(r"[A-Za-z0-9._:-]{8,80}\Z")

def instalar_trazabilidad(app: FastAPI, servicio: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    @app.middleware("http")
    async def registrar_solicitud(request: Request, call_next):
        # Solo Gateway decide el ID del navegador: evita falsificación de correlaciones.
        recibido = request.headers.get("X-Operacion", "") if servicio != "api-gateway" else ""
        operacion_id = recibido if PATRON.fullmatch(recibido) else str(uuid.uuid4())
        request.state.operacion_id = operacion_id
        response = await call_next(request)
        response.headers["X-Operacion"] = operacion_id
        logger.info("operacion_id=%s service=%s method=%s path=%s status=%s",
                    operacion_id, servicio, request.method, request.url.path, response.status_code)
        return response
