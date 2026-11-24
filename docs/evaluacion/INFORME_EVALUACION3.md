
# Informe de Evaluación 3
## Integración frontend-backend y validación basada en evidencias

**Proyecto:** Tokyo Noodles
**Integrante:** Patricio Frez
**Fecha de validación:** 23 de noviembre de 2026
**Entorno:** Windows, PowerShell, Docker Compose, MongoDB y Brave.
**Versión:** implementación local corregida; commit definitivo pendiente de registrar.

## 1. Objetivo y alcance

Validar la integración de la aplicación Tokyo Noodles, desde las acciones realizadas en el frontend hasta los servicios privados y la persistencia de los datos.

Se seleccionaron tres recorridos críticos:

- F01: consulta del catálogo desde Inventory mediante el Gateway.
- F02: registro, autenticación y consulta autorizada de perfil.
- F03: creación de pedido, solicitud de pago, confirmación simulada y persistencia.

Se incorporaron escenarios de éxito, rechazo, límites y control de duplicados. Las pruebas automatizadas se complementaron con un recorrido manual desde el navegador.

## 2. Arquitectura

El frontend utiliza PHP, HTML, CSS, JavaScript y Bootstrap.

Las solicitudes pasan por un API Gateway FastAPI, que utiliza Auth Service para la identidad y Vault para secretos de integración.

Los subsistemas Inventory, Clients, Orders y Payments implementan las operaciones comerciales. MongoDB almacena los registros persistentes.

GraphQL agrega información procedente de Orders e Inventory. ActiveMQ/STOMP permite publicar eventos, que son procesados por un consumidor independiente.

Los servicios privados no se exponen directamente al navegador.

## 3. Preparación del entorno

Se utilizó Docker Desktop y Compose para iniciar los contenedores.

Durante el proceso se corrigieron dos incidencias de arranque:

- INC01: error de sintaxis del script vault-init.
- INC02: error de importación Python por ausencia de PYTHONPATH=/app.

Posteriormente, Vault finalizó su inicialización correctamente, MongoDB quedó saludable y Gateway, Auth y los servicios privados respondieron a las pruebas de integración.

## 4. Estrategia y resultados

La validación incluyó:

1. Pruebas de conectividad.
2. Registro y autenticación de usuarios ficticios.
3. Validación de roles y permisos.
4. Consulta y persistencia de perfiles.
5. Creación de pedidos y control de reintentos.
6. Rechazo de entradas inválidas.
7. Validación del radio de entrega.
8. Consulta de agregación GraphQL.
9. Confirmación administrativa de pagos simulados.
10. Consulta independiente de MongoDB.
11. Observación de consumo de evento.

### Ejecuciones registradas

| RUN | Ejecución | Resultado |
|---|---|---|
| RUN01 | Preflight | 5/5 aprobadas |
| RUN02 | Suite ampliada E3 | 24/24 aprobadas, 0 fallidas, 0 bloqueadas |
| RUN03 | Compra y pago desde frontend | Confirmados mediante consulta de MongoDB |

### Pedido utilizado en RUN03

- Pedido: ORD-510247AA3E16.
- Pago: PAY-FE104807841F.
- Producto: Shio Ramen.
- Monto: $13.800.
- Estado inicial del pedido: pendiente_pago.
- Estado final del pedido: pagado.
- Estado final del pago: pagado.
- Eventos consumidos observados: 1.

La verificación se realizó posteriormente mediante un script ejecutado dentro del contenedor de Orders, conectado con MongoDB.

Aunque se observó consumo de evento, Orders conservó el valor `enviado_sin_confirmacion_de_consumo`. Por lo tanto, no se concluye que exista confirmación transaccional de entrega.

## 5. Incidencias y correcciones

### INC01 — Inicialización de Vault

El contenedor vault-init fallaba con código 2 debido a la interpretación del script de shell.

Se modificó la definición de Compose y se configuró la autenticación mediante VAULT_TOKEN.

Resultado posterior: inicialización completada con código 0.

### INC02 — Importación de módulos Python

Auth Service y Gateway se reiniciaban debido a un error ModuleNotFoundError.

Se estableció PYTHONPATH=/app en la configuración de los servicios Python.

Resultado posterior: servicios iniciados, autenticación y pruebas HTTP funcionando.

### INC03 — Presentación de errores de validación

Durante el registro, una respuesta HTTP 422 se presentó como [object Object].

Un registro posterior devolvió HTTP 201 y fue persistido correctamente. La presentación del error 422 permanece como incidencia abierta, sin corrección validada.

### INC04 — Verificación de correo DEMO

Se registró una notificación en modo DEMO sin entrega externa.

Los logs mostraron una verificación HTTP 200 y un intento posterior HTTP 404. No se acredita recepción de correo real ni validación de existencia del buzón.

## 6. Indicadores e interpretación

La aprobación observada en RUN01 fue 5/5 = 100%.

La aprobación observada en RUN02 fue 24/24 = 100%, con cero fallos y cero bloqueos registrados.

Estos indicadores representan el resultado de las pruebas ejecutadas, no el porcentaje completo de requisitos satisfechos ni una calificación académica.

Para calcular cobertura del diseño, ejecución total del plan y logro demostrado global se requiere reconciliar la totalidad de requisitos, criterios, pruebas, ejecuciones y evidencias de las matrices. No se declara un valor sin esa conciliación.

## 7. Limitaciones

- El entorno es local y académico.
- El pago está simulado.
- El comprobante comercial no es una boleta tributaria del SII.
- El correo DEMO no representa entrega externa.
- El radio de despacho utiliza una aproximación en línea recta.
- Vault utiliza modo de desarrollo.
- La mensajería no garantiza entrega transaccional fuerte en todos los escenarios.
- El alcance de las pruebas no demuestra rendimiento ni seguridad de producción.
- La repetición independiente de todos los flujos y la validación móvil requieren evidencia adicional.

La ausencia de analítica externa y gRPC se fundamenta en la decisión de aplicabilidad documentada.

## 8. Conclusiones

En el entorno evaluado se comprobó la comunicación entre frontend, Gateway, Auth Service y microservicios privados, así como la persistencia de un pedido y un pago simulado.

Las 24 pruebas ampliadas registraron los resultados HTTP esperados, incluyendo controles de autenticación, autorización, duplicados, concurrencia, límites de entrega, GraphQL y pagos.

Las conclusiones se restringen a estas ejecuciones. No se afirma que el sistema esté preparado para producción, cumpla procesos tributarios reales o integre proveedores externos de correo y pago.

El expediente de entrega incorpora scripts reproducibles, matrices, protocolos, resultados de ejecución y documentación de incidencias. La grabación y sus capturas correlacionadas deben incorporarse a este expediente al completarse.

## 9. Reproducción y evidencias

Para reproducir la integración se debe utilizar el README principal, preparar un .env local, levantar Docker Compose, ejecutar el preflight y posteriormente la suite ampliada.

Las evidencias se almacenan en:

`docs/evaluacion/evidencias/`

El índice de ejecuciones se mantiene en:

`docs/evaluacion/REGISTRO_EJECUCIONES_E3.md`

No se incluyen credenciales reales, contraseñas, tokens ni datos personales en las evidencias publicadas.