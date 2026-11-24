> **AVISO HISTÓRICO:** registro/protocolo previo al ZIP simplificado; no prueba ejecución de este nuevo código. Conservar datos originales y agregar nuevos RUN aparte.

# Verificación técnica del paquete de Evaluación 3

**Fecha de comprobación:** 23-11-2026
**Entorno de comprobación del paquete:** Python 3.13.5, Node.js 22.16.0, PHP 8.4.24, FastAPI 0.128.2, HTTPX 0.28.1. La versión FastAPI del contenedor de comprobación no coincide con el pin de `requirements.txt` (0.141.1); repetir las pruebas tras instalar las dependencias declaradas en el equipo de ejecución.

## Comprobaciones ejecutadas

| Comprobación | Resultado | Alcance |
|---|---|---|
| `python -m py_compile` sobre Gateway, Auth, Inventory, Clients, Orders, Payments, trazabilidad y scripts de pruebas | Aprobada | Sintaxis Python; no ejecuta dependencias externas |
| `node --check` sobre `frontend/api.js`, `frontend/integracion.js`, `frontend/productos.js`, prueba JS y GraphQL Gateway | Aprobada | Sintaxis JavaScript |
| `php -l frontend/*.php` | Aprobada | Sintaxis PHP de las cinco páginas |
| `python backend/pruebas/pruebas_gateway_basicas.py` | Aprobada | CORS preflight 200; ruta protegida sin token 401; catálogo público usa Vault/Inventory simulados; el secreto no aparece en respuesta |
| `node frontend/tests/api-client.test.js` | Aprobada | Siete solicitudes simuladas verifican login, token, catálogo, clave idempotente, pago, GraphQL y logout |
| Inicio de API Gateway con Uvicorn desde la raíz del repositorio | Aprobada | Importación del módulo compartido y arranque del servidor local |

## Pruebas no ejecutadas en este entorno

- Batería P01–P14 contra MongoDB, Vault y los microservicios reales.
- Flujo de navegador PHP/XAMPP en escritorio y móvil emulado.
- Comprobación independiente de persistencia MongoDB para el pedido y el pago.
- Dos ejecuciones end-to-end independientes y grabación de video.
- Instalación de dependencias Node mediante `npm ci`.

El contenedor de construcción no dispone de Motor/PyMongo ni de una instancia MongoDB/Vault levantada. El archivo `requirements.txt` declara las dependencias Python necesarias para ejecutar la aplicación en el equipo. Por tanto, las pruebas de sintaxis y las pruebas locales simuladas **no se presentan como validación end-to-end**.

## Conclusión

El paquete supera las verificaciones de sintaxis y las pruebas locales de Gateway/cliente JavaScript descritas arriba. La integración real con base de datos, autenticación persistente, pedidos, pagos y GraphQL debe ejecutarse siguiendo `PLAN_VALIDACION_E3.md`; sus resultados se registran en `REGISTRO_EJECUCIONES_E3.md` y en `evidencias/`.
