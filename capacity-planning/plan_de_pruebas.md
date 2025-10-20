# Plan de Pruebas de Carga - ANB Rising Stars Showcase

Este documento describe el plan de análisis de capacidad del sistema ANB Rising Stars Showcase, diseñado para medir la capacidad máxima que pueden soportar los componentes del sistema bajo diferentes escenarios de carga.

**Objetivo:** Ejecutar escenarios de prueba que permitan medir la capacidad máxima que pueden soportar algunos componentes del sistema, simulando el acceso, la carga, el estrés y la utilización de la aplicación.

---

## Documentación Completa en la Wiki

La documentación detallada del plan de pruebas, escenarios, ejecución y resultados se encuentra en la **Wiki de GitHub**:

### Plan de Pruebas

**[Plan de Pruebas de Carga](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Plan)**

Esta página incluye:
- Objetivos del análisis de capacidad
- Infraestructura de pruebas
- Herramientas utilizadas (k6, Prometheus, Grafana)
- Escenarios de prueba detallados
- Métricas evaluadas
- Procedimiento de ejecución paso a paso
- Criterios de éxito y fallo
- Estrategias de optimización

### Escenarios de Prueba

#### Escenario 1: Capacidad de la Capa Web

**[Escenario 1 - Capa Web (Usuarios Concurrentes)](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-1)**

**Objetivo:** Determinar el número de usuarios concurrentes (y RPS asociado) que la API de subida soporta cumpliendo SLOs.

**Pruebas ejecutadas:**
- Sanidad (Smoke Test): 5 VUs durante 1 minuto
- Escalamiento rápido (Ramp): 100 → 200 → 300 VUs
- Sostenida corta: 5 minutos al 80% de capacidad

**Resultados:**
- Capacidad máxima identificada
- Curvas de latencia vs usuarios concurrentes
- Throughput (RPS) sostenido
- Cuellos de botella identificados con evidencias

#### Escenario 2: Rendimiento de la Capa Worker

**[Escenario 2 - Worker (Videos/Minuto)](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-2)**

**Objetivo:** Medir cuántos videos por minuto procesa el/los worker(s) a distintos niveles de paralelismo y tamaños de archivo.

**Configuraciones evaluadas:**
- Tamaños de video: 50 MB, 100 MB
- Concurrencia: 1, 2, 4 workers
- Pruebas de saturación y sostenidas

**Resultados:**
- Throughput observado (videos/min)
- Tiempo medio de servicio por video
- Tabla de capacidad por configuración
- Puntos de saturación identificados

---

## Scripts de Prueba

Los scripts de k6 utilizados para las pruebas se encuentran en el directorio [`K6/`](../K6/):

### Escenario 1: Capa Web

- [`K6/1sanidad.js`](../K6/1sanidad.js) - Prueba de sanidad (5 VUs, 1 minuto)
- [`K6/2escalamiento.js`](../K6/2escalamiento.js) - Prueba de escalamiento (100/200/300 VUs)
- [`K6/3sostenidaCorta.js`](../K6/3sostenidaCorta.js) - Prueba sostenida (100 VUs, 5 minutos)

### Escenario 2: Worker

- Scripts de inyección directa a RabbitMQ (pendiente de documentar)

---

## Herramientas Utilizadas

### Generación de Carga

**k6 (Grafana k6)**
- Herramienta moderna de testing de performance
- Scripting en JavaScript ES6
- Métricas detalladas out-of-the-box
- Open source y altamente eficiente

**Justificación:** Se seleccionó k6 por la experiencia previa del equipo con la herramienta, su facilidad de uso, y su capacidad para generar reportes detallados de latencia y throughput. Aunque el documento de referencia sugiere Locust o JMeter, k6 es una alternativa superior en términos de performance y facilidad de scripting.

### Observabilidad

**Stack de Monitoreo:**
- **Prometheus:** Recolección de métricas de todos los servicios
- **Grafana:** Visualización de métricas en tiempo real
- **Loki:** Agregación y consulta de logs
- **Promtail:** Recolección automática de logs de contenedores

**Exportadores:**
- nginx-exporter (métricas de Nginx)
- pg-exporter (métricas de PostgreSQL)
- cAdvisor (métricas de contenedores Docker)

---

## Infraestructura de Pruebas

### Ambiente de Ejecución

**Sistema Operativo:** Windows 11
**Docker Desktop:** 4.x
**Recursos asignados:**
- CPU: 8 cores
- RAM: 8 GB
- Disco: 50 GB

### Servicios Evaluados

- **anb_api** (FastAPI) - API Core
- **worker** (Celery + FFmpeg) - Procesamiento asíncrono
- **rabbitmq** (RabbitMQ 3.10) - Message broker
- **anb-core-db** (PostgreSQL 15) - Base de datos
- **nginx** (Nginx 1.25) - Reverse proxy

---

## Criterios de Éxito y Fallo

### Escenario 1: Capa Web

**Capacidad Máxima:**
- p95 de endpoints ≤ 1s
- Errores (4xx evitables/5xx) ≤ 5%
- Sin resets/timeouts anómalos

**Criterios ajustados para Entrega 1:**
- p95 ≤ 5s (considerando procesamiento real sin mock)
- p99 ≤ 10s

### Escenario 2: Worker

**Capacidad Nominal:**
- Throughput sostenido (videos/min)
- Cola estable (tendencia ~0)
- Sin saturación de recursos

---

## Resultados y Conclusiones

Los resultados detallados de las pruebas, incluyendo:
- Gráficos de latencia vs usuarios concurrentes
- Tablas de capacidad por configuración
- Análisis de cuellos de botella con evidencias
- Recomendaciones de escalabilidad

Se encuentran documentados en las páginas de la Wiki:

- **[Escenario 1: Resultados Capa Web](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-1)**
- **[Escenario 2: Resultados Worker](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-2)**

---

## Estructura de Documentación

```
capacity-planning/
├── plan_de_pruebas.md          # Este archivo (overview y redirección a Wiki)
└── (futuros reportes)

K6/
├── 1sanidad.js                 # Smoke test
├── 2escalamiento.js            # Ramp-up test
└── 3sostenidaCorta.js          # Sustained load test

Wiki/
├── Pruebas-Plan                # Plan detallado
├── Pruebas-Escenario-1         # Resultados Capa Web
└── Pruebas-Escenario-2         # Resultados Worker
```

---

## Comandos de Ejecución

### Ejecutar Prueba de Sanidad

```bash
k6 run K6/1sanidad.js \
  -e BASE_URL=http://localhost:8080 \
  -e FILE_PATH=K6/testVideo.mp4 \
  -e ACCESS_TOKEN=<your-jwt-token>
```

### Ejecutar Prueba de Escalamiento

```bash
k6 run K6/2escalamiento.js \
  -e BASE_URL=http://localhost:8080 \
  -e FILE_PATH=K6/testVideo.mp4 \
  -e ACCESS_TOKEN=<your-jwt-token>
```

### Ejecutar Prueba Sostenida

```bash
k6 run K6/3sostenidaCorta.js \
  -e BASE_URL=http://localhost:8080 \
  -e FILE_PATH=K6/testVideo.mp4 \
  -e ACCESS_TOKEN=<your-jwt-token>
```

---

## Referencias

- [Wiki del Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki)
- [Plan de Pruebas Detallado](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Plan)
- [Arquitectura del Sistema](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Descripción)
- [Observabilidad](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Observabilidad)
- [Documentación de k6](https://k6.io/docs/)

---

**Última actualización:** Enero 2025
**Versión:** 1.0.0
