# Plan E3 — trazabilidad y prueba desde frontend

**Versión de protocolo:** vSIMPL-1. Los criterios se definen aquí ANTES de correr Docker. Anotar cambios posteriores y repetir las pruebas afectadas.

| Requisito | Criterio de aceptación | Prueba |
|---|---|---|
| R01 catálogo | `menu.php` refleja catálogo Inventory vía Gateway; errores y vacío visibles | P01, F01 |
| R02 registro | Auth y Clients crean perfil; reversión si Clients falla | P15, P16 |
| R03 identidad | Sin token 401; rol ajeno 403, token expirado 401 | P02, P18, P19 |
| R04 pedidos | Total viene de Inventory y se persiste, propio vs ajeno | P07, P09, P23 |
| R05 duplicados | Mismo cliente+codigo+payload -> mismo ORD; diferente -> 409; concurrencia solo un doc | P08, P20-P22, P39 |
| R06 pagos | Un pago por pedido, confirmación de prueba protegida, pedido pagado | P10, P11, P24-P26, P31-P32 |
| R07 radio | ≤3 km aproximados aceptados, >3 km rechazados, coordenadas válidas | P27-P28, aislada |
| R08 correlación | Network devuelve `X-Operacion`; mismos logs Gateway/Auth/Orders/Mongo | M01 vídeo |
| R09 GraphQL | Consulta privada agrega Orders + Inventory, permisos y error controlado | P12, P29 |
| R10 mensajería | STOMP `order.paid` posterior al pago y consumidor único, falla sin perder pedido | M02 |
| R11 correo | HTTP envía según contrato o DEMO Mongo explícito, código confirmado | M03 |
| R12 comprobante y reportes | Comercial no tributario; venta por período admin | P33-P34 |
| R13 responsable | Escritorio y móvil emulado registran dimensiones | M04 |

**Flujos críticos sugeridos:** F01 catálogo (lectura), F02 pedido+pago (escritura persistente), F03 acceso propio/ajeno (autorización). Evaluar al menos éxito, rechazo/fallo y límite/recuperación por cada uno, repetir de estado controlado con RUN01 y RUN02 distintos. Inspeccionar F12, respuestas depuradas, backend, Mongo, consumidor y contrato GraphQL. No sumar capturas de RUN distintos a una única ejecución.

**Riesgo:** alto si se duplican cobros/pedidos o se filtran datos, medio en reportes y notificaciones demo; priorizar en ese orden. Muestras pequeñas, datos sintéticos, proveedor pago no conectado, navegador emulado y Vault -dev limitan conclusiones. Evidencias pendientes hasta ejecución.
