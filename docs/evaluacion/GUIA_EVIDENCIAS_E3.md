# Guía de evidencias E3 — versión simplificada

## Nomenclatura

E01: F12 Network (sin Authorization ni cookies). E02: Gateway logs Vault + enrutamiento. E03: Auth introspección/rol. E04: Orders `secret_check=ok` y acción de persistencia. E05: lectura Mongo real del mismo pedido. E06: repetición/conflicto/concurrencia. E07: GraphQL agregación y fallo. E08: Events consumer (registrado Mongo). E09: frontend desktop 1366x768 (ejemplo, registrar dimensiones reales). E10: frontend móvil emulado 390x844 (ejemplo). E11: registro y verificación por código, modo demo vs HTTP. E12: comprobante y reporte.

## Cómo recolectar

1. Registrar código de versión, responsable, navegador y viewport antes de accionar.
2. Crear un pedido de prueba desde frontend, anotar `X-Operacion` de la respuesta y `ORD-...`.
3. `docker compose logs --since=10m gateway auth orders clients inventory payments events-consumer | Select-String "operacion_id=ID"` (PowerShell).
4. `docker compose exec orders python -m backend.pruebas.verificar_persistencia_e3 --pedido ORD-XXX` para comparar escritura/lectura, pagos/eventos Mongo reales.
5. Repetir con mismo `codigo_compra` y distinta carga; registrar HTTP, identificador y resultado de Mongo. Registrar al menos 2 RUN independientes.
6. Los fallos NO se eliminan. Cambios generan una versión nueva y RUN separado; no unir capturas de versiones diferentes.
7. Registrar la diferencia entre HTTP API aceptado y entrega externa efectiva; la demo solo deja documentos en Mongo.

**Criterio de credibilidad:** captura aislada != persistencia. Un HTTP 200 != ejecución de regla de negocio sin corroboración. El estado `enviado_sin_confirmacion_de_consumo` no prueba recepción STOMP; mostrar `events_consumed`. Nunca publicar contraseñas, valores de tokens, claves internas, cookies o datos personales reales.
