
# Tokyo Noodles

**Plataforma web de gestión comercial, clientes, pedidos y pagos**
**Evaluaciones 2 y 3 — Desarrollo Web y Móvil**
**Integrante:** Patricio Frez
**Validación local:** 23 de noviembre de 2026
**Modalidad:** desarrollo y demostración académica.

## 1. Descripción

Tokyo Noodles adapta el caso gastronómico Fukusuke Sushi-Delivery a una aplicación web responsiva que permite consultar productos, registrarse, iniciar sesión, administrar un carrito, crear pedidos y consultar su estado.

El personal autorizado puede gestionar pedidos, consultar reportes y confirmar pagos simulados.

La Evaluación 2 desarrolla la arquitectura y los servicios. La Evaluación 3 integra el frontend con el backend y verifica los recorridos mediante pruebas, trazabilidad y evidencias.

## 2. Arquitectura

La solución utiliza:

| Componente | Tecnología y responsabilidad |
|---|---|
| Frontend | PHP, HTML, CSS, JavaScript y Bootstrap |
| API Gateway | FastAPI; entrada HTTP, autorización y enrutamiento |
| Auth Service | Cuentas, login, roles, sesiones e introspección |
| Inventory | Catálogo, stock, disponibilidad y precios |
| Clients | Perfiles y verificación de correo |
| Orders | Pedidos, totales, estados y control de duplicados |
| Payments | Solicitudes y confirmación simulada de pagos |
| GraphQL Gateway | Node.js, Express y Apollo; agregación de Orders e Inventory |
| MongoDB | Persistencia de cuentas, pedidos, pagos y eventos |
| HashiCorp Vault | Almacenamiento de secretos de integración |
| ActiveMQ/STOMP | Publicación y consumo de eventos |
| Docker Compose | Despliegue local de los componentes |

El recorrido principal es:

```text
Navegador
   |
   v
API Gateway
   |------ Vault
   |------ Auth Service
   |
   +------ Inventory
   +------ Clients
   +------ Orders
   +------ Payments
   +------ GraphQL Gateway
              |
              v
           MongoDB

Orders -> ActiveMQ -> Consumidor -> MongoDB
```

Los microservicios se comunican dentro de la red de Docker. El navegador accede a los servicios mediante el API Gateway.

Los diagramas editables y las decisiones de diseño se encuentran en `docs/arquitectura/`, `docs/uml/` y `docs/decisiones/`.

## 3. Requisitos

- Docker Desktop con motor Linux y Docker Compose.
- Python para ejecutar scripts de preparación y pruebas.
- Conexión a Internet durante la construcción inicial.
- Navegador moderno.
- VS Code o editor equivalente.

Entorno utilizado durante las pruebas:

- Windows y PowerShell.
- Python 3.14.3 en el equipo anfitrión.
- Python 3.12 en los contenedores del backend.
- Docker Compose.
- Navegador Brave.

## 4. Instalación y ejecución

Abrir la carpeta del proyecto que contiene `compose.yaml`.

En una instalación nueva, generar la configuración local:

```powershell
py -3.14 backend/scripts/init_local_env.py
```

El archivo `.env` contiene las credenciales locales y no debe subirse al repositorio. Se conserva `.env.example` como referencia.

Iniciar el sistema:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps -a
```

Verificar la conectividad:

```powershell
py -3.14 backend/scripts/preflight_e3.py
```

En el primer arranque, Docker descarga las imágenes e instala dependencias.

El contenedor `vault-init` debe finalizar con código 0. Esta finalización es normal. MongoDB debe aparecer saludable y los demás servicios deben permanecer ejecutándose.

### Direcciones locales

| Recurso | Dirección |
|---|---|
| Aplicación web | http://127.0.0.1:8080 |
| Documentación API Gateway | http://127.0.0.1:8000/docs |
| Consola ActiveMQ | http://127.0.0.1:8161 |

No se requiere instalar MongoDB, Vault o ActiveMQ manualmente para este despliegue.

Para detener los contenedores sin eliminar los datos:

```powershell
docker compose down
```

No utilizar `docker compose down -v` salvo que se desee eliminar expresamente la base de datos de prueba.

## 5. Funcionalidades y recorrido de uso

1. Consultar el catálogo desde el menú.
2. Crear una cuenta ficticia desde el registro.
3. Iniciar sesión y consultar el perfil.
4. Agregar productos al carrito.
5. Seleccionar retiro o despacho.
6. Confirmar el pedido.
7. Consultar el historial del cliente.
8. Confirmar el pago simulado desde una cuenta administradora.
9. Consultar el estado actualizado y el comprobante comercial.

Inventory establece los precios oficiales. Orders registra la compra y calcula el total. Payments registra y administra la solicitud de pago.

Los pedidos incorporan un `codigo_compra` para controlar reintentos. MongoDB utiliza un índice de unicidad que evita la creación duplicada de pedidos bajo la misma clave de compra.

El API Gateway utiliza autenticación, introspección de tokens y controles de autorización. Los permisos no dependen únicamente de ocultar elementos del frontend.

## 6. Pruebas y resultados de Evaluación 3

### 6.1. Pruebas ejecutadas

El 23 de noviembre de 2026 se registraron los siguientes resultados:

| Prueba | Resultado observado |
|---|---|
| Preflight de conectividad | 5 aprobadas de 5 |
| Suite ampliada E3 | 24 aprobadas de 24 |
| Pruebas ampliadas fallidas | 0 |
| Pruebas ampliadas bloqueadas | 0 |
| Registro y autenticación | Confirmados |
| Creación de pedido desde frontend | Confirmada |
| Pago simulado | Confirmado |
| Persistencia de pedido y pago | Confirmada |
| Consumo de evento | Observado en MongoDB |

Estos resultados corresponden al entorno local y a las ejecuciones identificadas; no representan automáticamente la aprobación de toda la rúbrica.

### 6.2. Evidencias

Los registros generados se encuentran en:

```text
docs/evaluacion/evidencias/
├── preflight_20261123_192856.json
├── run_ampliada_20261123_203010.json
└── persistencia_pago_ORD-510247AA3E16.txt
```

El pedido manual de referencia fue:

- Pedido: `ORD-510247AA3E16`.
- Pago: `PAY-FE104807841F`.
- Producto: Shio Ramen.
- Total: $13.800.
- Resultado final: pedido y pago en estado `pagado`.
- Eventos consumidos observados: 1.

El campo `event_status` del pedido indicó `enviado_sin_confirmacion_de_consumo`. El consumo se corroboró mediante una consulta independiente de MongoDB, no mediante una confirmación del publicador.

### 6.3. Repetir pruebas

```powershell
py -3.14 backend/scripts/preflight_e3.py
py -3.14 backend/pruebas/pruebas_ampliadas_e3.py
```

Si falta `httpx`:

```powershell
py -3.14 -m pip install httpx==0.28.1
```

La suite ampliada solicita la contraseña administrativa configurada localmente. Cada ejecución puede crear nuevos registros ficticios y genera un reporte de evidencias independiente.

Para consultar la persistencia de un pedido existente:

```powershell
docker compose exec orders python -m backend.pruebas.verificar_persistencia_e3 --pedido ORD-510247AA3E16
```

La consulta anterior depende de que ese pedido exista en la base de datos local. En una instalación nueva debe crearse primero un pedido de prueba.

También están disponibles pruebas de integración, reglas del negocio, clientes API y verificaciones aisladas en `backend/pruebas/` y `frontend/tests/`.

## 7. Documentación de Evaluación 2 y Evaluación 3

Los principales documentos del expediente son:

| Archivo o carpeta | Contenido |
|---|---|
| `docs/evaluacion/INFORME_ARQUITECTURA.md` | Arquitectura, servicios y responsabilidades |
| `docs/evaluacion/INFORME_EVALUACION3.md` | Integración, pruebas, incidencias y conclusiones |
| `docs/evaluacion/PLAN_VALIDACION_E3.md` | Criterios y alcance de validación |
| `docs/evaluacion/PROTOCOLOS_AMPLIADOS_E3.md` | Protocolos de las pruebas |
| `docs/evaluacion/MATRIZ_TRAZABILIDAD_E3.csv` | Relación entre requisitos y pruebas |
| `docs/evaluacion/MATRIZ_AMPLIADA_E3.csv` | Cobertura y escenarios adicionales |
| `docs/evaluacion/REGISTRO_EJECUCIONES_E3.md` | Ejecuciones y resultados |
| `docs/evaluacion/evidencias/` | Evidencias generadas |
| `docs/evaluacion/CHECKLIST_E3_VIDEO.md` | Guía de grabación |
| `docs/arquitectura/` | Diagramas de arquitectura |
| `docs/uml/` | Diagramas UML editables |
| `docs/decisiones/` | Decisiones técnicas y aplicabilidad de componentes |

Las capturas y grabaciones deben identificarse con la ejecución y versión a la que corresponden. No se deben presentar resultados simulados como ejecuciones reales.

## 8. Limitaciones

La implementación corresponde a un entorno académico de desarrollo.

- Vault utiliza modo de desarrollo; no es adecuado para producción.
- El pago es simulado y no realiza cargos bancarios.
- El comprobante es comercial y no constituye boleta electrónica tributaria del SII.
- El envío de correos en modo DEMO no acredita recepción real ni existencia del buzón.
- El radio de despacho de 3 km se calcula mediante una aproximación en línea recta, no mediante rutas viales.
- La publicación directa por ActiveMQ no garantiza entrega transaccional fuerte ante todos los tipos de fallo.
- La suite automatizada no sustituye la evaluación manual en escritorio y móvil.

No se incorporan analítica externa ni gRPC porque no se identificó una necesidad justificada para estos componentes dentro del alcance adoptado. La decisión está documentada en `docs/decisiones/ADR_Analitica_y_Comunicacion.md`.

## 9. Uso de inteligencia artificial

Durante el desarrollo de Tokyo Noodles se utilizó **ChatGPT de OpenAI** como herramienta de apoyo técnico y documental.

Su utilización comprendió:

- Revisión y adaptación de propuestas de código.
- Apoyo en depuración de errores de Docker, configuración y microservicios.
- Propuesta y estructuración de casos de prueba.
- Organización y revisión de documentación técnica.
- Revisión de errores y mejoras de la interfaz de usuario.

El uso de IA fue asistido. Las propuestas se revisaron e integraron en el proyecto y se contrastaron con pruebas locales, solicitudes HTTP, registros de servicios, capturas de interfaz y consultas a MongoDB.

## 10. Seguridad y entrega

No deben incorporarse al repositorio:

- Archivo `.env` ni contraseñas locales.
- Tokens de autenticación, claves de Vault o claves API.
- Cookies o cabeceras sensibles.
- Bases de datos privadas o información personal real.
- Dependencias generadas, cachés o archivos temporales.
- Registros completos que expongan credenciales.

Se conserva `.env.example` para permitir configurar el proyecto en otro equipo.

El repositorio debe contener código fuente, Docker Compose, dependencias declaradas, documentación, matrices y evidencias depuradas.

La versión publicada en GitHub constituye el código entregable. La verificación reproducible requiere configurar secretos locales y ejecutar los protocolos indicados.