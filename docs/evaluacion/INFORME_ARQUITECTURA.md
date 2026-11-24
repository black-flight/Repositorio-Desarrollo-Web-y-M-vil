# Informe de arquitectura — versión simplificada E3

## Caso y prioridad E2

El caso 19 exige catálogo, registro, roles, pedidos, pago externo, preparación posterior a pago, delivery gratuito hasta 3 km, anulación motivada, venta y caja, boleta digital, correo validado, reportes, mantenimiento e impresión de despacho. El proyecto académico adapta el caso a Tokyo Noodles con tecnologías trabajadas en la asignatura: MongoDB/FastAPI en vez de Oracle/.NET que aparecen en los RNF del texto original. **No se afirma equivalencia con todas las exigencias del caso:** emisión tributaria, correo externo y pago real tienen dependencias no integradas.

## Componentes y autoridad de datos

| Componente | Autoridad y protocolos | Permisos |
|---|---|---|
| Frontend PHP/JS | Pantallas responsive Bootstrap; Fetch al Gateway; no contiene secretos | Visitante, user, staff, admin |
| API Gateway FastAPI | CORS, rutas permitidas, token introspectado, secreto Vault, correlación | Puerta única externa `8000` |
| Auth Service | Hash PBKDF2, sesiones token, roles, vencimiento, introspección | Solo Gateway para registro e introspección; puertos privados |
| Inventory | Productos, disponibilidad y precios oficiales en Mongo | Lectura a usuario, mutación admin |
| Clients | Perfiles, correo, desafíos por código y estado de verificación | Propietario/admin |
| Orders | Carrito confirmado, cálculo, estado, cancelación, ventas y emisión de evento | Propietario, staff y admin por ruta |
| Payments | Intento único por pedido, pago demo protegido y aviso comercial | Propietario, admin, identidad `payments` para Orders |
| GraphQL Express/Apollo | Lectura `resumenPedido` agregando Orders + Inventory | Solo Gateway; no publicar 8090 a host |
| MongoDB | Persistencia e índices únicos, deduplicación eventos | Solo red Docker privada |
| Vault KV v2 | Valores secretos para Gateway/Auth/Payments/GraphQL | Demo de desarrollo, modo dev |
| ActiveMQ STOMP | Cola `/queue/tokyo.orders` con `order.paid` | Productor Orders; consumidor deduplica |
| Correo HTTP externo | Aceptación REST opcional; bitácora ficticia si no hay proveedor | Clave API en `.env` no versionado |

### Secuencia protegida recomendada para el video

`F12 -> POST /api/orders -> Gateway (operacion_id, Vault KV, token) -> Auth introspect -> Orders (verifica secreto) -> Clients (perfil) -> Inventory (precio) -> Mongo (insert) -> Gateway -> F12 X-Operacion`. Logs idénticos `operacion_id=...` en la cadena. No mostrar secretos ni tokens. En pago: `Gateway -> Payments -> Orders (pagado) -> STOMP producer -> ActiveMQ -> consumer -> Mongo events_consumed`.

### Unicidad, concurrencia y pagos

Orders define índice compuesto único `(client_id,codigo_compra)` condicionado a presencia de `codigo_compra` en documentos nuevos. La carga útil (sin código) se firma con SHA-256, y otra carga con mismo código devuelve 409. Primer insert 201, repetición 200 con mismo pedido; concurrentes se resuelven mediante `DuplicateKeyError`. Payments tiene índice único `order_id`; el estado pagado lo confirma exclusivamente el servicio autorizado mediante secreto interno y condición de estado. Los clientes no envían importes ni estados de pago confiables.

### STOMP directo, sin sondeo de pendientes

Después de persistir `pagado`, Orders publica `order.paid` con `order_id`, `total_clp`, modalidad, referencia de pago y `operacion_id`. `event_published` es solo registro de `send()` local, **no acuse de consumidor**. Si la conexión falla, queda `event_status=fallido` y la compra permanece pagada; admin/staff puede invocar `/api/orders/{id}/publish-event` o botón de gestión. Mongo `events_consumed.event_id` único impide tratar dos veces el mismo evento entregado. Si la caída ocurre mientras el estado queda `publicando`, esa condición debe diagnosticarse manualmente; se sacrifica recuperación automática del patrón anterior.

### Comprobantes y correo

El `GET /orders/{id}/comprobante` devuelve comprobante comercial **NO tributario**. La notificación de pago genera `comprobante_compra` en Mongo (modo DEMO) o envía vía adaptador REST `httpx` con estado API aceptado/error. Para registro, Clients guarda hash de código de seis cifras y vencimiento de 15 minutos; permite cinco intentos, marca `correo_verificado=true` únicamente cuando el desafío fue enviado en modo HTTP y el código fue presentado. En DEMO se marca `correo_verificacion_demo` pero **NO** `correo_verificado`: el código retornado no demuestra que el buzón exista. El contrato genérico necesita integración y credenciales con un proveedor real para demostrar entrega.

### Delivery y validaciones

Distancia local: `delta_lat*111.2`, `delta_lon*111.2*cos(radians(lat_tienda))`, luego raíz de suma de cuadrados. Valida finitud y rango; verifica distancia **sin redondear** contra 3 km; las coordenadas deben corresponder al domicilio, no geocodifica ni mide rutas viales. Configuración actual de sucursal es ficticia.

### Secrets, límites y decisiones de aplicabilidad

`INTERNAL_GATEWAY_SECRET`, `AUTH_INTROSPECTION_SECRET`, `GRAPHQL_GATEWAY_SECRET`, `PAYMENT_TEST_SECRET` se guardan en Vault KV v2 de **desarrollo**, con env locales excluidas del repo. El pago demo solo se habilita en entorno local y para admin. `EMAIL_API_KEY` se inyecta por `.env` solo en contenedores Clients y Payments, nunca se muestra ni devuelve al navegador. En producción deben usarse Vault no-dev y control de acceso de mínimos privilegios. No gRPC ni servicio analítico independiente: no se justifica una transferencia de alto volumen o stream; el reporte de ventas lo agrega Orders con Mongo.

### UML y diagramas

`docs/uml/` conserva diagramas de dominio y políticas Gateway editables de E2; el diagrama de comunicación del despliegue actualizado está en `docs/arquitectura/ARQUITECTURA_SIMPLIFICADA.mmd` y el modelo C4 editable en `TokyoNoodles.dsl`. Verificar visualmente antes de defensa.
