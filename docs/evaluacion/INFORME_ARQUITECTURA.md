# Tokyo Noodles — Arquitectura y contratos de servicios

**Sistema:** Tokyo Noodles
**Integrante:** Patricio Frez
**Fecha de documentación:** 09 de noviembre de 2026
**Alcance:** arquitectura de microservicios, gestión de identidad, catálogo, clientes, pedidos, pagos, seguridad, persistencia y agregación GraphQL.

---

## 1. Visión general

Tokyo Noodles es una plataforma comercial organizada mediante una arquitectura de microservicios. La solución separa la interfaz web, las operaciones transaccionales, la gestión de identidad, el enrutamiento de solicitudes y la composición de información.

El backend está compuesto por cuatro microservicios de negocio: **Inventory, Clients, Orders y Payments**. Estos servicios utilizan Python, FastAPI y MongoDB para administrar sus propios datos y aplicar las reglas correspondientes.

La arquitectura incorpora además:

- **API Gateway:** punto de entrada HTTP, autenticación y enrutamiento autorizado.
- **Auth Service:** administración de usuarios, contraseñas, roles y sesiones.
- **GraphQL Gateway:** agregación de información entre Orders e Inventory.
- **MongoDB:** persistencia de productos, perfiles, pedidos, pagos, usuarios y sesiones.
- **HashiCorp Vault:** almacenamiento de secretos utilizados para las comunicaciones internas.
- **Frontend responsivo:** interfaz web desarrollada con PHP, HTML, CSS y JavaScript.

La ejecución documentada utiliza un entorno local Windows, con los servicios vinculados a `127.0.0.1`.

### 1.1. Principios de arquitectura

La organización del backend responde a los siguientes principios:

1. **Separación de responsabilidades:** cada microservicio administra un conjunto definido de operaciones y datos.
2. **Autoridad de datos:** los cambios sobre un recurso se realizan mediante el servicio que lo administra.
3. **Autenticación centralizada:** el API Gateway obtiene la identidad de usuarios mediante Auth Service.
4. **Autorización por recurso:** los servicios internos comprueban las condiciones de acceso correspondientes.
5. **Persistencia:** las operaciones de negocio se almacenan en MongoDB.
6. **Protección de secretos:** las credenciales de integración permanecen en los componentes internos.
7. **Contratos explícitos:** la comunicación entre subsistemas utiliza rutas y métodos HTTP definidos.
8. **Agregación controlada:** GraphQL combina respuestas sin modificar directamente las bases de datos de otros servicios.
9. **Reproducibilidad:** el repositorio incorpora instrucciones de ejecución y scripts de comprobación.

### 1.2. Documentación relacionada

| Archivo | Contenido |
|---|---|
| `README.md` | Instalación, configuración, ejecución y mantenimiento |
| `requirements.txt` | Versiones de dependencias Python |
| `docs/arquitectura/TokyoNoodles.dsl` | Modelo arquitectónico C4 |
| `docs/uml/UML_Dominio.drawio` | UML de clases del dominio y servicios |
| `docs/uml/UML_Gateway.drawio` | UML del API Gateway y políticas |
| `docs/decisiones/ADR_Analitica_y_Comunicacion.md` | Decisiones de arquitectura sobre comunicación y analítica |
| `docs/evaluacion/RESULTADOS_PRUEBAS.md` | Registro de comprobaciones funcionales |
| `docs/evaluacion/REPORTE_CARGA.md` | Mediciones de rendimiento |
| `backend/pruebas/pruebas_evaluacion2.py` | Script de comprobaciones HTTP |
| `backend/pruebas/prueba_carga.py` | Script de carga reproducible |

Los diagramas `.drawio` constituyen las versiones editables. Sus representaciones PNG permiten visualizar las relaciones sin utilizar el editor.

---

## 2. Contexto funcional y trazabilidad

El sistema considera operaciones relacionadas con la visualización del catálogo, promociones, selección de productos, autenticación, perfiles de clientes, administración, pedidos y solicitudes de pago.

Los identificadores de pantalla y servicio se utilizan para relacionar las interacciones comerciales con los contratos disponibles.

Una operación del backend puede utilizarse desde distintas interfaces. La existencia de un contrato HTTP no implica que todas las interfaces estén conectadas a él.

### 2.1. Matriz de trazabilidad funcional

| Referencia | Interacción o necesidad | Operación del backend | Sistema | Datos y acceso |
|---|---|---|---|---|
| P01 / S01 | Visualizar menú | `GET /api/products` | Inventory | Catálogo; usuario autenticado |
| P01 / S02 | Consultar producto | `GET /api/products/{id}` | Inventory | Producto y disponibilidad |
| P02 / S01 | Mostrar promociones del catálogo | `GET /api/products` | Inventory | Productos y categoría |
| P03 / S13 | Crear pedido desde una selección | `POST /api/orders` | Orders | Productos, cantidades y modalidad |
| P03 / S15 | Consultar pedido registrado | `GET /api/orders/{id}` | Orders | Pedido propio |
| P04 / S06 | Iniciar sesión | `POST /api/auth/login` | Auth Service | Usuario y contraseña |
| P04 / S07 | Cerrar sesión | `POST /api/auth/logout` | Auth Service | Token de sesión |
| P05 / S09 | Consultar perfil | `GET /api/clients/{id}` | Clients | Propietario o administrador |
| P05 / S10 | Registrar perfil | `POST /api/clients` | Clients | Identificación y contacto |
| P05 / S11 | Modificar perfil | `PUT /api/clients/{id}` | Clients | Propietario o administrador |
| P06 / S03 | Crear producto | `POST /api/products` | Inventory | Administrador |
| P06 / S04 | Modificar producto | `PUT /api/products/{id}` | Inventory | Administrador |
| P06 / S05 | Desactivar producto | `DELETE /api/products/{id}` | Inventory | Administrador |
| P06 / S17 | Actualizar estado de pedido | `PUT /api/orders/{id}/status` | Orders | Administrador |
| P07 / S18 | Iniciar solicitud de pago | `POST /api/payments` | Payments | Pedido propio |
| P07 / S19 | Consultar pago | `GET /api/payments/{id}` | Payments | Propietario |
| P07 / S20 | Consultar resumen agregado | `POST /api/graphql` | GraphQL Gateway | Pedido propio |

### 2.2. Clasificación de operaciones

Las operaciones se clasifican según su efecto:

- **GET:** consulta de recursos.
- **POST:** creación de recursos o ejecución de operaciones específicas.
- **PUT:** modificación de un recurso identificado.
- **DELETE:** solicitud de desactivación según las reglas del servicio.

La desactivación de productos y clientes conserva sus registros. La anulación de un pedido se ejecuta mediante una transición de estado y no mediante la eliminación de su historial.

### 2.3. Autoridad de los datos enviados

Las cantidades y los identificadores de productos forman parte de una solicitud de pedido.

Sin embargo, el precio unitario, los subtotales, el total y los estados oficiales se determinan mediante los servicios de negocio.

Orders consulta Inventory para obtener los precios y conserva una instantánea del detalle al registrar la operación.

Los datos proporcionados por un cliente HTTP no sustituyen las validaciones del backend.

---

## 3. Inventario de componentes y datos

### 3.1. Componentes principales

| Componente | Puerto local | Responsabilidad | Dependencias |
|---|---:|---|---|
| API Gateway | 8000 | Autenticación, políticas de rutas y reenvío HTTP | Auth, Vault, servicios REST y GraphQL |
| Inventory | 9001 | Catálogo, productos, precios y disponibilidad | MongoDB |
| Orders | 9002 | Creación, consulta y estados de pedidos | Inventory, Clients, MongoDB |
| Auth Service | 9003 | Usuarios, contraseñas, roles y sesiones | MongoDB |
| Clients | 9004 | Perfiles e información personal | MongoDB |
| Payments | 9005 | Solicitudes y estados de pago | Orders, MongoDB |
| GraphQL Gateway | 8090 | Agregación de información | Orders, Inventory |
| Vault | 8200 | Administración de secretos | Almacenamiento KV v2 |
| MongoDB | 27017 | Persistencia documental | Instalación local |

Los puertos indicados corresponden a la configuración local utilizada para las comprobaciones.

### 3.2. Colecciones persistentes

La base de datos utilizada por los microservicios es:

`tokyo_noodles_eval2`

| Colección | Sistema que administra los datos | Contenido |
|---|---|---|
| `products` | Inventory | Catálogo comercial |
| `clients` | Clients | Perfiles de clientes |
| `orders` | Orders | Pedidos y detalles |
| `payments` | Payments | Solicitudes y estados de pago |
| `auth_users` | Auth Service | Usuarios, roles y hashes de contraseñas |
| `auth_sessions` | Auth Service | Sesiones, hashes de tokens y expiración |

La separación se realiza por responsabilidad del servicio. Los sistemas utilizan colecciones diferenciadas y se comunican mediante contratos HTTP para consultar información administrada por otros subsistemas.

### 3.3. Colaboración entre microservicios

1. Auth Service valida las credenciales de acceso y administra sesiones.
2. API Gateway consulta la identidad del usuario mediante introspección.
3. Inventory proporciona información comercial y precios oficiales.
4. Clients administra los datos y el estado de actividad de los clientes.
5. Orders comprueba la información necesaria antes de registrar un pedido.
6. Payments consulta Orders para obtener el importe oficial de una solicitud.
7. GraphQL Gateway combina información de Orders e Inventory.
8. Vault proporciona las credenciales utilizadas por el Gateway.

### 3.4. Gestión de fallos

Las comunicaciones HTTP internas utilizan tiempos máximos de espera.

Cuando Orders no puede obtener los datos necesarios desde Inventory o Clients, la operación no se registra como una compra confirmada.

Cuando GraphQL puede recuperar un pedido, pero no obtiene la disponibilidad del catálogo, la respuesta conserva la información transaccional y comunica la condición mediante una advertencia.

Las operaciones de pago distinguen entre iniciar una solicitud y confirmar su resultado.

---

## 4. Modelo de dominio y cardinalidades

El modelo de clases se encuentra en:

`docs/uml/UML_Dominio.drawio`

Este diagrama representa las entidades del negocio, sus atributos, multiplicidades y dependencias con los servicios.

### 4.1. Entidades del dominio

| Clase | Atributos representativos | Responsabilidad |
|---|---|---|
| Producto | `id`, `nombre`, `descripcion`, `precio`, `imagen`, `categoria`, `available` | Información comercial |
| Cliente | `id`, `run`, `nombre`, `correo`, `telefono`, `direccion`, `activo` | Perfil del cliente |
| Pedido | `id`, `client_id`, `items`, `total`, `modalidad`, `estado` | Transacción de compra |
| DetallePedido | `product_id`, `nombre`, `cantidad`, `precio_unitario`, `subtotal` | Productos incluidos en el pedido |
| Pago | `id`, `order_id`, `client_id`, `monto`, `estado` | Solicitud de pago |
| UsuarioAuth | `user_id`, `username`, `roles`, `salt`, `password_hash` | Identidad y credenciales |
| Sesion | `token_hash`, `user_id`, `username`, `roles`, `expires_at` | Sesión autenticada |

### 4.2. Relaciones

| Relación | Cardinalidad | Justificación |
|---|---|---|
| Cliente — Pedido | `1` a `0..*` | Cada pedido pertenece a un cliente y un cliente puede generar múltiples pedidos |
| Pedido — DetallePedido | `1` a `1..*` | Cada pedido registrado contiene uno o más detalles |
| Producto — DetallePedido | `1` a `0..*` | Un producto puede aparecer en distintos pedidos |
| Pedido — Pago | `1` a `0..1` | Payments mantiene unicidad de solicitud por pedido |
| Cliente — Pago | `1` a `0..*` | Un cliente puede generar solicitudes para distintos pedidos |
| UsuarioAuth — Sesion | `1` a `0..*` | Un usuario puede iniciar diferentes sesiones |

### 4.3. Composición de pedidos

La relación entre Pedido y DetallePedido representa una composición.

Los detalles forman parte del pedido registrado y contienen una instantánea de los valores comerciales utilizados al momento de su creación.

Cada detalle conserva:

- Identificador del producto.
- Nombre del producto.
- Cantidad.
- Precio unitario.
- Subtotal.

De esta manera, los cambios posteriores en el catálogo no modifican automáticamente el valor histórico de un pedido existente.

### 4.4. Servicios del dominio

El diagrama también presenta las interfaces lógicas:

- `InventoryService`
- `ClientsService`
- `OrdersService`
- `PaymentsService`
- `AuthService`

Estas interfaces describen operaciones disponibles y dependencias del dominio. No representan necesariamente clases físicas instanciadas dentro de los programas Python.

---

## 5. Contratos REST

Los contratos externos se publican mediante el API Gateway en `http://127.0.0.1:8000`.

### 5.1. Inventory — Catálogo

| Método | Ruta | Operación | Permiso |
|---|---|---|---|
| GET | `/api/products` | Consultar catálogo | Usuario autenticado |
| GET | `/api/products/{id}` | Consultar producto | Usuario autenticado |
| POST | `/api/products` | Crear producto | Administrador |
| PUT | `/api/products/{id}` | Modificar producto | Administrador |
| DELETE | `/api/products/{id}` | Desactivar producto | Administrador |

**Ejemplo de producto:**

```json
{
  "id": "1",
  "nombre": "Shio Ramen",
  "descripcion": "Caldo ligero con noodles e ingredientes de la casa",
  "precio": 13800,
  "imagen": "img/shio.png",
  "categoria": "ramen",
  "available": true
}
```

El precio es expresado como número entero en pesos chilenos.

La propiedad `available` indica la disponibilidad comercial del producto.

La operación DELETE establece el producto como no disponible, conservando el registro.

### 5.2. Clients — Gestión de perfiles

| Método | Ruta | Operación | Permiso |
|---|---|---|---|
| GET | `/api/clients` | Listar perfiles | Administrador |
| POST | `/api/clients` | Registrar perfil | Propietario del identificador o administrador |
| GET | `/api/clients/{id}` | Consultar perfil | Propietario o administrador |
| PUT | `/api/clients/{id}` | Modificar perfil | Propietario o administrador |
| DELETE | `/api/clients/{id}` | Desactivar perfil | Administrador |

**Ejemplo de solicitud de perfil con datos ficticios:**

```json
{
  "id": "USR-001",
  "run": "11111111-1",
  "nombre": "Cliente de Prueba",
  "direccion": "Calle Ejemplo 123",
  "comuna": "Providencia",
  "provincia": "Santiago",
  "region": "Metropolitana",
  "fecha_nacimiento": "2000-01-01",
  "sexo": "No especificado",
  "correo": "cliente@example.com",
  "telefono": "+56911111111"
}
```

El servicio valida la estructura de los campos, comprueba la fecha de nacimiento y verifica que el usuario tenga autorización sobre el identificador solicitado.

Los registros almacenan además indicadores de actividad y verificación de correo.

### 5.3. Orders — Gestión de pedidos

| Método | Ruta | Operación | Permiso |
|---|---|---|---|
| GET | `/api/orders` | Consultar pedidos permitidos | Usuario autenticado o administrador |
| POST | `/api/orders` | Crear pedido | Cliente autenticado |
| GET | `/api/orders/{id}` | Consultar pedido | Propietario o administrador |
| POST | `/api/orders/{id}/cancel` | Solicitar anulación | Propietario o administrador, según estado |
| PUT | `/api/orders/{id}/status` | Modificar estado | Administrador |

**Ejemplo de solicitud:**

```http
POST /api/orders HTTP/1.1
Authorization: Bearer <TOKEN_DE_SESION>
Content-Type: application/json
```

```json
{
  "modalidad": "retiro",
  "items": [
    {
      "product_id": "1",
      "quantity": 2
    }
  ]
}
```

El backend utiliza los identificadores de productos para consultar Inventory y obtener los precios oficiales.

Para el producto Shio Ramen, con un precio de 13.800 CLP, dos unidades generan un total de 27.600 CLP.

El pedido se registra inicialmente con estado `pendiente_pago`.

**Ejemplo de solicitud de anulación:**

```json
{
  "motivo": "El cliente solicita anular el pedido"
}
```

Las anulaciones se procesan mediante reglas de transición y conservan la información histórica.

### 5.4. Payments — Solicitudes de pago

| Método | Ruta | Operación | Permiso |
|---|---|---|---|
| POST | `/api/payments` | Iniciar solicitud de pago | Cliente autenticado |
| GET | `/api/payments/{id}` | Consultar pago | Propietario |

**Ejemplo de entrada:**

```json
{
  "order_id": "ORD-EJEMPLO"
}
```

`ORD-EJEMPLO` es un identificador ilustrativo. Las solicitudes reales utilizan el identificador generado por Orders.

Payments consulta el pedido para obtener el importe oficial y registra una solicitud persistente.

La colección mantiene un índice único sobre `order_id`, utilizado para evitar la creación de múltiples registros de pago para el mismo pedido.

La confirmación simulada se administra mediante una ruta técnica protegida y requiere una credencial específica.

### 5.5. Auth Service — Autenticación y sesiones

Las operaciones de autenticación publicadas por el API Gateway son:

| Método | Ruta | Operación | Acceso |
|---|---|---|---|
| POST | `/api/auth/login` | Autenticar usuario y generar sesión | Sin token previo |
| POST | `/api/auth/logout` | Revocar sesión | Usuario autenticado |

**Ejemplo de inicio de sesión:**

```json
{
  "username": "USUARIO_DE_PRUEBA",
  "password": "CLAVE_INGRESADA_EN_EJECUCION"
}
```

Los valores anteriores representan la estructura de la solicitud y no constituyen credenciales reales.

**Ejemplo de estructura de respuesta:**

```json
{
  "access_token": "TOKEN_GENERADO_POR_EL_SERVICIO",
  "token_type": "bearer",
  "expires_in": 900
}
```

El token se genera al validar correctamente las credenciales y tiene una vigencia configurada de 15 minutos.

Auth Service mantiene las sesiones en MongoDB y almacena hashes de los tokens.

El cierre de sesión permite revocar una sesión antes de su expiración.

#### 5.5.1. Registro de credenciales y perfiles de clientes

Auth Service dispone adicionalmente de una operación interna:

`POST /register`

Esta operación permite registrar credenciales de acceso y crear un usuario con su identificador y rol correspondiente.

La operación de registro de credenciales pertenece a Auth Service.

Por su parte, la creación del perfil comercial se administra mediante:

`POST /api/clients`

Ambas operaciones corresponden a contratos diferenciados:

- **Auth Service:** administra usuario, contraseña, hash, sal y roles.
- **Clients:** administra nombre, RUN, dirección, correo, teléfono y demás información del perfil.

Las operaciones publicadas actualmente por el API Gateway para autenticación son `POST /api/auth/login` y `POST /api/auth/logout`.

Esta separación mantiene los datos de autenticación bajo la responsabilidad de Auth Service y los datos personales del perfil bajo Clients.

### 5.6. Códigos de respuesta HTTP

| Código | Interpretación |
|---|---|
| 200 | Solicitud procesada |
| 201 | Recurso creado |
| 400 | Solicitud incorrecta o regla incumplida |
| 401 | Autenticación ausente o inválida |
| 403 | Operación no autorizada |
| 404 | Recurso no encontrado |
| 409 | Conflicto de estado o unicidad |
| 422 | Error de validación de campos |
| 502 | Respuesta no válida de una dependencia |
| 503 | Servicio o dependencia no disponible |

Los mensajes de error se utilizan para comunicar las condiciones de la operación sin incorporar contraseñas, tokens ni secretos de integración.

---

## 6. Stakeholders y permisos

### 6.1. Actores e identidades

| Actor o identidad | Función | Alcance |
|---|---|---|
| Visitante | Consulta de la interfaz comercial | Navegación por el frontend |
| Cliente autenticado | Consulta de productos, perfil, pedidos y pagos | Recursos propios |
| Administrador | Mantenimiento de productos y operaciones administrativas | Rutas autorizadas |
| Payments | Confirmación técnica de pagos | Integración privada |
| GraphQL Gateway | Consulta y composición de datos | Contratos privados |
| Operador técnico | Configuración y mantenimiento | Entorno de ejecución |

Los usuarios del negocio y las identidades técnicas cumplen funciones diferentes.

Una credencial de servicio no representa automáticamente un usuario administrador.

### 6.2. Matriz de autorización

| Actor | Método | Recurso | Condición |
|---|---|---|---|
| Anónimo | GET | `/api/products` | El Gateway actual exige autenticación |
| `user` | GET | `/api/products` | Sesión válida |
| `user` | POST | `/api/products` | Operación denegada |
| `admin` | POST | `/api/products` | Rol administrativo |
| `admin` | PUT / DELETE | `/api/products/{id}` | Rol administrativo |
| `user` | GET / PUT | `/api/clients/{id}` | Recurso propio |
| `user` | GET | `/api/clients` | Operación denegada |
| `admin` | GET | `/api/clients` | Rol administrativo |
| `user` | POST | `/api/orders` | Identidad y datos válidos |
| `user` | GET | `/api/orders/{id}` | Pedido propio |
| `user` | POST | `/api/orders/{id}/cancel` | Propiedad y estado permitido |
| `admin` | PUT | `/api/orders/{id}/status` | Rol y transición válida |
| `user` | POST | `/api/payments` | Pedido propio |
| `user` | GET | `/api/payments/{id}` | Pago propio |
| `payments` | POST | Confirmación interna de Orders | Identidad técnica y secreto específico |
| `user` | POST | `/api/graphql` | Identidad válida y permiso sobre el pedido |

### 6.3. Verificación de permisos

El API Gateway aplica una primera comprobación de identidad y permisos.

Los servicios internos realizan validaciones adicionales:

- Inventory comprueba los permisos administrativos para escritura.
- Clients verifica la propiedad del perfil.
- Orders comprueba la pertenencia del pedido y las transiciones de estado.
- Payments valida la relación entre usuario, pedido y solicitud.
- Auth Service comprueba la validez de las sesiones.
- GraphQL utiliza el contrato de Orders para respetar la autorización del pedido.

La autorización depende del método HTTP, el recurso solicitado, el rol y las condiciones del negocio.

---

## 7. API Gateway, rutas internas y secretos

El API Gateway centraliza la entrada HTTP hacia el backend.

Su estructura lógica se documenta en:

`docs/uml/UML_Gateway.drawio`

El modelo representa:

- `ApiGateway`
- `RouteDefinition`
- `ServiceTarget`
- `AuthenticationPolicy`
- `AuthorizationPolicy`
- `SecretProvider`
- `GraphQLGateway`
- `GraphQLSchema`
- `GraphQLResolver`

Estas clases representan responsabilidades y relaciones arquitectónicas.

### 7.1. Fronteras de confianza

**Navegador → API Gateway**

El cliente presenta un token Bearer para las rutas protegidas.

Las cabeceras internas de identidad proporcionadas directamente por el navegador no se utilizan como prueba de autenticación.

**API Gateway → Auth Service**

El Gateway introspecta la sesión utilizando una credencial de integración.

Auth Service determina la validez del token y devuelve la identidad asociada.

**API Gateway → servicios privados**

El Gateway transmite identidad verificada y credenciales internas mediante cabeceras controladas.

Cada servicio comprueba además las reglas que administra.

**API Gateway → GraphQL Gateway**

La agregación GraphQL requiere una credencial de servicio diferenciada.

**GraphQL Gateway → Orders e Inventory**

La composición utiliza consultas HTTP internas y respeta las reglas de acceso a los recursos.

**Payments → Orders**

La confirmación de pago exige una identidad técnica y una credencial específica para esa comunicación.

### 7.2. Mapa de rutas

| Ruta externa | Ruta interna | Sistema |
|---|---|---|
| `/api/auth/login` | `/login` | Auth Service |
| `/api/auth/logout` | `/logout` | Auth Service |
| `/api/products` | `/products` | Inventory |
| `/api/products/{id}` | `/products/{id}` | Inventory |
| `/api/clients` | `/clients` | Clients |
| `/api/clients/{id}` | `/clients/{id}` | Clients |
| `/api/orders` | `/orders` | Orders |
| `/api/orders/{id}` | `/orders/{id}` | Orders |
| `/api/orders/{id}/cancel` | `/orders/{id}/cancel` | Orders |
| `/api/orders/{id}/status` | `/orders/{id}/status` | Orders |
| `/api/payments` | `/payments` | Payments |
| `/api/payments/{id}` | `/payments/{id}` | Payments |
| `/api/graphql` | `/graphql` | GraphQL Gateway |

Los verbos y permisos particulares se detallan en las matrices de las secciones 5 y 6.

### 7.3. Inventario de secretos

| Referencia | Finalidad | Componente consumidor |
|---|---|---|
| `backend_shared_secret` | Comunicación Gateway–servicios REST | Gateway y microservicios |
| `auth_introspection_secret` | Introspección de sesiones | Gateway y Auth Service |
| `graphql_shared_secret` | Acceso al GraphQL privado | Gateway y GraphQL Gateway |
| `PAYMENTS_TO_ORDERS_SECRET` | Confirmación interna de pagos | Payments y Orders |
| `PAYMENT_TEST_SECRET` | Ejecución de confirmaciones simuladas | Payments |
| `VAULT_TOKEN` | Consulta al administrador de secretos | API Gateway |

Las primeras tres referencias se administran mediante Vault KV v2 en:

`secret/data/gateway`

Los consumidores internos reciben las credenciales correspondientes mediante su configuración de entorno.

Este documento registra referencias simbólicas y no incluye los valores de las credenciales.

### 7.4. Administración y rotación

El reemplazo de una credencial interna requiere:

1. Generar un nuevo valor.
2. Actualizar el almacenamiento o configuración correspondiente.
3. Actualizar los componentes consumidores.
4. Reiniciar los procesos que necesiten recargar su configuración.
5. Comprobar la comunicación autorizada.
6. Retirar la credencial anterior.

El uso de credenciales diferenciadas permite separar las comunicaciones de autenticación, GraphQL y confirmación de pagos.

El Gateway utiliza una credencial compartida para sus comunicaciones REST con los microservicios de negocio.

---

## 8. Clasificación y protección de datos

### 8.1. Inventario de datos

| Dato | Finalidad | Clasificación | Sistema custodio | Protección |
|---|---|---|---|---|
| Identificador y nombre de producto | Catálogo | Comercial | Inventory | Contrato de lectura |
| Descripción e imagen | Catálogo | Comercial | Inventory | Contrato de lectura |
| Precio | Cálculo de compra | Comercial | Inventory | Total calculado en servidor |
| RUN | Identificación de cliente | Personal restringido | Clients | Propiedad de recurso |
| Nombre y fecha de nacimiento | Perfil | Personal restringido | Clients | Control de acceso |
| Correo y teléfono | Contacto | Personal restringido | Clients | Control de acceso |
| Dirección | Información de pedido | Personal restringido | Clients / Orders | Control de acceso |
| Historial de pedidos | Gestión comercial | Restringido | Orders | Propiedad del pedido |
| Información de pagos | Gestión transaccional | Restringido | Payments | Propiedad del pago |
| Contraseña | Autenticación | Credencial | Auth Service | Hash y sal individual |
| Token de sesión | Autorización temporal | Credencial | Auth Service | Hash persistido y expiración |
| Secretos de integración | Comunicación privada | Secreto técnico | Vault y entorno | Acceso interno |

### 8.2. Protección de contraseñas

Auth Service utiliza PBKDF2-HMAC-SHA256 para procesar las contraseñas.

Cada contraseña se almacena mediante:

- Una sal aleatoria individual.
- Un hash derivado de la contraseña.
- 250.000 iteraciones configuradas.

El servicio compara el resultado derivado durante el inicio de sesión y no necesita conservar la contraseña original para autenticar al usuario.

### 8.3. Administración de sesiones

El sistema utiliza tokens aleatorios de sesión.

Auth Service almacena un hash del token junto con el usuario, los roles y el instante de expiración.

Las sesiones tienen una duración configurada de 15 minutos.

El cierre de sesión permite revocar el token y las comprobaciones posteriores rechazan las sesiones revocadas o expiradas.

### 8.4. Secretos del cliente

Las credenciales de integración se administran exclusivamente en componentes internos.

El navegador utiliza el token de sesión asociado al usuario autenticado para acceder a las rutas protegidas.

Los secretos que permiten operar entre microservicios no forman parte de los contratos destinados al cliente HTTP.

### 8.5. Entorno de transporte

La ejecución documentada utiliza direcciones de loopback (`127.0.0.1`) y comunicación HTTP local.

Las referencias de secretos y los controles implementados corresponden a esta configuración de ejecución.

---

## 9. GraphQL Gateway privado

El GraphQL Gateway se ejecuta mediante Node.js, Express y Apollo Server.

Su responsabilidad es agregar información entre servicios de negocio mediante operaciones de lectura.

### 9.1. Componentes y responsabilidades

| Componente | Función |
|---|---|
| API Gateway | Autenticar y autorizar la entrada HTTP |
| GraphQL Gateway | Interpretar y resolver consultas |
| Orders | Proporcionar información transaccional del pedido |
| Inventory | Proporcionar información comercial y disponibilidad |
| Auth Service | Validar la identidad utilizada por el Gateway |

### 9.2. Contrato GraphQL

La operación principal es:

`resumenPedido(id: ID!)`

Tipo:

`Query`

**Ejemplo:**

```graphql
query Resumen($id: ID!) {
  resumenPedido(id: $id) {
    id
    estado
    total
    modalidad
    items {
      productId
      nombre
      cantidad
      precioUnitario
      subtotal
      disponibleActual
    }
    advertencias
  }
}
```

**Variables de ejemplo:**

```json
{
  "id": "ORD-EJEMPLO"
}
```

El identificador debe reemplazarse por un pedido existente al ejecutar la consulta.

### 9.3. Resolución de la consulta

El procesamiento sigue esta secuencia:

1. API Gateway recibe la consulta autenticada.
2. Gateway valida la identidad del usuario.
3. Gateway reenvía la solicitud al GraphQL Gateway privado.
4. El resolver consulta Orders utilizando la identidad verificada.
5. Orders comprueba el acceso al pedido.
6. GraphQL consulta Inventory para obtener la información actual del catálogo.
7. El resolver combina la información en una sola respuesta.
8. Gateway entrega la respuesta al cliente HTTP.

Los estados y valores históricos del pedido provienen de Orders.

Los datos actuales de los productos provienen de Inventory.

### 9.4. Políticas de consulta

El GraphQL Gateway utiliza:

- Validación de credencial interna.
- Identidad de usuario verificada.
- Autorización mediante contratos de Orders.
- Restricciones de profundidad.
- Restricciones de tamaño y cantidad de campos.
- Tiempos máximos de espera.
- Tratamiento de errores de dependencias.
- Consulta agrupada del catálogo para resolver los ítems.
- Introspección del esquema deshabilitada.

Las operaciones de escritura del negocio permanecen en los servicios REST.

### 9.5. Respuesta ante fallos parciales

Si Orders no permite consultar el pedido, la agregación no devuelve sus datos restringidos.

Si Inventory no responde durante una consulta autorizada, GraphQL puede conservar la información histórica obtenida desde Orders y añadir una advertencia.

La disponibilidad actual se representa como desconocida cuando no puede determinarse.

---

## 10. Comunicación interna, analítica y rendimiento

### 10.1. Comunicación entre componentes

La comunicación transaccional implementada utiliza HTTP/JSON.

GraphQL se utiliza para la composición de información entre servicios.

Las alternativas de comunicación y procesamiento se describen en:

`docs/decisiones/ADR_Analitica_y_Comunicacion.md`

El ADR registra el contexto, las alternativas y las consecuencias de las decisiones arquitectónicas.

### 10.2. Caracterización de carga

Se ejecutó una prueba de lectura reproducible mediante:

`backend/pruebas/prueba_carga.py`

La prueba utilizó:

- 160 solicitudes.
- Concurrencia de seis trabajadores.
- Cuatro escenarios de consulta.
- Los servicios ejecutados en el entorno local.

### 10.3. Mediciones observadas

| Indicador | Valor registrado |
|---|---:|
| Solicitudes | 160 |
| Concurrencia | 6 |
| Errores HTTP o funcionales | 0 |
| Latencia p95 | 5.690,38 ms |
| Throughput | 1,39 solicitudes/s |

El reporte generado contiene el detalle de la ejecución, sus escenarios, códigos de respuesta y métricas adicionales de recursos.

Archivo de evidencia:

`docs/evaluacion/REPORTE_CARGA.md`

Las cifras corresponden a mediciones locales y no a valores estimados.

### 10.4. Interpretación

La ejecución procesó las 160 solicitudes registradas y no informó errores HTTP ni funcionales durante la carga medida.

La latencia y el rendimiento observados dependen del entorno, del número de solicitudes concurrentes, del procesamiento de autenticación y de las comunicaciones entre servicios.

Estas métricas permiten conservar una referencia cuantitativa para futuras comparaciones de rendimiento.

---

## 11. Comprobaciones funcionales reproducibles

El repositorio contiene un script Python que ejecuta solicitudes HTTP contra los servicios locales.

Ruta:

`backend/pruebas/pruebas_evaluacion2.py`

### 11.1. Alcance de las comprobaciones

El script incluye verificaciones de:

- Disponibilidad del API Gateway.
- Rechazo de solicitudes sin token.
- Acceso protegido a Inventory.
- Inicio de sesión de usuarios.
- Consulta del catálogo.
- Consulta de perfiles propios.
- Rechazo de acceso a perfiles ajenos.
- Restricción de operaciones administrativas.
- Creación de pedidos.
- Cálculo de importes en el backend.
- Recuperación de pedidos persistidos.
- Rechazo de acceso a pedidos ajenos.
- Creación de solicitudes de pago.
- Prevención de solicitudes de pago duplicadas.
- Rechazo de consultas de pagos ajenos.
- Restricción de confirmaciones de pago.
- Agregación entre Orders e Inventory.
- Protección del GraphQL privado.
- Restricción de consultas GraphQL excesivas.
- Cierre de sesión.
- Revocación de tokens.

### 11.2. Registro de resultados

La ejecución funcional realizada registró:

**23 comprobaciones coincidentes de un total de 23.**

Los resultados se encuentran en:

`docs/evaluacion/RESULTADOS_PRUEBAS.md`

La expresión *coincidente* indica que la respuesta observada correspondió a la condición esperada por el script.

No representa una aprobación externa ni una certificación del sistema.

### 11.3. Ejecución

Con MongoDB, Vault y los servicios activos, ejecutar desde la raíz del repositorio:

```powershell
python backend/pruebas/pruebas_evaluacion2.py
```

El programa solicita las contraseñas de los usuarios de prueba necesarios para las comprobaciones.

Para ejecutar la prueba de carga:

```powershell
python backend/pruebas/prueba_carga.py
```

Las instrucciones de preparación, arranque y configuración del entorno se encuentran en `README.md`.

---

## 12. Reproducibilidad y mantenimiento

### 12.1. Dependencias

Las bibliotecas Python utilizadas por el proyecto se encuentran declaradas en:

`requirements.txt`

Las dependencias de GraphQL están declaradas en:

- `backend/graphql-gateway/package.json`
- `backend/graphql-gateway/package-lock.json`

Los archivos permiten conservar las versiones de dependencias asociadas a la ejecución documentada.

### 12.2. Inicio del sistema

El entorno requiere:

1. MongoDB disponible.
2. Vault iniciado y configurado.
3. Auth Service activo.
4. Inventory activo.
5. Clients activo.
6. Orders activo.
7. Payments activo.
8. GraphQL Gateway activo.
9. API Gateway activo.

Las variables de entorno y los comandos correspondientes están documentados en el README principal.

### 12.3. Estructura documental

```text
docs/
├── arquitectura/
│   └── TokyoNoodles.dsl
├── decisiones/
│   └── ADR_Analitica_y_Comunicacion.md
├── evaluacion/
│   ├── INFORME_ARQUITECTURA.md
│   ├── RESULTADOS_PRUEBAS.md
│   └── REPORTE_CARGA.md
└── uml/
    ├── UML_Dominio.drawio
    ├── UML_Dominio.png
    ├── UML_Gateway.drawio
    └── UML_Gateway.png
```

### 12.4. Mantenimiento de los contratos

Cuando se modifica una ruta, un campo, una política de acceso o una regla de negocio, deben revisarse los documentos asociados.

En particular:

- Los endpoints REST deben coincidir con las rutas implementadas.
- Los permisos deben coincidir con las verificaciones del Gateway y los servicios.
- Las cardinalidades deben representar las reglas del dominio.
- Los diagramas deben mantenerse coherentes con los componentes ejecutables.
- Las referencias a secretos deben conservar sus nombres y finalidades.
- Las evidencias deben corresponder a ejecuciones reales.

### 12.5. Referencias arquitectónicas

El repositorio utiliza tres representaciones complementarias:

**Modelo C4**

`docs/arquitectura/TokyoNoodles.dsl`

Describe el contexto general, los contenedores y los componentes del Gateway.

**UML del dominio**

`docs/uml/UML_Dominio.drawio`

Describe entidades, atributos, servicios, asociaciones y multiplicidades.

**UML del API Gateway**

`docs/uml/UML_Gateway.drawio`

Describe políticas, rutas, destinos, secretos, agregación GraphQL y relaciones de dependencia.

---

## 13. Consideraciones técnicas del entorno

La solución está organizada para ejecutar y comprobar los componentes mediante procesos locales.

Los servicios privados se vinculan a direcciones de loopback y utilizan controles de credenciales para sus operaciones internas.

Los procesos del negocio conservan su información en MongoDB.

El API Gateway proporciona un punto de entrada común para las operaciones HTTP autorizadas.

Las credenciales de integración se suministran mediante la configuración del entorno y Vault, sin incorporarlas a los ejemplos de esta documentación.

Los scripts de comprobación registran las respuestas obtenidas en cada ejecución y permiten reproducir los escenarios funcionales y de carga documentados.

---

## 14. Conclusión arquitectónica

Tokyo Noodles organiza sus operaciones comerciales mediante una arquitectura de microservicios que distingue identidad, catálogo, clientes, pedidos, pagos y consultas agregadas.

Los cuatro servicios de negocio mantienen responsabilidades y datos diferenciados.

Auth Service administra usuarios y sesiones, API Gateway controla las solicitudes externas y GraphQL Gateway combina información transaccional y comercial mediante contratos privados.

MongoDB proporciona persistencia para los recursos administrados por los servicios y Vault permite gestionar las credenciales utilizadas en las integraciones.

La documentación incluye modelos UML editables, una descripción C4, contratos REST, decisiones arquitectónicas y registros reproducibles de ejecución.

En conjunto, estos elementos proporcionan una descripción técnica de los componentes implementados, sus responsabilidades, sus relaciones y su comportamiento observado.

---

**Integrante:** Patricio Frez