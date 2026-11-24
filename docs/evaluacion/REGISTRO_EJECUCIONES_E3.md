
# Registro de ejecuciones — Evaluación 3

**Proyecto:** Tokyo Noodles
**Fecha:** 23 de noviembre de 2026
**Entorno:** Windows, Docker Compose, Python 3.14.3 y navegador Brave.
**Versión:** copia local de TokyoNoodles-Evaluacion3 con correcciones de Compose y frontend. Commit definitivo pendiente de registrar.

## 1. Ejecuciones realizadas

| RUN | Flujo o prueba | Evidencia | Resultado |
|---|---|---|---|
| RUN01 | Preflight de conectividad | preflight_20261123_192856.json | 5/5 aprobadas |
| RUN02 | Suite ampliada E3 | run_ampliada_20261123_203010.json | 24 aprobadas, 0 fallidas, 0 bloqueadas |
| RUN03 | Compra manual, pago DEMO y persistencia | persistencia_pago_ORD-510247AA3E16.txt | Pedido y pago pagados; 1 evento consumido |

Los reportes originales se encuentran en `docs/evaluacion/evidencias/`.

## 2. Recorrido manual RUN03

- Cuenta: cliente ficticio autenticado.
- Producto: Shio Ramen.
- Cantidad: 1.
- Modalidad: retiro.
- Total calculado por Orders: $13.800.
- Pedido: ORD-510247AA3E16.
- Pago: PAY-FE104807841F.
- Estado inicial: pendiente_pago.
- Confirmación: realizada mediante cuenta con rol admin.
- Estado final: pagado.
- MongoDB: pedido y pago persistidos.
- Colección events_consumed: 1 registro observado.

El campo `event_status` permaneció como `enviado_sin_confirmacion_de_consumo`. La recepción se comprobó mediante la lectura independiente de MongoDB, no por acuse confirmado del publicador.

Las capturas del navegador apoyan la observación manual, pero deben incorporarse como archivos de evidencia antes de declarar cerrado su paquete visual.

## 3. Pruebas de rechazo y límite

La suite RUN02 incluye, entre otras, las siguientes comprobaciones:

- Acceso sin sesión rechazado: HTTP 401.
- Cliente sin permiso administrativo: HTTP 403.
- Contenido distinto con el mismo código de compra: HTTP 409.
- Reintento de compra con el mismo contenido: mismo pedido.
- Compra concurrente: un solo documento persistente.
- Pedido fuera del radio de entrega: HTTP 422.
- Pedido dentro del radio permitido: HTTP 201.
- Confirmación de pago reservada al rol autorizado.
- Logout y revocación de sesión.
- Consulta GraphQL de Orders e Inventory.

Los códigos esperados y observados, identificadores y resultados individuales se conservan en el reporte JSON.

## 4. Consolidado observado

| Conjunto | Aprobadas | Fallidas | Bloqueadas |
|---|---:|---:|---:|
| Preflight | 5 | 0 | 0 |
| Suite ampliada | 24 | 0 | 0 |

El 100% de aprobación corresponde únicamente a los conjuntos ejecutados y registrados. Las pruebas de ambos conjuntos no se consideran automáticamente una sola lista de casos distintos.

La repetición manual independiente de todos los recorridos críticos, la verificación móvil con dimensiones registradas y el video todavía deben documentarse por separado.

## 5. Incidencias

| ID | Problema | Acción | Estado |
|---|---|---|---|
| INC01 | vault-init terminaba con error de sintaxis de shell | Corrección de command y VAULT_TOKEN en Compose | Corregida y comprobada |
| INC02 | Auth/Gateway no encontraban el paquete backend | Configuración PYTHONPATH=/app | Corregida y comprobada |
| INC03 | Error HTTP 422 representado como [object Object] | Se verificó registro correcto posterior; presentación del error sin nueva corrección comprobada | Abierta |
| INC04 | Código de correo DEMO sin entrega externa | Se comprobó una verificación HTTP 200 y se documentó la limitación | Limitación declarada |

No se borran resultados fallidos ni se atribuyen pruebas de una versión anterior a esta ejecución.

## 6. Evidencias pendientes de incorporar

- Captura de Network con X-Operacion.
- Logs correlacionados de Gateway, Auth y Orders.
- Captura o registro de persistencia asociado al video.
- Prueba móvil emulada, indicando dimensiones.
- Ubicación final del video.
- Hash del commit final publicado en GitHub.

La matriz de trazabilidad y los protocolos de prueba se encuentran en esta misma carpeta.