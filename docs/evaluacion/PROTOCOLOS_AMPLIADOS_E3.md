# Protocolos ampliados E3 — versión simplificada

| ID | Precondición | Procedimiento | Esperado | Evidencias necesarias |
|---|---|---|---|---|
| M01 | Docker arriba, usuario registrado y token | Crear pedido desde carrito, observar F12 `POST /api/orders` y `X-Operacion` | Gateway/Auth/Orders/Clients/Inventory/Mongo comparten ID sin valores secretos | Network depurado, logs por ID, lectura Mongo |
| M02 | Pedido de prueba pendiente, cuenta admin | Confirmar pago; ver `event_status`, cola ActiveMQ, registro de consumer; parar broker y reintentar | Evento `order.paid` solo tras pago; 1 recepción lógica por `event_id`; caída no elimina pedido | pagos+orders+eventos Mongo, logs broker y consumer |
| M03 | Cuenta con email ficticio o proveedor HTTP | Crear cuenta; solicitar/introducir código; comparar modo demo y HTTP | DEMO no marca `correo_verificado`; HTTP solo con código entrado y API aceptada marca verificado | `notifications`, perfil de cliente y evidencia email externa SOLO si real |
| M04 | Browser PC + móvil emulado | Repetir login, menú, carrito, mensajes de error en ambos | Todas las acciones operan en dos viewports declarados | Capturas con dimensiones y versión |
| M05 | Cuenta logueada | Crear dos POST simultáneos con mismo `codigo_compra`, luego payload distinto | Un solo `ORD` y HTTP 200/201, diferente 409 | RUN pruebas script, consulta única Mongo |
| M06 | Admin y usuario normal | Intentar modificar producto, ver pedido ajeno, confirmar pago demo | Acceso denegado por servidor; ningún cambio indebido | respuestas 403 + inspección Mongo |
| M07 | Compra real confirmada en modo prueba | Consultar comprobante y reporte por período | Comprobante no tributario, reporte suma ventas del período | recibo, consulta y Mongo |
| M08 | GraphQL privado | Consulta `resumenPedido` a través de Gateway, exceso de tamaño o consulta no permitida | Agregación autorizada, errores no aparentan datos completos | Network + servicio Node + Orders/Inventory |

Para cada protocolo completar antes/después: R/CA/P/RUN/E, versión/commit, fecha/hora, navegador, viewport, rol, datos ficticios, solicitud, resultado esperado, observado, estado APROBADA/FALLIDA/BLOQUEADA/NO EJECUTADA, limitaciones, responsable y restauración. En caso de fallo, abrir INC con causa (hipótesis o confirmada), commit de corrección, nueva ejecución y regresión. No inventar resultados.

**Restauración:** `docker compose down -v` solo en entorno de prueba tras respaldo de registros; recrear `.env` si se requieren credenciales nuevas y documentarlo. El pago demo no acredita proveedor real y la recepción SMTP ya no existe (se utiliza REST o bitácora ficticia).
