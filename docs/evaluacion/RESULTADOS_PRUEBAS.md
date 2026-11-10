# Registro de pruebas funcionales - Tokyo Noodles

Fecha de ejecucion: 2026-11-09 23:01:08

Resultado: 23/23 comprobaciones coincidentes.

| Prueba | Resultado | Detalle |
|---|---|---|
| T01 Gateway disponible | COINCIDE | HTTP 200 |
| T02 Acceso anonimo rechazado | COINCIDE | HTTP 401 |
| T03 Inventory privado | COINCIDE | HTTP 403 |
| T04 Login Ana | COINCIDE | HTTP 200 |
| T05 Login Pedro | COINCIDE | HTTP 200 |
| T06 Catalogo completo | COINCIDE | HTTP 200, productos 10 |
| T07 Consultar perfil propio | COINCIDE | HTTP 200 |
| T08 Bloquear perfil ajeno | COINCIDE | HTTP 403 |
| T09 Bloquear listado administrativo | COINCIDE | HTTP 403 |
| T10 Crear pedido | COINCIDE | HTTP 201 |
| T11 Total calculado por backend | COINCIDE | Total 27600 |
| T12 Recuperar pedido | COINCIDE | HTTP 200 |
| T13 Bloquear pedido ajeno | COINCIDE | HTTP 403 |
| T14 Crear solicitud de pago | COINCIDE | HTTP 201 |
| T15 Evitar pago duplicado | COINCIDE | HTTP 201 |
| T16 Bloquear pago ajeno | COINCIDE | HTTP 403 |
| T17 Prohibir confirmacion de pago desde cliente | COINCIDE | HTTP 403 |
| T18 Agregacion GraphQL Orders e Inventory | COINCIDE | HTTP 200 |
| T19 Bloquear GraphQL directo | COINCIDE | HTTP 403 |
| T20 Bloquear GraphQL sin token | COINCIDE | HTTP 401 |
| T21 Limitar consulta GraphQL | COINCIDE | HTTP 400 |
| T22 Cerrar sesion | COINCIDE | HTTP 200 |
| T23 Revocar token | COINCIDE | HTTP 401 |

## Alcance

Pruebas funcionales de autenticacion, autorizacion,
catalogo, clientes, pedidos, pagos y agregacion GraphQL.

Se requiere MongoDB, Vault y los servicios locales activos.

Estas pruebas no representan pagos bancarios reales,
pruebas de carga ni integracion con el frontend.
