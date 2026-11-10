# Tokyo Noodles

**Plataforma de gestión comercial, catálogo, clientes, pedidos y pagos**
**Integrante entrega:** Patricio Frez
**Documentación técnica y operativa**

---

## 1. Resumen ejecutivo

Tokyo Noodles es una solución web orientada a la venta de productos gastronómicos. Su backend se organiza en cuatro microservicios privados: **Inventory**, **Clients**, **Orders** y **Payments**. El acceso a los servicios se centraliza en un **API Gateway**, que valida la identidad por medio de **Auth Service**, obtiene las credenciales de integración desde **HashiCorp Vault** y aplica controles de enrutamiento y autorización.

La persistencia de los datos comerciales y de las sesiones se implementa con **MongoDB**. Los servicios REST utilizan **Python, FastAPI, Motor y HTTPX**. La agregación de información se realiza por medio de un **GraphQL Gateway** construido con **Node.js, Express y Apollo Server**.

El repositorio mantiene el frontend responsivo y el backend como componentes independientes. La comunicación entre ambos está definida mediante contratos HTTP, rutas REST y una operación GraphQL de composición. Esta organización permite desarrollar, verificar y desplegar los componentes de forma controlada.

### 1.1. Capacidades del backend

| Componente | Capacidades |
|---|---|
| **Inventory** | Catálogo de diez productos, consultas, administración y disponibilidad |
| **Clients** | Registro de perfiles, consultas autorizadas, modificación y desactivación |
| **Orders** | Creación y consulta de pedidos, cálculo de totales, anulación y control de estados |
| **Payments** | Registro y consulta de solicitudes de pago; confirmación mediante adaptador de pruebas protegido |
| **Auth Service** | Inicio de sesión, roles, expiración y revocación de tokens; contraseñas con hash y sal |
| **API Gateway** | Autenticación, políticas por ruta y método, propagación de identidad validada y secretos |
| **GraphQL Gateway** | `resumenPedido`: información de Orders y disponibilidad de Inventory |
| **Persistencia** | Colecciones de MongoDB con responsabilidades definidas por servicio |
| **Verificación** | Suite Python de 23 escenarios HTTP y reporte reproducible de resultados |

### 1.2. Verificación funcional


La ejecución de `backend/pruebas/pruebas_evaluacion2.py` registró **23 de 23 comprobaciones coincidentes con los resultados esperados**.

Los resultados se encuentran documentados en `docs/evaluacion/RESULTADOS_PRUEBAS.md` e incluyen verificaciones de autenticación, autorización, acceso a recursos, cálculo de pedidos, solicitudes de pago y composición GraphQL.

Las verificaciones se realizaron mediante solicitudes HTTP contra los servicios ejecutados en el entorno local.


---

## 2. Arquitectura y responsabilidades

### 2.1. Vista lógica

```text
                        Cliente HTTP de pruebas
                                  |
                                  v
                         API Gateway :8000
                         /       |       \
                        v        v        v
                Auth Service    Vault    GraphQL Gateway
                   :9003       :8200        :8090
                     |                       |  \
                     |                       v   v
                     |                     Orders Inventory
                     |                     :9002   :9001
                     |                       ^       ^
                     |                       |       |
                     |              +--------+-------+
                     |              |        |       |
                     |           Payments  Clients    |
                     |             :9005     :9004    |
                     |                \        |     /
                     +-----------------+--------+----+
                                       |
                                 MongoDB :27017
```


El diagrama representa las comunicaciones verificadas entre el cliente HTTP de pruebas y los componentes del backend. El frontend responsivo se mantiene como un componente independiente dentro de la misma solución.

Las vistas C4 editables se encuentran en `docs/arquitectura/TokyoNoodles.dsl`. Los modelos UML del dominio y del API Gateway están disponibles en `docs/uml/`.


Es una vista conceptual de responsabilidades y comunicación. En el entorno local, los servicios se ejecutan asociados a `127.0.0.1`, con acceso controlado mediante el API Gateway y credenciales de integración.

### 2.2. Inventario de servicios

| Componente | Puerto local | Propietario de datos / responsabilidad | Dependencias |
|---|---:|---|---|
| API Gateway | 8000 | Identidad verificada, políticas de rutas y reenvío | Auth, Vault, servicios REST y GraphQL |
| Inventory | 9001 | `products`: catálogo, precios y disponibilidad | MongoDB |
| Orders | 9002 | `orders`: detalle, total histórico, estado y anulación | MongoDB, Inventory, Clients |
| Auth Service | 9003 | `auth_users`, `auth_sessions` | MongoDB |
| Clients | 9004 | `clients`: perfil y condición de actividad | MongoDB |
| Payments | 9005 | `payments`: solicitudes e importe autorizado | MongoDB, Orders |
| GraphQL Gateway | 8090 | Agregación de lectura; sin escritura de negocio | Orders, Inventory |
| Vault | 8200 | Secretos de integración en KV v2 | Servicio Vault |
| MongoDB | 27017 | Persistencia documental | Servidor MongoDB local |

**Decisión de diseño:** cada microservicio modifica su propia colección y obtiene información de otros sistemas a través de HTTP. Por ejemplo, Orders calcula el total con los precios de Inventory; Payments no modifica directamente la colección de Orders, sino que solicita su transición mediante un endpoint privado.

### 2.3. Modelo de datos y relaciones

| Entidad | Identificador | Atributos destacados | Relaciones del negocio |
|---|---|---|---|
| `Producto` | `id` | nombre, descripción, precio, categoría, imagen, `available` | Puede figurar en muchos detalles históricos |
| `Cliente` | `id` (`USR-...`) | RUN, nombre, correo, dirección, `activo` | Puede tener varios pedidos y pagos |
| `Pedido` | `id` (`ORD-...`) | `client_id`, items, total, modalidad, estado, fecha | Pertenece a un cliente; contiene al menos un ítem |
| `DetallePedido` | `product_id` dentro de pedido | nombre, cantidad, precio_unitario, subtotal | Conserva el precio aplicado al comprar |
| `Pago` | `id` (`PAY-...`) | `order_id`, `client_id`, monto, estado | Máximo un registro de pago por pedido según índice único |
| `UsuarioAuth` | `user_id` | usuario, roles, hash y salt | Puede tener múltiples sesiones |
| `Sesion` | `token_hash` | user_id, roles, vencimiento | Token revocable y con expiración |

Las asociaciones representan reglas del dominio. Entre colecciones se utilizan identificadores y contratos HTTP, sin depender de claves foráneas entre microservicios. El modelo conceptual se complementa con `docs/arquitectura/TokyoNoodles.dsl`.

### 2.4. Estructura relevante del repositorio

```text
Repositorio-Desarrollo-Web-y-M-vil/
├── backend/
│   ├── api-gateway/gateway.py
│   ├── auth-service/auth_service.py
│   ├── inventory/backend_api.py
│   ├── clients/backend_api.py
│   ├── orders/backend_api.py
│   ├── payments/backend_api.py
│   ├── graphql-gateway/
│   │   ├── server.js
│   │   ├── package.json
│   │   └── package-lock.json
│   ├── mensajeria/
│   │   ├── productor.py
│   │   └── consumidor.py
│   └── pruebas/pruebas_evaluacion2.py
├── docs/
│   ├── arquitectura/TokyoNoodles.dsl
│   └── evaluacion/
│       └── RESULTADOS_PRUEBAS.md
├── frontend/
└── .gitignore
```

El árbol se concentra en los componentes operativos principales. Los diagramas, contratos y documentación complementaria se encuentran organizados en `docs/`.

---

## 3. Requisitos de ejecución

### 3.1. Entorno de referencia comprobado

- **Sistema operativo de pruebas:** Windows con PowerShell y VS Code.
- **Python:** 3.14.3, según la instalación utilizada durante la validación.
- **Node.js:** 22.15.0.
- **npm:** 10.9.2.
- **Vault:** 2.1.1 en modo de desarrollo local.
- **MongoDB:** servicio local accesible en `127.0.0.1:27017` (versión exacta no registrada).
- **Bibliotecas Python utilizadas:** `fastapi`, `uvicorn`, `pydantic`, `motor`, `pymongo` y `httpx`.
- **Dependencias Node declaradas:** `apollo-server-express@3.13.0`, `express@4.21.2`, `graphql@15.10.3`.

El procedimiento de inicio se realiza directamente desde Windows y PowerShell, sin contenedores. Para otros entornos pueden adaptarse los comandos y el mecanismo de configuración de variables.

### 3.2. Instalación inicial

Desde la raíz del repositorio:

```powershell
python --version
node --version
npm --version
vault --version
```

Instalar las bibliotecas Python necesarias:

```powershell
python -m pip install -r requirements.txt
```

Instalar las dependencias de GraphQL utilizando su propia carpeta (no la raíz):

```powershell
cd backend/graphql-gateway
npm ci
node --check server.js
cd ../..
```

`npm ci` utiliza el `package-lock.json` para reproducir la resolución de dependencias JavaScript. Las actualizaciones de dependencias se administran mediante revisión de compatibilidad y repetición de la batería de pruebas; las modificaciones mayores se validan antes de incorporar cambios al entorno operativo.

Comprobar MongoDB:

```powershell
Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue
```

Si está detenido, iniciar el servicio MongoDB instalado en el equipo. Un puerto escuchando no garantiza por sí solo una conexión correcta: el arranque y las pruebas HTTP posteriores la comprueban.

---

## 4. Configuración de secretos y variables de entorno

Los secretos pertenecen a la configuración del entorno y permanecen fuera del código fuente. Los procedimientos siguientes configuran **Vault en modo de desarrollo local**, con almacenamiento temporal y credenciales separadas por finalidad.

### 4.1. Iniciar Vault (terminal independiente)

```powershell
vault server -dev -dev-listen-address="127.0.0.1:8200"
```

Dejar abierta esa terminal. Vault mostrará el token raíz de desarrollo generado para esta ejecución. En **otra** terminal PowerShell:

```powershell
$env:VAULT_ADDR = "http://127.0.0.1:8200"
$tokenSeguro = Read-Host "Token de desarrollo de Vault" -AsSecureString
$env:VAULT_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password
vault status
```

La respuesta esperada incluye `Initialized: true` y `Sealed: false`.

### 4.2. Dar de alta secretos de prueba

En la misma terminal ya autenticada contra Vault, ingresar **valores de prueba distintos y suficientemente largos** cuando se soliciten:

```powershell
function PedirSecreto($mensaje) {
    $valor = Read-Host $mensaje -AsSecureString
    return [System.Net.NetworkCredential]::new("", $valor).Password
}

$claveGateway = PedirSecreto "Secreto compartido Gateway/backend"
$claveAuth = PedirSecreto "Secreto de introspeccion Auth"
$claveGraphql = PedirSecreto "Secreto privado GraphQL"
$clavePayments = PedirSecreto "Secreto Payments a Orders"
$clavePrueba = PedirSecreto "Secreto de confirmacion simulada"

vault kv put -mount=secret gateway `
    "backend_shared_secret=$claveGateway" `
    "auth_introspection_secret=$claveAuth" `
    "graphql_shared_secret=$claveGraphql"

vault kv put -mount=secret payment-integration `
    "payments_to_orders_secret=$clavePayments" `
    "payment_test_secret=$clavePrueba"

Remove-Variable claveGateway,claveAuth,claveGraphql,clavePayments,clavePrueba
```

Los comandos anteriores corresponden a un entorno local de desarrollo. En un entorno administrado se asignan políticas de acceso de mínimo privilegio a cada identidad técnica y se utiliza un procedimiento de rotación controlada de credenciales.

Para comprobar nombres de claves, **sin imprimir valores**:

```powershell
$r = Invoke-RestMethod `
  -Uri "$env:VAULT_ADDR/v1/secret/data/gateway" `
  -Headers @{"X-Vault-Token"=$env:VAULT_TOKEN}
$r.data.data.PSObject.Properties.Name
```

Se esperan `backend_shared_secret`, `auth_introspection_secret` y `graphql_shared_secret`.

### 4.3. Variables por servicio

| Variable | Consumidor | Propósito |
|---|---|---|
| `VAULT_ADDR` | Gateway, terminales de configuración | Dirección de Vault |
| `VAULT_TOKEN` | Gateway / herramienta CLI | Leer secretos en Vault |
| `INTERNAL_GATEWAY_SECRET` | Inventory, Clients, Orders, Payments, GraphQL | Rechazar llamadas sin credencial interna |
| `AUTH_INTROSPECTION_SECRET` | Auth Service | Autorizar introspección de token |
| `GRAPHQL_GATEWAY_SECRET` | GraphQL Gateway | Autorizar la llamada desde Gateway |
| `PAYMENTS_TO_ORDERS_SECRET` | Payments, Orders | Autorizar confirmación interna |
| `PAYMENT_TEST_SECRET` | Payments | Proteger simulador de confirmación |
| `PAYMENT_TEST_MODE` | Payments | `1` habilita solo en pruebas; omitido/desactivado por defecto |
| `MONGO_URL` | Microservicios y Auth | URI local MongoDB; predeterminado `mongodb://127.0.0.1:27017` |
| `AUTH_PASSWORD_ANA`, `AUTH_PASSWORD_PEDRO`, `AUTH_PASSWORD_ERNESTO` | Auth Service | Alta inicial de cuentas **solo si aún no existen** |
| `AUTH_SERVICE_URL`, `INVENTORY_URL`, `ORDERS_URL`, `CLIENTS_URL`, `PAYMENTS_URL`, `GRAPHQL_URL` | Gateways/servicios | Sobrescribir URLs locales si cambia el despliegue |

**Consideración sobre cuentas iniciales:** las contraseñas pasadas por variables al iniciar Auth solo se usan para **crear** usuarios que no existen; reiniciar con valores nuevos **no modifica** contraseñas previamente guardadas en MongoDB. No se deben registrar contraseñas de pruebas en este documento.

---

## 5. Inicio completo del backend

Cada comando `uvicorn` o `npm start` se ejecuta en **una terminal independiente que debe permanecer abierta**. Al iniciar un proceso desde una terminal nueva, las variables de otra terminal **no se heredan automáticamente**.

### 5.1. Preparación de una terminal de servicio

Ejecutar el bloque siguiente **en cada terminal nueva**, antes del comando de arranque correspondiente:

```powershell
$env:VAULT_ADDR = "http://127.0.0.1:8200"
$seguro = Read-Host "Token Vault del entorno de prueba" -AsSecureString
$env:VAULT_TOKEN = [System.Net.NetworkCredential]::new("", $seguro).Password
$env:INTERNAL_GATEWAY_SECRET = (vault kv get -mount=secret -field=backend_shared_secret gateway).Trim()
$env:AUTH_INTROSPECTION_SECRET = (vault kv get -mount=secret -field=auth_introspection_secret gateway).Trim()
$env:GRAPHQL_GATEWAY_SECRET = (vault kv get -mount=secret -field=graphql_shared_secret gateway).Trim()
$env:PAYMENTS_TO_ORDERS_SECRET = (vault kv get -mount=secret -field=payments_to_orders_secret payment-integration).Trim()
$env:PAYMENT_TEST_SECRET = (vault kv get -mount=secret -field=payment_test_secret payment-integration).Trim()
```

Para facilitar la puesta en marcha local, el bloque establece las variables utilizadas por los diferentes procesos. En entornos segregados, cada componente recibe únicamente los secretos vinculados con su responsabilidad.

### 5.2. Orden de arranque y comandos

Primero MongoDB y Vault; luego los microservicios y Auth; por último GraphQL y Gateway. Ejecutar **uno por terminal**, desde la **raíz del repositorio**:

**Terminal Inventory (9001)**

```powershell
python -m uvicorn backend_api:app --app-dir backend/inventory --host 127.0.0.1 --port 9001
```

**Terminal Clients (9004)**

```powershell
python -m uvicorn backend_api:app --app-dir backend/clients --host 127.0.0.1 --port 9004
```

**Terminal Orders (9002)**

```powershell
python -m uvicorn backend_api:app --app-dir backend/orders --host 127.0.0.1 --port 9002
```

**Terminal Payments (9005)**

```powershell
$env:PAYMENT_TEST_MODE = "0"
python -m uvicorn backend_api:app --app-dir backend/payments --host 127.0.0.1 --port 9005
```

**Terminal Auth Service (9003)**. En una **base nueva**, configurar contraseñas de demostración **distintas**, de 8 caracteres como mínimo, antes de arrancar:

```powershell
function ClaveInicial($usuario) {
    $seguro = Read-Host "Contrasena inicial de $usuario" -AsSecureString
    return [System.Net.NetworkCredential]::new("", $seguro).Password
}
$env:AUTH_PASSWORD_ANA = ClaveInicial "ana"
$env:AUTH_PASSWORD_PEDRO = ClaveInicial "pedro"
$env:AUTH_PASSWORD_ERNESTO = ClaveInicial "ernesto"
python -m uvicorn auth_service:app --app-dir backend/auth-service --host 127.0.0.1 --port 9003
```

**Terminal GraphQL (8090)**

```powershell
cd backend/graphql-gateway
npm start
```

Después del arranque, volver a la raíz **solo en otras terminales**; esta terminal debe quedarse atendiendo peticiones.

**Terminal API Gateway (8000)**

```powershell
python -m uvicorn gateway:app --app-dir backend/api-gateway --host 127.0.0.1 --port 8000
```

Los puertos de Auth, Payments, Inventory y GraphQL se utilizan como interfaces internas y se mantienen vinculados a `127.0.0.1`. Para el acceso desde otra red se define una política de publicación controlada, cifrado TLS y separación de la infraestructura.

### 5.3. Crear el perfil ficticio inicial de Ana en una base nueva

El usuario `ana` en Auth y su perfil en Clients son **registros diferentes**. Para que las pruebas de pedidos funcionen en una base recién instalada, es necesario crear el perfil `USR-001` después de iniciar sesión. La información siguiente es estrictamente **ficticia**:

```powershell
$seguro = Read-Host "Contrasena de ana" -AsSecureString
$clave = [System.Net.NetworkCredential]::new("", $seguro).Password
$login = Invoke-RestMethod -Method POST `
  -Uri "http://127.0.0.1:8000/api/auth/login" `
  -Body (@{username="ana";password=$clave} | ConvertTo-Json) `
  -ContentType "application/json"
Remove-Variable clave

$h = @{Authorization = "Bearer $($login.access_token)"}
$perfil = @{
  id="USR-001";run="11111111-1";nombre="Ana Ejemplo"
  direccion="Calle Ejemplo 123";comuna="Maipu";provincia="Santiago"
  region="Metropolitana";fecha_nacimiento="2000-01-15";sexo="F"
  correo="ana@example.test";telefono="912345678"
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/api/clients" `
  -Headers $h -ContentType "application/json" -Body $perfil
```

Si el perfil ya existe, el servicio puede devolver `409 Conflict`; en ese caso **no repetir el alta**. Los valores ficticios no constituyen validación oficial de RUN ni verificación del correo. Para el script de pruebas se necesitan además las cuentas `ana` y `pedro` existentes en Auth. Los registros y pedidos de prueba quedan en MongoDB hasta que se depuren de forma controlada.

### 5.4. Health checks

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8090/health
Invoke-RestMethod http://127.0.0.1:9001/health
Invoke-RestMethod http://127.0.0.1:9002/health
Invoke-RestMethod http://127.0.0.1:9003/health
Invoke-RestMethod http://127.0.0.1:9004/health
Invoke-RestMethod http://127.0.0.1:9005/health
```

Una respuesta `status: OK` verifica la respuesta HTTP del proceso. Las pruebas funcionales complementan este control mediante operaciones reales sobre los contratos.

### 5.5. Detención

Detener cada proceso con **Ctrl+C** en su terminal. Dejar Vault para el final. En modo `-dev`, reiniciar Vault borra sus secretos; deben configurarse nuevamente antes de reiniciar Gateway y GraphQL. MongoDB conserva las colecciones en su directorio de datos configurado.

---

## 6. Contratos HTTP disponibles

**Dirección de acceso local:** `http://127.0.0.1:8000`. Las rutas `/api/...` documentadas aquí requieren token Bearer, **salvo** `/api/auth/login`. Las rutas directas en puertos internos no están destinadas al navegador.

### 6.1. Identidad y sesiones

| Método | Ruta | Acceso | Resultado principal |
|---|---|---|---|
| POST | `/api/auth/login` | Sin sesión previa | Token de acceso y vigencia |
| POST | `/api/auth/logout` | Bearer válido | Revocación de sesión |
| POST | `/register` en Auth :9003 | Ruta interna | Alta de identidad con validación de nombre y contraseña |

Ejemplo de cuerpo para iniciar sesión (usar contraseña propia, **no guardar el JSON con credenciales reales**):

```json
{"username":"ana","password":"<CONTRASENA_DE_PRUEBA>"}
```

Respuesta de ejemplo (token ilustrativo, no utilizable):

```json
{"access_token":"<TOKEN_TEMPORAL>","token_type":"bearer","expires_in":900}
```

Auth genera tokens aleatorios, guarda su hash SHA-256, los valida mediante introspección autorizada y permite revocarlos. No se presenta el token como JWT.

### 6.2. Inventario

| Método | Ruta externa | Acceso / efecto |
|---|---|---|
| GET | `/api/products` | Usuario autenticado; lista productos, filtro `available` opcional |
| GET | `/api/products/{id}` | Usuario autenticado; detalle |
| POST | `/api/products` | Administrador; crea producto |
| PUT | `/api/products/{id}` | Administrador; reemplaza producto |
| DELETE | `/api/products/{id}` | Administrador; **desactiva** producto, sin borrar historial |

Entrada representativa para crear o modificar un producto:

```json
{
  "id": "11",
  "nombre": "Producto ficticio",
  "descripcion": "Producto de demostracion",
  "precio": 1000,
  "imagen": "img/ejemplo.png",
  "categoria": "ramen",
  "available": true
}
```

Inventory crea inicialmente diez productos cuando faltan en la colección. Los datos persistidos no se sobrescriben en cada arranque (`$setOnInsert`). Un producto marcado como no disponible no puede incorporarse a un pedido nuevo.

**Política de consulta:** la API Gateway requiere autenticación para `GET /api/products` y `GET /api/products/{id}`. El servicio Inventory valida además la credencial de comunicación interna.

### 6.3. Clientes

| Método | Ruta externa | Acceso / efecto |
|---|---|---|
| GET | `/api/clients` | Administrador; lista perfiles |
| GET | `/api/clients/{id}` | Propietario o administrador |
| POST | `/api/clients` | Usuario autenticado, con `id` coincidente con su identidad; o administrador |
| PUT | `/api/clients/{id}` | Propietario o administrador |
| DELETE | `/api/clients/{id}` | Administrador; desactiva registro |

Contrato de ejemplo de perfil:

```json
{
  "id": "USR-001",
  "run": "11111111-1",
  "nombre": "Ana Ejemplo",
  "direccion": "Calle Ejemplo 123",
  "comuna": "Maipu",
  "provincia": "Santiago",
  "region": "Metropolitana",
  "fecha_nacimiento": "2000-01-15",
  "sexo": "F",
  "correo": "ana@example.test",
  "telefono": "912345678"
}
```

Clients controla la propiedad del perfil, administra duplicados de `id`, RUN y correo, y registra el indicador `correo_verificado` con valor inicial `false`. El contrato valida tipos y formatos de los campos recibidos.

### 6.4. Pedidos

| Método | Ruta externa | Acceso / efecto |
|---|---|---|
| GET | `/api/orders` | Usuario: pedidos propios; administrador: todos |
| GET | `/api/orders/{id}` | Propietario o administrador |
| POST | `/api/orders` | Cliente autenticado y activo |
| POST | `/api/orders/{id}/cancel` | Propietario o administrador; depende del estado |
| PUT | `/api/orders/{id}/status` | Administrador; transición permitida |

Solicitud de compra (nunca enviar precios ni un estado de pago confiable desde el cliente):

```json
{
  "modalidad": "retiro",
  "items": [
    {"product_id": "1", "quantity": 2},
    {"product_id": "5", "quantity": 1}
  ]
}
```

Con los precios iniciales, el servidor calcula `2 × 13800 + 2900 = 30500` CLP. El pedido generado incluye un identificador `ORD-...`, los precios unitarios del momento de compra, el total y el estado inicial `pendiente_pago`.

Reglas existentes:

- Se exige al menos un ítem; no se aceptan cantidades nulas/negativas ni productos repetidos en la misma solicitud.
- Orders consulta a Clients y a Inventory antes de crear el pedido; si las dependencias no responden o el producto no existe, no genera una compra confirmada.
- Los precios y subtotales los determina el backend, no el navegador.
- Antes de pagar se admite la anulación con motivo. Para un pedido pagado se registra solicitud de anulación, **sin asumir un reembolso automático**.
- La confirmación de pago y las transiciones de preparación/entrega tienen reglas de estado.

**Modalidades:** el servicio distingue `retiro` y `delivery`. Para `delivery` solicita una dirección; la lógica de tarifas y cobertura se mantiene separada del cálculo de importes del catálogo.

### 6.5. Pagos

| Método | Ruta | Acceso / efecto |
|---|---|---|
| POST | `/api/payments` | Propietario del pedido pendiente; registra solicitud |
| GET | `/api/payments/{id}` | Propietario del pago |
| POST | `/orders/{id}/confirm-payment` en Orders :9002 | **Interna**; requiere credencial Payments → Orders y rol técnico |
| POST | `/payments/{id}/test-confirm` en Payments :9005 | **Uso interno de pruebas**, si `PAYMENT_TEST_MODE=1` y se presenta credencial especial |

Cuerpo para iniciar una solicitud:

```json
{"order_id":"ORD-IDENTIFICADOR-FICTICIO"}
```

Payments obtiene el monto desde Orders, registra una solicitud pendiente e impone unicidad por `order_id`. Para verificar la transición de estados se dispone de un **adaptador de confirmación simulada** protegido por credencial adicional, habilitado mediante `PAYMENT_TEST_MODE=1` exclusivamente en sesiones de prueba. La integración con proveedores de pago se puede incorporar mediante un adaptador que conserve los contratos y reglas de negocio de Payments.

### 6.6. GraphQL privado

- **Ruta de acceso autorizada:** `POST /api/graphql` con Bearer, a través del Gateway.
- **Ruta interna:** `POST http://127.0.0.1:8090/graphql`, protegida por secreto privado.
- **Operación implementada:** `Query.resumenPedido(id: ID!)`.
- **Origen de información:** Orders (propiedad, estado, importes históricos) + Inventory (disponibilidad actual).
- **Escrituras:** ninguna Mutation; se mantienen en las APIs REST.

Consulta de ejemplo:

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

Variables de ejemplo:

```json
{"id":"ORD-IDENTIFICADOR-FICTICIO"}
```

GraphQL consulta primero el pedido con la identidad validada; Orders comprueba que pertenezca al usuario. Después consulta el catálogo una sola vez y vincula productos por identificador. Si Inventory falla, puede devolver el resumen histórico y una advertencia, sin inventar disponibilidad. El servicio limita longitud, cantidad de campos y profundidad, impide introspección y rechaza llamadas directas sin credencial.

La operación cuenta con evidencia de ejecución mediante el cliente HTTP de pruebas, a través de `/api/graphql`.

### 6.7. Estados HTTP y errores

| Código | Interpretación en este proyecto | Ejemplos |
|---|---|---|
| `200` | Consulta o acción completada | Login, consulta, anulación |
| `201` | Recurso creado | Pedido, perfil, pago |
| `400` | Entrada u operación inválida | Producto inexistente en pedido, límite GraphQL |
| `401` | Sin autenticación o sesión inválida | Token ausente o revocado |
| `403` | Operación prohibida | Pedido ajeno, ruta administrativa, secreto inválido |
| `404` | Recurso inexistente | Pedido, producto o pago no encontrado |
| `409` | Conflicto de negocio | Duplicado, transición no permitida |
| `422` | Error de validación de entrada | Tipos, formatos o rangos inválidos |
| `502` / `503` | Fallo en dependencia o servicio | Vault, Auth, GraphQL o servicio interno no disponible |

Los códigos se interpretan de acuerdo con el contrato y el estado del recurso consultado.

---

## 7. Seguridad, identidad y privacidad

### 7.1. Fronteras de confianza

El navegador **no debe** enviar una identidad interna confiable. El Gateway genera `X-Authenticated-Client`, `X-Authenticated-User` y `X-Authenticated-Roles` a partir de la introspección del token, y aporta `X-Gateway-Secret` para los microservicios. Cada servicio repite los controles relevantes de autorización por propietario, administrador y estado.

La ruta de confirmación de pagos requiere una **segunda credencial específica** (`X-Payments-Secret`); no aparece en el enrutamiento público del Gateway.

GraphQL acepta únicamente solicitudes con su secreto de servicio e identidad interna; el Gateway externo requiere Bearer para acceder a él.

### 7.2. Clasificación de información

| Información | Clasificación | Tratamiento |
|---|---|---|
| Descripción de productos | Pública/comercial | Contrato de catálogo |
| Precios y disponibilidad | Comercial | Autoridad de Inventory; cálculo de pedido en backend |
| RUN, correo, teléfono, domicilio | Personal restringida | Propietario y roles autorizados |
| Pedidos y pagos | Personal/transaccional | Consultas filtradas por usuario |
| Contraseñas | Credenciales | PBKDF2-HMAC-SHA256, sal aleatoria, 250.000 iteraciones |
| Sesiones | Credenciales temporales | Token aleatorio, hash persistido, expiración a 15 minutos y revocación |
| Secretos de servicios | Integración restringida | Vault y variables de proceso; nunca frontend |

**Criterios de operación segura:** en infraestructura administrada se aplican TLS, políticas de mínimo privilegio en Vault, rotación de credenciales, control de retención de datos personales, registros de auditoría con datos minimizados, seguimiento de dependencias y controles frente a tráfico abusivo. Estas medidas forman parte de las políticas de despliegue y operación de la plataforma.

### 7.3. Rotación, filtración y recuperación

Si se sospecha compromiso de una clave, debe regenerarse, actualizarse en Vault y en los procesos consumidores, reiniciarse los servicios necesarios y revocarse la credencial anterior. Si se expone un token de sesión, debe revocarse mediante logout o invalidación de sesiones. No colocar secretos ni contraseñas en URL, código, capturas, informes o control de versiones.

Vault `-dev` conserva los secretos en memoria y requiere reconfiguración tras reiniciarse. MongoDB conserva sus colecciones de acuerdo con la configuración de almacenamiento del servidor. Las operaciones de copia de seguridad se gestionan por el administrador de la instancia de MongoDB.

---

## 8. Pruebas y evidencias reproducibles

### 8.1. Ejecución

Con todos los servicios activos y las cuentas ficticias `ana` y `pedro` creadas:

```powershell
python -m py_compile backend/pruebas/pruebas_evaluacion2.py
python backend/pruebas/pruebas_evaluacion2.py
```

El script solicita las contraseñas de forma interactiva y las oculta durante su ingreso, y efectúa solicitudes HTTP a las APIs reales. En un entorno limpio es necesario crear primero el perfil `USR-001` de Ana, como se indica en §5.3.

### 8.2. Resultado documentado

En la ejecución registrada se obtuvo:

```text
RESULTADO FINAL: 23/23
```

El script actualiza `docs/evaluacion/RESULTADOS_PRUEBAS.md` con la fecha, la cantidad de comprobaciones coincidente y los resultados de la ejecución. Se recomienda ejecutar nuevamente la suite después de modificar contratos o reglas de negocio.

La batería verifica: salud del Gateway; solicitudes anónimas; bloqueo de Inventory directo; login de dos cuentas; 10 productos; propiedad de perfiles y pedidos; permisos administrativos; creación y total de pedidos; solicitudes de pago e idempotencia básica; prohibición de confirmar pagos desde el cliente; agregación GraphQL; bloqueo de acceso GraphQL directo; límites de consulta; logout y revocación de token.

**Alcance de esta batería:** pruebas HTTP funcionales sobre identidad, autorización, catálogo, perfiles, pedidos, pagos y GraphQL. Las mediciones de rendimiento, las pruebas de infraestructura y las integraciones con proveedores utilizan procedimientos especializados de operación.

### 8.3. Verificaciones manuales útiles

```powershell
# Sin credenciales, la ruta comercial protegida debe devolver HTTP 401.
try {
  Invoke-WebRequest http://127.0.0.1:8000/api/products -ErrorAction Stop
} catch {
  [int]$_.Exception.Response.StatusCode
}

# El GraphQL interno, sin secreto de integración, debe devolver HTTP 403.
try {
  Invoke-WebRequest -Method POST http://127.0.0.1:8090/graphql `
    -ContentType "application/json" -Body '{"query":"{__typename}"}' `
    -ErrorAction Stop
} catch {
  [int]$_.Exception.Response.StatusCode
}
```

Los registros de verificación se conservan sin tokens, contraseñas ni valores de secretos.

---

## 9. Operación, mantenimiento e incidencias

| Síntoma | Posible causa | Comprobación o acción |
|---|---|---|
| `ModuleNotFoundError` | Paquete Python no instalado en el intérprete activo | `python -m pip install fastapi uvicorn pydantic motor pymongo httpx` |
| npm busca `package.json` en la raíz | Terminal en carpeta incorrecta | `cd backend/graphql-gateway; npm ci` |
| `Application startup failed` en Auth | Contraseña inicial menor que 8 caracteres o MongoDB inaccesible | Revisar mensaje del servidor y variables de Auth |
| `Address already in use` | Puerto ocupado por otra instancia | `Get-NetTCPConnection -LocalPort <PUERTO> -State Listen` |
| Gateway responde `503` al autenticar | Vault inaccesible, token Vault inválido o secretos faltantes | Comprobar Vault, URL, token y nombres de claves |
| Gateway responde `502` | Microservicio interno o GraphQL no disponible | Verificar puerto y terminal del servicio de destino |
| `/api/products` responde `401` | Falta token, expiró o fue revocado | Volver a autenticar |
| Consulta ajena responde `403` | Control de propiedad funcionando | Utilizar identidad propietaria o rol válido |
| Crear pedido falla | Falta perfil activo o Inventory no responde | Revisar Clients, Inventory y registros de servidor |
| GraphQL no inicia | Dependencias no instaladas o secretos de entorno ausentes | Verificar `npm ci`, variables y puerto 8090 |
| `npm audit` reporta avisos de seguridad | Paquetes con actualizaciones de mantenimiento | Revisar avisos, evaluar compatibilidad y ejecutar nuevamente las pruebas tras cambios |
| Reiniciar Vault rompe acceso | Se perdieron secretos al usar modo `-dev` | Volver a cargar KV y reiniciar consumidores |
| Las pruebas dan menos de 23/23 | Datos de prueba faltantes, dependencia caída o cambio de contrato | Revisar prueba exacta, código HTTP y estado de servicios |

En despliegues administrados se complementan los endpoints de salud con métricas, registros, alertas, respaldos y procedimientos de recuperación establecidos por la operación.

---

## 10. Criterios de comunicación y rendimiento

Los servicios transaccionales intercambian información mediante contratos REST y tiempos máximos de espera configurados. El GraphQL Gateway incorpora una vista de lectura que reúne información de Orders e Inventory en una única consulta autorizada.

Esta arquitectura favorece la separación de responsabilidades y mantiene un modelo de comunicación homogéneo para catálogo, clientes, pedidos y pagos. Las decisiones de evolución se evalúan en función de indicadores como volumen de transacciones, concurrencia, tamaño de mensajes, latencia y necesidad de procesamiento continuo.

Entre las métricas recomendadas para el seguimiento operativo se encuentran la latencia p95, el throughput, los códigos HTTP por operación, el uso de CPU y memoria, así como la disponibilidad de las dependencias internas.


## 11. Organización del frontend y el backend

Tokyo Noodles organiza sus componentes en dos áreas principales: la interfaz web responsiva y los servicios backend.

### 11.1. Frontend responsivo

El frontend se encuentra en `frontend/` y utiliza PHP, HTML, CSS y JavaScript.

Contiene las interfaces de navegación, catálogo, promociones, acceso de usuarios y carrito de compras. Su estructura se conserva de forma independiente respecto de los servicios backend.

Esta separación permite mantener la presentación visual y la lógica transaccional en componentes con responsabilidades diferenciadas.

### 11.2. Backend y contratos HTTP

El backend concentra la autenticación, la autorización, la persistencia de datos, las reglas de negocio y la comunicación entre microservicios.

El API Gateway dispone de las siguientes familias de rutas:

- `/api/auth/login` y `/api/auth/logout`: autenticación y cierre de sesión.
- `/api/products`: consulta y administración del catálogo.
- `/api/clients`: gestión de perfiles.
- `/api/orders`: creación, consulta y administración de pedidos.
- `/api/payments`: inicio y consulta de solicitudes de pago.
- `/api/graphql`: consulta agregada mediante GraphQL.

Las rutas protegidas utilizan tokens Bearer. El Gateway valida la identidad y aplica permisos iniciales según el método HTTP y la ruta solicitada.

Los microservicios mantienen las reglas de validación, propiedad de recursos y transición de estados que corresponden a sus responsabilidades.

### 11.3. Separación de responsabilidades

- El frontend administra la presentación y las interacciones visuales.
- El API Gateway controla la entrada HTTP y el enrutamiento autorizado.
- Auth Service administra las credenciales, sesiones y roles.
- Inventory mantiene los productos y sus precios oficiales.
- Clients administra los perfiles y datos de clientes.
- Orders calcula importes y conserva el historial de pedidos.
- Payments administra las solicitudes de pago y sus estados.
- GraphQL Gateway combina datos de Orders e Inventory mediante contratos internos.

Esta organización evita trasladar al navegador las credenciales de integración y las reglas críticas de negocio.

### 11.4. Documentación de interfaces

Los contratos de servicios, sus parámetros y las reglas de autorización se describen en este README y en `docs/evaluacion/INFORME_ARQUITECTURA.md`.

Los diagramas editables se encuentran en `docs/uml/` y el modelo de arquitectura C4 en `docs/arquitectura/TokyoNoodles.dsl`.


## 12. Estructura de documentación y operación

La documentación se organiza para facilitar consulta, soporte y reproducción del entorno:

| Recurso | Finalidad |
|---|---|
| `README.md` | Manual técnico, arquitectura, contratos y puesta en marcha |
| `docs/arquitectura/TokyoNoodles.dsl` | Vistas de arquitectura y componentes |
| `backend/pruebas/pruebas_evaluacion2.py` | Verificaciones funcionales por HTTP |
| `docs/evaluacion/RESULTADOS_PRUEBAS.md` | Registro de resultados de la suite |
| `backend/graphql-gateway/package.json` | Dependencias y comandos de GraphQL |
| `backend/graphql-gateway/package-lock.json` | Resolución reproducible de paquetes JavaScript |
| `requirements.txt` | Versiones de las dependencias Python utilizadas por los servicios |

La información de configuración se mantiene separada del código y las credenciales de los servicios se gestionan mediante Vault y variables de entorno.

---

## 13. Preparación del repositorio y distribución

### 13.1. Archivos incluidos

- Código fuente del frontend responsivo en `frontend/`.
- Código de los cuatro microservicios, Auth Service, API Gateway y GraphQL Gateway.
- `package.json` y `package-lock.json` del servicio GraphQL.
- Script Python de pruebas y `RESULTADOS_PRUEBAS.md` correspondiente a la versión final.
- Modelo de arquitectura `docs/arquitectura/TokyoNoodles.dsl` y documentación técnica del repositorio.
- Este `README.md`, coherente con los archivos distribuidos.
- `requirements.txt` con las versiones de dependencias Python del entorno utilizado.

### 13.2. Archivos excluidos

- `node_modules/`, `__pycache__/`, `*.pyc`, entornos virtuales y archivos temporales.
- `.env`, contraseñas, tokens, claves, archivos de Vault y registros que contengan secretos.
- Bases de datos locales con información personal real.
- Backups ZIP dentro del ZIP de entrega y archivos de configuración privados de la máquina.

### 13.3. Verificaciones previas a la distribución

```powershell
git status --short
git check-ignore backend/graphql-gateway/node_modules
git check-ignore backend/inventory/__pycache__
python -m py_compile backend/api-gateway/gateway.py
python -m py_compile backend/auth-service/auth_service.py
python -m py_compile backend/inventory/backend_api.py
python -m py_compile backend/clients/backend_api.py
python -m py_compile backend/orders/backend_api.py
python -m py_compile backend/payments/backend_api.py
python -m py_compile backend/pruebas/pruebas_evaluacion2.py
node --check backend/graphql-gateway/server.js
```

Revisar `git status` para validar los cambios de rutas producidos por la reorganización del proyecto. Confirmar que las carpetas actuales y los archivos del frontend estén incluidos antes del commit. Conservar un respaldo verificable antes de utilizar comandos de limpieza o restauración de Git.

El paquete distribuido debe representar una versión coherente del código, contratos, configuración documentada y evidencias funcionales.

---

---

## 14. Referencias técnicas internas

- `docs/arquitectura/TokyoNoodles.dsl`: modelo de arquitectura de la solución.
- `backend/api-gateway/gateway.py`: enrutamiento, autenticación y autorización de solicitudes externas.
- `backend/auth-service/auth_service.py`: gestión de usuarios y sesiones.
- `backend/graphql-gateway/server.js`: schema, resolvers y límites de consultas.
- `backend/pruebas/pruebas_evaluacion2.py`: script de verificación HTTP.
- `docs/evaluacion/RESULTADOS_PRUEBAS.md`: registro de los resultados ejecutados.

## 15. Integrante y mantenimiento técnico

**Integrante entrega:** Patricio Frez
**Sistema:** Tokyo Noodles
**Componentes:** frontend responsivo, backend de microservicios, API Gateway, Auth Service, GraphQL Gateway, MongoDB y Vault.

La organización del repositorio, los contratos de servicio y las instrucciones de puesta en marcha están diseñados para facilitar la transferencia técnica, la operación local, la verificación de resultados y el mantenimiento evolutivo de la plataforma.
