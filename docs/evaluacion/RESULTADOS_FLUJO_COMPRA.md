# Comprobaciones de pedidos, pagos y anulaciones - Tokyo Noodles

Fecha local: 2026-11-09 22:59:42
Resultado: 20/20 comprobaciones coincidentes.

| ID | Operacion | Resultado | Codigo |
|---|---|---|---|
| T28 | Crear pedido pendiente | COINCIDE | HTTP 201 |
| T29 | Iniciar pago con importe del pedido | COINCIDE | HTTP 201 |
| T30 | Evitar solicitud duplicada | COINCIDE | HTTP 201 |
| T31 | Rechazar confirmacion sin credencial | COINCIDE | HTTP 403 |
| T32 | Confirmar pago con credencial tecnica | COINCIDE | HTTP 200 |
| T33 | Pedido queda pagado | COINCIDE | HTTP 200 |
| T34 | Confirmacion repetida idempotente | COINCIDE | HTTP 200 |
| T35 | No crear pago nuevo sobre pedido pagado | COINCIDE | HTTP 409 |
| T36 | Preparacion despues del pago | COINCIDE | HTTP 200 |
| T37 | Rechazar salto de estado | COINCIDE | HTTP 409 |
| T38 | Rechazar anulacion despues de preparar | COINCIDE | HTTP 409 |
| T39 | Pedido pasa a listo | COINCIDE | HTTP 200 |
| T40 | Pedido de retiro entregado | COINCIDE | HTTP 200 |
| T41 | Crear otro pedido pendiente | COINCIDE | HTTP 201 |
| T42 | Impedir preparar antes de pagar | COINCIDE | HTTP 409 |
| T43 | Anular pedido pendiente con motivo | COINCIDE | HTTP 200 |
| T44 | No pagar pedido anulado | COINCIDE | HTTP 409 |
| T45 | Crear pedido para anulacion posterior al pago | COINCIDE | HTTP 201 |
| T46 | Confirmar pago previo a solicitud de anulacion | COINCIDE | HTTP 200 |
| T47 | Registrar solicitud de anulacion pagada | COINCIDE | HTTP 200 |

**Entorno:** backend local con confirmacion de pago simulada y protegida.

Las pruebas crean pedidos y pagos de prueba persistentes en MongoDB.

No se realizaron transacciones bancarias externas.
