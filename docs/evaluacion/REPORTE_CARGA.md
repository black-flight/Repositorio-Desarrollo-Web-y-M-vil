# Reporte de rendimiento - Tokyo Noodles

- **Fecha y hora local:** 2026-11-09 20:26:22 -0300
- **Entorno:** Windows 11; Python 3.14.3; 16 procesadores logicos.
- **Topologia:** API Gateway en `127.0.0.1:8000` y microservicios/GraphQL en loopback; MongoDB y Vault locales.
- **Concurrencia:** 6 clientes concurrentes (hilos).
- **Solicitudes medidas:** 160; calentamiento: 8 (excluidas).
- **Carga:** consultas de catalogo, listado de pedidos, pedido propio y resumen GraphQL; proporcion 25 % cada una.
- **Datos:** usuarios y pedidos ficticios persistidos previamente; solo solicitudes de lectura durante la medicion.
- **Alcance:** medicion local de laboratorio, no una proyeccion certificada de trafico de produccion.

## Indicadores medidos

| Indicador | Resultado |
|---|---:|
| Duracion total | 114.73 s |
| Solicitudes | 160 |
| Concurrencia | 6 |
| Throughput | 1.39 solicitudes/s |
| Latencia media | 4279.35 ms |
| Latencia mediana | 4106.78 ms |
| Latencia p95 | 5690.38 ms |
| Latencia maxima | 6070.39 ms |
| Errores funcionales o HTTP | 0 (0.00 %) |

## Desglose por operacion

| Operacion | Solicitudes | p95 (ms) | Errores |
|---|---:|---:|---:|
| Catalogo | 40 | 4412.89 | 0 |
| Listado de pedidos | 40 | 4693.27 | 0 |
| Pedido propio | 40 | 4625.83 | 0 |
| Resumen GraphQL | 40 | 6026.94 | 0 |

## Recursos del equipo de laboratorio

- **CPU acumulada por procesos Python/Node detectados:** +115.766 segundos de CPU durante la medicion.
- **CPU aproximada sobre capacidad logica del equipo:** 6.31 %.
- **Memoria agregada al inicio:** 359.8 MiB.
- **Memoria agregada al final:** 430.5 MiB.
- **Metodo:** instantaneas de `Get-Process` (Python y Node.js) antes y despues.
- **Limitacion de atribucion:** cifras agregadas; pueden incluir otros procesos Python/Node. Memoria instantanea, no pico.

## Codigos y respuestas observados

| Codigo o error | Cantidad |
|---|---:|
| 200 | 160 |


## Criterios operativos de referencia

Los siguientes valores se utilizan como referencias cuantitativas para interpretar las mediciones del entorno local.

| Indicador | Referencia de laboratorio | Valor observado |
|---|---:|---:|
| Latencia p95 | 1.000 ms o menos | 5.690,38 ms |
| Throughput | 8 solicitudes/s o más | 1,39 solicitudes/s |
| Errores HTTP o funcionales | 1 % o menos | 0,00 % |

La ejecución registrada procesó 160 solicitudes de lectura con seis clientes concurrentes. No se registraron errores HTTP ni funcionales durante el tramo medido.

La latencia y el throughput observados se presentan como mediciones del entorno local. Su interpretación depende del hardware, la configuración de los servicios, las dependencias y las características de la carga utilizada.

## Interpretacion

Los indicadores anteriores corresponden unicamente a la ejecucion registrada. No permiten inferir capacidad maxima de produccion ni comparar tecnologias sin una prueba A/B equivalente.
Las decisiones de comunicacion y separacion se documentan en `docs/decisiones/ADR_Analitica_y_Comunicacion.md`.

## Reproduccion

Desde la raiz del repositorio y con todos los servicios encendidos:

```powershell
python backend/pruebas/prueba_carga.py
```

No se registran contrasenas ni tokens en este informe.