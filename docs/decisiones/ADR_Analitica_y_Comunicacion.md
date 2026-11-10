# Registro de decisión arquitectónica — Analítica y comunicación interna

**Sistema:** Tokyo Noodles
**Integrante:** Patricio Frez
**Fecha del documento:** 09 de noviembre de 2026
**Componentes relacionados:** API Gateway, Inventory, Orders, Clients, Payments y GraphQL Gateway

## 1. Propósito

Este documento registra los criterios utilizados para organizar la comunicación entre servicios y determinar en qué circunstancias tendría sentido separar el procesamiento analítico. Describe las alternativas técnicas consideradas y la organización utilizada en el backend.

## 2. Contexto técnico

Tokyo Noodles utiliza servicios HTTP con mensajes JSON para operaciones de catálogo, autenticación, clientes, pedidos y solicitudes de pago. Inventory, Orders, Clients y Payments administran sus propios datos en MongoDB. El API Gateway centraliza la entrada de solicitudes y el GraphQL Gateway privado compone una lectura a partir de Orders e Inventory.

El catálogo inicial contiene diez productos. Las operaciones implementadas intercambian documentos JSON de tamaño acotado. La lectura agregada `resumenPedido` consulta un pedido y la información actual del catálogo sin transferir una secuencia continua de eventos.

El escenario de carga documentado en este repositorio ejecuta 160 solicitudes de lectura con seis clientes concurrentes. Se trata de una carga sintética definida para el entorno local y no de una estadística de usuarios reales. Las métricas obtenidas se guardan por separado al ejecutar el script.

## 3. Necesidades y caracterización

| Dimensión | Escenario documentado | Origen de la información |
|---|---|---|
| Operaciones | Lecturas del catálogo, pedidos y resumen GraphQL | Contratos HTTP implementados |
| Formato | JSON sobre HTTP | Implementación de servicios |
| Concurrencia de la medición | Seis trabajadores concurrentes | Configuración del script de carga |
| Número de solicitudes | 160, distribuidas entre cuatro operaciones | Configuración del script de carga |
| Contenido transaccional | Productos, pedidos, estados y pagos | Modelo funcional implementado |
| Streaming | No utilizado en los contratos descritos | Diseño de los endpoints actuales |
| Datos personales | Clientes, pedidos y pagos restringidos | Controles de identidad y propiedad |
| Procesamiento analítico | No existe un servicio analítico independiente | Inventario de componentes del proyecto |

### Referencias cuantitativas de la medición local

Se declaran tres valores orientativos **para contrastar los resultados de la prueba local**:

- Latencia p95: referencia de 1.000 ms por solicitud.
- Throughput: referencia de 8 solicitudes completadas por segundo.
- Proporción de errores funcionales o HTTP: referencia de 1 % como máximo.

La comparación se interpreta de forma descriptiva; una sola ejecución local no acredita capacidad de producción.

## 4. Procesamiento analítico

### Alternativa A: servicio privado de analítica

Un servicio independiente podría consolidar ventas por período, estadísticas de productos y otros informes. Requeriría una fuente de actualización, reglas de consistencia, control de acceso y recursos adicionales para ejecutar las agregaciones.

### Alternativa B: conservar las operaciones de lectura en los servicios actuales

Inventory y Orders pueden responder a sus propios contratos, y GraphQL combina información cuando una consulta necesita datos de más de un servicio. Esta alternativa mantiene la propiedad de los datos en cada subsistema y no agrega un almacén analítico para las consultas descritas.

### Organización utilizada

La implementación actual mantiene las operaciones transaccionales en sus cuatro microservicios y las consultas compuestas en GraphQL. No dispone de un subsistema analítico separado. Los posibles informes históricos y su volumen deberán caracterizarse con datos propios antes de elegir una arquitectura de agregación especializada.

## 5. Comunicación entre servicios

### Alternativa A: REST/HTTP y JSON

Permite reutilizar FastAPI y HTTPX, contratos ya presentes y reglas de autorización verificables con solicitudes HTTP. Se emplean tiempos de espera y credenciales de integración entre procesos.

### Alternativa B: gRPC unary

Utiliza archivos `.proto`, interfaces tipadas y llamadas RPC. Su incorporación requeriría clientes y servidores adicionales y la definición de autenticación por método, límites y tratamiento de errores.

### Alternativa C: gRPC streaming

Permite transferencias continuas de mensajes. Es una opción técnica para flujos persistentes de eventos o telemetría, distintos de las consultas puntuales descritas para el backend.

### Organización utilizada

El backend implementado se comunica mediante REST/HTTP con JSON. El GraphQL Gateway privado proporciona composición de consultas; no reemplaza la lógica transaccional. No se utiliza gRPC en los contratos actuales porque no se ha definido un intercambio tipado de alta frecuencia ni un flujo de streaming entre componentes.

La selección corresponde a los contratos y patrones de comunicación utilizados actualmente.

## 6. Procedimiento de medición

**Archivo:** `backend/pruebas/prueba_carga.py`
**Salida generada:** `docs/evaluacion/REPORTE_CARGA.md`

La ejecución utiliza una cuenta de prueba con pedidos previamente registrados. Efectúa autenticación fuera del tramo medido, verifica los contratos, realiza peticiones de calentamiento y después envía 160 solicitudes concurrentes repartidas entre las cuatro operaciones de lectura.

El reporte contiene fecha, sistema operativo, versión de Python, cantidad de solicitudes, duración, throughput, latencia media, mediana, p95, máxima, errores y códigos de respuesta. En Windows también intenta registrar muestras agregadas de CPU y memoria de procesos Python y Node.js; pueden incluir otros procesos de esos nombres y no representan exclusivamente el backend.

Para ejecutar desde la raíz del repositorio:

```powershell
python backend/pruebas/prueba_carga.py
```

La prueba no envía contraseñas ni tokens al informe. Los resultados solo se deben describir como observados después de ejecutar el script.

## 7. Consecuencias técnicas

**Características de la organización actual:** se reutilizan contratos HTTP, se conserva la autoridad de cada servicio sobre sus datos y la agregación se concentra en una interfaz de consulta.

**Factores a observar:** una consulta compuesta depende de otros servicios; la comunicación HTTP introduce tiempos de red y las agregaciones históricas pueden consumir recursos de los sistemas transaccionales.

**Condiciones para reconsiderar el diseño:** crecimiento de los volúmenes medidos, reportes frecuentes de alto costo, eventos internos continuos, objetivos de latencia distintos o una comparación de protocolos que muestre diferencias relevantes en el entorno real.

## 8. Referencias internas

- `README.md`: instalación, componentes y contratos.
- `docs/arquitectura/TokyoNoodles.dsl`: vista de arquitectura.
- `docs/uml/UML_Gateway.drawio`: políticas y dependencias del Gateway.
- `backend/pruebas/prueba_carga.py`: procedimiento de medición.
- `docs/evaluacion/REPORTE_CARGA.md`: valores registrados en cada ejecución.
