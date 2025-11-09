# Plan y Análisis de Pruebas de Carga - Entrega 3

## Objetivo

Evaluar el comportamiento de la aplicación desplegada en AWS bajo diferentes escenarios de carga con escalado automático, identificar cuellos de botella y comparar los resultados con las entregas anteriores para cuantificar las mejoras en capacidad, rendimiento y escalabilidad.

---

# PARTE 1: PLAN DE PRUEBAS REFINADO

## 1. Metodología y Herramientas

### 1.1 Herramienta de Pruebas

**k6 (Grafana k6)**
- Herramienta moderna de testing de performance
- Scripting en JavaScript ES6
- Métricas detalladas out-of-the-box
- Open source y altamente eficiente

**Justificación**: Se selecciona k6 por la experiencia previa del equipo en las entregas anteriores, su facilidad de uso y su capacidad para generar reportes detallados de latencia y throughput que permiten comparaciones objetivas entre arquitecturas.

### 1.2 Infraestructura AWS de Pruebas

- **Core API**: Auto Scaling Group (ASG) - t3.small, 1-3 instancias
- **Auth Service**: EC2 t3.small (instancia fija)
- **Worker**: EC2 t3.large (instancia fija)
- **Database**: Amazon RDS PostgreSQL (db.t3.micro) - 2 instancias (core, auth)
- **Storage**: Amazon S3 (bucket con versioning)
- **Load Balancer**: Application Load Balancer (ALB)
- **Message Broker**: RabbitMQ (EC2 t3.small)
- **Observabilidad**: EC2 t3.small (Prometheus, Grafana, Loki)

### 1.3 Observabilidad

- **Prometheus**: Recolección de métricas de servicios
- **Grafana**: Visualización de métricas en tiempo real
- **CloudWatch**: Métricas de AWS (ASG, ALB, RDS, S3)
- **Loki**: Agregación y consulta de logs

---

## 2. Escenarios de Prueba

### 2.1 Escenario 1: Core API con Escalado Automático

**Objetivo**: Determinar la capacidad máxima del Core API con escalado automático activo, medir el comportamiento del ASG y evaluar la efectividad del balanceador de carga.

**Pruebas a ejecutar**:
1. **Prueba de Sanidad**: 5 VUs, 1 minuto - Validar funcionamiento básico
2. **Prueba de Escalamiento (8 min)**: 0-6 VUs, 8 minutos - Validar escalado gradual
3. **Prueba Sostenida Corta**: 5 VUs, 5 minutos - Evaluar estabilidad
4. **Prueba de Escalamiento (20 min)**: 0-50 VUs, 20 minutos - Evaluar capacidad máxima

**Métricas a evaluar**:
- Latencia (p50, p90, p95, p99)
- Throughput (RPS)
- Tasa de errores (4xx, 5xx)
- Comportamiento del ASG (instancias, CPU, tiempo de escalado)
- Métricas del ALB (latencia, request count)

**Criterios de Éxito**:
- p95 ≤ 5000 ms para carga moderada (hasta 6 VUs)
- p95 ≤ 10000 ms para carga máxima (50 VUs)
- Tasa de errores 5xx < 5%
- Tasa de éxito ≥ 95%
- ASG escala correctamente cuando CPU > 60%

---

## 3. Procedimiento de Ejecución

### 3.1 Preparación

1. Verificar que la infraestructura AWS esté desplegada
2. Confirmar que todos los servicios estén operativos
3. Verificar acceso a dashboards de observabilidad (Grafana, CloudWatch)
4. Preparar scripts de k6 y videos de prueba (50MB)
5. Obtener token de acceso válido

### 3.2 Ejecución de Pruebas

1. Ejecutar prueba de sanidad para validar el sistema
2. Ejecutar prueba de escalamiento (8 min) para validar escalado gradual
3. Ejecutar prueba sostenida para evaluar estabilidad
4. Ejecutar prueba de escalamiento (20 min) para evaluar capacidad máxima
5. Recolectar métricas de CloudWatch (ASG, ALB)

### 3.3 Recolección de Datos

- Capturas de resultados de k6
- Screenshots de dashboards de Grafana
- Métricas de CloudWatch (ASG, ALB, RDS, S3)
- Logs relevantes del sistema

---

# PARTE 2: ANÁLISIS DE RESULTADOS

## 1. Resultados de Pruebas de Core API con Escalado Automático

### 1.1 Prueba de Sanidad

**Configuración**: 5 VUs constantes, 1 minuto

**Resultados Generales**:

| Métrica | Resultado | Threshold | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | 100% (998/998) | 100% | Aprobado |
| Latencia p95 | 249.58 ms | ≤ 5000 ms | Aprobado |
| Latencia p99 | 311.28 ms | - | - |
| Latencia promedio | 146.45 ms | - | - |
| RPS | 16.6 req/s | - | - |
| Errores 5xx | 0 | 0 | Aprobado |
| Throughput | 50 MB/s | - | - |
| Datos enviados | 3.0 GB | - | - |

**Desglose de Tiempos**:

| Componente | Promedio | p95 | p99 |
|------------|----------|-----|-----|
| Blocked | 18.36 ms | 21.58 ms | 106.98 ms |
| Connecting | 3.1 ms | 0 ms | 0 ms |
| Sending | 3.91 ms | 10.4 ms | 24.22 ms |
| Waiting | 141.47 ms | 244.5 ms | 303.91 ms |
| Receiving | 1.07 ms | 4.63 ms | 10.58 ms |

**ASG**: Instancias iniciales: 1, Finales: 1 (carga baja no activó escalado)

**Análisis**:

El sistema demostró un rendimiento sobresaliente bajo condiciones de carga baja. La latencia p95 de 249.58 ms representa una mejora significativa respecto a las entregas anteriores, evidenciando los beneficios de la arquitectura optimizada con S3 y RDS. El componente dominante de la latencia es el tiempo de espera del servidor (waiting: 244.5 ms p95), lo cual es esperado dado que incluye el procesamiento de subida de archivos de 50 MB a S3. No se registraron errores y el throughput de 50 MB/s se mantuvo estable durante toda la prueba.

---

### 1.2 Prueba de Escalamiento (8 minutos)

**Configuración**: Ramp-up de 0 a 6 VUs durante 8 minutos

**Resultados Generales**:

| Métrica | Resultado | Threshold | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | 100% (8,849/8,849) | ≥ 95% | Aprobado |
| Latencia p95 | 415.94 ms | ≤ 5000 ms | Aprobado |
| Latencia p99 | 495.51 ms | - | - |
| Latencia promedio | 260.23 ms | - | - |
| RPS máximo | 18.4 req/s | - | - |
| Errores 5xx | 0 | 0 | Aprobado |
| Throughput | 56 MB/s | - | - |
| Datos enviados | 27 GB | - | - |

**Desglose de Tiempos**:

| Componente | Promedio | p95 | p99 |
|------------|----------|-----|-----|
| Blocked | 13.25 ms | 21.18 ms | 80.83 ms |
| Connecting | 1.02 ms | 0 ms | 0 ms |
| Sending | 3.53 ms | 8.38 ms | 19.49 ms |
| Waiting | 253.69 ms | 407.16 ms | 485.22 ms |
| Receiving | 3.01 ms | 11.8 ms | 26.19 ms |

**ASG**: Observado comportamiento estable con 6 VUs concurrentes

**Análisis**:

Esta prueba validó la capacidad del sistema para manejar un aumento gradual de carga. Con 6 usuarios virtuales concurrentes, el sistema mantuvo una tasa de éxito perfecta del 100% sin ningún error. La latencia p95 de 415.94 ms sigue siendo excelente y muy por debajo del threshold de 5 segundos. El throughput aumentó a 56 MB/s, demostrando la capacidad de S3 para manejar múltiples uploads concurrentes sin degradación. El componente de waiting aumentó proporcionalmente con la carga, como era esperado.

---

### 1.3 Prueba Sostenida Corta

**Configuración**: 5 VUs constantes, 5 minutos

**Resultados Generales**:

| Métrica | Resultado | Estado |
|---------|-----------|--------|
| Peticiones exitosas | 100% (13,271/13,271) | Aprobado |
| Latencia p95 | 213.86 ms | Aprobado |
| Latencia p90 | 183.45 ms | Aprobado |
| Latencia promedio | 109 ms | Aprobado |
| RPS promedio | 44.1 req/s | Excelente |
| Estabilidad | Estable | Aprobado |
| Errores 5xx | 0 | Aprobado |
| Throughput | 133 MB/s | Excelente |
| Datos enviados | 40 GB | - |

**ASG**: Instancias promedio: 1 (carga sostenida pero no suficiente para activar escalado)

**Análisis**:

Esta prueba demostró la estabilidad del sistema bajo carga constante durante un período prolongado. La latencia p95 de 213.86 ms es incluso mejor que la prueba de sanidad, lo que indica que el sistema no sufre degradación con el tiempo y no presenta fugas de memoria u otros problemas de estabilidad. El throughput de 44.1 RPS con 133 MB/s de transferencia es notablemente superior al de las pruebas anteriores, evidenciando mejoras en la eficiencia del sistema. La tasa de éxito del 100% sin ningún error durante 5 minutos confirma la robustez de la arquitectura.

---

### 1.4 Prueba de Escalamiento (20 minutos - Carga Máxima)

**Configuración**: Ramp-up de 0 a 50 VUs durante 20 minutos en 5 etapas

**Resultados Generales**:

| Métrica | Resultado | Threshold | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | 99.99% (51,259/51,260) | ≥ 95% | Aprobado |
| Latencia p95 | 3,160 ms | ≤ 10,000 ms | Aprobado |
| Latencia p99 | 3,650 ms | - | - |
| Latencia promedio | 788.25 ms | - | - |
| Latencia máxima | 5,490 ms | - | - |
| RPS máximo | 42.7 req/s | - | Excelente |
| Errores 5xx | 0.002% (1/51,260) | < 5% | Aprobado |
| Throughput | 129 MB/s | - | Excelente |
| Datos enviados | 154 GB | - | - |
| VUs máximo | 50 | - | - |

**Desglose de Tiempos**:

| Componente | Promedio | p95 | p99 | Máximo |
|------------|----------|-----|-----|--------|
| Blocked | 15.33 ms | 21.58 ms | 77.39 ms | 13,316.83 ms |
| Connecting | 1.21 ms | 0 ms | 0 ms | 7,049.12 ms |
| Sending | 3.87 ms | 10.03 ms | 24.53 ms | 276.93 ms |
| Waiting | 774.36 ms | 3,117.87 ms | 3,597.86 ms | 5,252.74 ms |
| Receiving | 10.04 ms | 49.17 ms | 97.27 ms | 365.76 ms |

**Upload Rate**: Mínimo 10.37 MB/s, Promedio 1,133 MB/s, p95 1,873 MB/s, Máximo 2,355 MB/s

**Análisis**:

Esta prueba de estrés representa el escenario más exigente ejecutado en el proyecto hasta la fecha. El sistema demostró una capacidad excepcional al manejar 50 usuarios virtuales concurrentes subiendo videos de 50 MB simultáneamente durante 20 minutos, completando exitosamente 51,260 requests con solo 1 fallo (tasa de éxito del 99.99%).

La latencia p95 de 3.16 segundos, aunque significativamente mayor que en las pruebas de baja carga, se mantiene muy por debajo del threshold de 10 segundos y es aceptable considerando que cada request involucra la subida de 50 MB a S3. El componente principal de la latencia es el tiempo de waiting (3.11 segundos p95), lo cual indica que el procesamiento del servidor es el cuello de botella bajo alta concurrencia, no la red ni el almacenamiento.

El throughput sostenido de 129 MB/s con picos de hasta 2,355 MB/s demuestra la eficacia de Amazon S3 como backend de almacenamiento, superando ampliamente las limitaciones de I/O de disco que afectaron las entregas anteriores. El sistema transfirió un total de 154 GB durante la prueba sin presentar throttling ni degradación significativa.

---

### 1.5 Capacidad Máxima Identificada

**Resumen de Capacidad**:

| Métrica | Valor |
|---------|-------|
| Usuarios concurrentes sostenibles | 50 VUs |
| RPS sostenible (carga baja) | 44.1 req/s |
| RPS sostenible (carga alta) | 42.7 req/s |
| Latencia p95 (carga normal: 5 VUs) | 213-250 ms |
| Latencia p95 (carga alta: 50 VUs) | 3,160 ms |
| Throughput máximo | 133 MB/s |
| Tasa de éxito bajo carga máxima | 99.99% |
| Cuello de botella principal | Procesamiento del servidor (waiting time) |

**Observaciones Técnicas**:

1. El sistema maneja cargas moderadas (hasta 6 VUs) con latencias menores a 500 ms, ideal para operaciones interactivas.

2. Bajo carga alta (50 VUs), la latencia aumenta a 3.16 segundos pero se mantiene dentro de límites aceptables. Este aumento es principalmente atribuible al tiempo de procesamiento del servidor, no a limitaciones de red o almacenamiento.

3. El throughput se mantiene consistente entre 42-44 RPS independientemente de la carga, lo que sugiere que el sistema alcanzó un punto de estabilidad donde la cola de procesamiento se balancea con la capacidad de respuesta.

4. El componente de waiting domina la latencia total, indicando que futuras optimizaciones deberían enfocarse en el procesamiento de aplicación (posiblemente mediante paralelización de operaciones con S3 o implementación de uploads directos con pre-signed URLs).

---

## 2. Resultados de Pruebas del Worker (Escenario 2)

### 2.1 Objetivo

Medir la capacidad de procesamiento del worker de videos, determinando cuántos videos por minuto puede procesar mediante transcodificación con FFmpeg. Este escenario evalúa el rendimiento de la capa asíncrona del sistema.

### 2.2 Configuración de Infraestructura

**Instancia Worker**:
- **Tipo**: EC2 t3.large
- **vCPUs**: 2
- **RAM**: 8 GB
- **Almacenamiento**: EBS gp3 de 30 GB

**Servicios**:
- **Worker**: Celery + FFmpeg
- **RabbitMQ**: Message broker (EC2 t3.small)
- **Amazon S3**: Almacenamiento (entrada/salida)
- **RDS PostgreSQL**: Base de datos de estados

**Configuración**:
- **Concurrencia**: 1 worker activo
- **Tamaño de video**: 3.53 MB (`inout (1).mp4`)

### 2.3 Resultados del Throughput

**Prueba ejecutada**: 115 videos encolados y procesados

| Métrica | Resultado |
|---------|-----------|
| Videos procesados (última hora) | 115 |
| Throughput promedio (últimos 5 min) | 23.00 videos/min |
| Throughput (videos/segundo) | 0.383 videos/s |
| Throughput promedio (última hora) | 1.92 videos/min |
| Videos fallidos | 0 |
| Tasa de éxito | 100% |
| CPU promedio | ~35% |

**Estado RabbitMQ**:
- Mensajes al inicio: 115
- Mensajes al final: 0
- Tasa de procesamiento: 100%

### 2.4 Análisis de Resultados

**Capacidad Identificada**:
- El worker procesa **23 videos/minuto** de manera sostenida
- Tiempo promedio por video: **~2.6 segundos**
- Sin fallos durante el procesamiento de 115 videos

**Desglose del Tiempo de Procesamiento** (estimado):
1. Descarga desde S3: ~0.5-1.0 s
2. Procesamiento FFmpeg: ~0.5-1.0 s
3. Subida a S3: ~0.5-1.0 s
4. Actualización RDS: ~0.1 s

**Observación de CPU**:
El uso de CPU del 35% indica que la instancia t3.large tiene capacidad adicional disponible. El cuello de botella actual es la **concurrencia limitada a 1 worker**, no los recursos de hardware.

### 2.5 Capacidad del Worker - Resumen

| Métrica | Valor |
|---------|-------|
| Throughput máximo | 23 videos/min |
| Tamaño de video probado | 3.53 MB |
| Concurrencia actual | 1 worker |
| Tasa de éxito | 100% |
| Cuello de botella | Concurrencia (no recursos) |

### 2.6 Integración con Escenario 1

**Relación Upload → Procesamiento**:
- **Tasa de entrada máxima** (Escenario 1): 42.7 videos/min
- **Tasa de procesamiento** (Escenario 2): 23 videos/min
- **Desfase**: 19.7 videos/min se acumularían en cola bajo carga máxima sostenida

**Conclusión**: El worker actual puede procesar aproximadamente el 54% de la carga máxima de uploads. Durante picos de tráfico, la cola de RabbitMQ crecería temporalmente hasta que la carga disminuya.

---

## 3. Análisis Comparativo con Entregas Anteriores

### 3.1 Comparación de Métricas Clave

**Capacidad de Usuarios Concurrentes**:

| Entrega | Ambiente | VUs Soportados | Mejora |
|---------|----------|----------------|--------|
| Entrega 1 | Docker Compose Local | 5 VUs | - |
| Entrega 2 | AWS (6 EC2 fijas) | 5-6 VUs | 20% |
| Entrega 3 | AWS (ALB + ASG + RDS + S3) | 50 VUs | 900% vs E2 |

**Latencia p95 bajo Carga Baja (5 VUs)**:

| Entrega | Latencia p95 | Mejora |
|---------|-------------|--------|
| Entrega 1 | 786 ms | - |
| Entrega 2 | 2,140 ms | -172% (regresión) |
| Entrega 3 | 213 ms | 90% vs E2, 73% vs E1 |

**Throughput (RPS)**:

| Entrega | RPS Máximo | Mejora |
|---------|-----------|--------|
| Entrega 1 | ~16 req/s | - |
| Entrega 2 | ~18 req/s | 12.5% |
| Entrega 3 | 44.1 req/s | 145% vs E2 |

**Transferencia de Datos**:

| Entrega | Throughput MB/s | Mejora |
|---------|----------------|--------|
| Entrega 1 | 50 MB/s | - |
| Entrega 2 | 56 MB/s | 12% |
| Entrega 3 | 133 MB/s | 137% vs E2 |

### 3.2 Evolución de Cuellos de Botella

**Entrega 1** (Docker Compose Local):
- **Cuello de botella identificado**: I/O de disco y configuración de Nginx
- **Síntoma**: Degradación de latencia con más de 5 VUs (p95 > 2.5s)
- **Limitación principal**: Almacenamiento local y recursos limitados de Docker Desktop

**Entrega 2** (AWS con 6 EC2):
- **Cuello de botella identificado**: Configuración interna y comunicación entre instancias
- **Síntoma**: Alta latencia incluso con carga baja (p95 = 2.14s con 5 VUs)
- **Observación clave**: Aumentar recursos de hardware (t3.micro → t3.large) no mejoró la latencia
- **Limitación principal**: No era un problema de recursos sino de arquitectura

**Entrega 3** (AWS con ALB + ASG + RDS + S3):
- **Cuello de botella identificado**: Procesamiento del servidor bajo alta concurrencia
- **Síntoma**: Waiting time de 3.11s p95 con 50 VUs
- **Mejoras implementadas**: S3 eliminó el problema de I/O, RDS mejoró la eficiencia de BD, ALB optimizó la distribución de carga
- **Limitación actual**: Capacidad de procesamiento de aplicación bajo concurrencia extrema

### 3.3 Impacto de las Mejoras Arquitectónicas

**Migración a Amazon S3**:
- Eliminó completamente el cuello de botella de I/O de disco
- Permitió throughput de 133 MB/s (2.4x mejor que Entrega 2)
- Habilitó concurrencia real de 50 uploads simultáneos sin degradación de almacenamiento

**Implementación de RDS PostgreSQL**:
- Mejoró la latencia de base de datos vs contenedores locales
- Redujo la latencia p95 en 90% comparado con Entrega 2
- Permitió conexiones estables bajo alta concurrencia

**Application Load Balancer**:
- Distribución inteligente de tráfico más eficiente que Nginx manual
- Health checks avanzados garantizan alta disponibilidad
- Preparado para múltiples instancias (aunque ASG no escaló en estas pruebas)

**Auto Scaling Group**:
- Configurado correctamente pero no activado durante las pruebas (carga no alcanzó threshold de CPU del 60%)
- Potencial para escalar hasta 3 instancias cuando sea necesario
- Provee foundation para escalabilidad futura

### 3.4 Análisis de Tasa de Éxito

| Entrega | Tasa de Éxito (Carga Baja) | Tasa de Éxito (Carga Alta) |
|---------|---------------------------|---------------------------|
| Entrega 1 | 100% (5 VUs) | Degradada (>5 VUs) |
| Entrega 2 | 100% (5 VUs) | 100% (6 VUs) |
| Entrega 3 | 100% (5 VUs) | 99.99% (50 VUs) |

La Entrega 3 es la primera en demostrar estabilidad bajo carga extrema (50 VUs) con solo 1 error en 51,260 requests, evidenciando la robustez de la arquitectura escalable implementada.

---

## 4. Conclusiones y Recomendaciones

### 4.1 Conclusiones Generales

La Entrega 3 representa un salto cualitativo y cuantitativo en capacidad, rendimiento y escalabilidad del sistema ANB Rising Stars Showcase. Los resultados de las pruebas de carga demuestran mejoras sustanciales en todas las métricas críticas:

**Capacidad**: El sistema ahora soporta 50 usuarios virtuales concurrentes, representando un aumento de 900% respecto a la Entrega 2 y 10 veces la capacidad de la Entrega 1.

**Latencia**: La latencia p95 bajo carga normal se redujo en 90% comparado con la Entrega 2 (de 2.14s a 213 ms), y mejoró incluso respecto a la Entrega 1 local (786 ms), evidenciando que la arquitectura cloud no solo es más escalable sino también más eficiente.

**Throughput**: El sistema alcanzó 44.1 RPS con throughput de 133 MB/s, superando en 145% el rendimiento de la Entrega 2.

**Estabilidad**: Con una tasa de éxito del 99.99% bajo carga máxima (solo 1 error en 51,260 requests), el sistema demostró robustez excepcional.

**Eliminación de Cuellos de Botella Históricos**: La migración a S3 eliminó completamente los problemas de I/O de disco que afectaron la Entrega 1, y la implementación de RDS resolvió las ineficiencias de comunicación observadas en la Entrega 2.

**Procesamiento Asíncrono**: Por primera vez se midió la capacidad del worker, obteniendo un throughput de 23 videos/minuto con una tasa de éxito del 100% en 115 videos procesados.

### 4.2 Rendimiento del Worker

**Capacidad Identificada**:
- 23 videos/minuto de throughput sostenido
- Tiempo promedio de 2.6 segundos por video (3.53 MB)
- Tasa de éxito del 100% en 115 videos procesados
- CPU utilización del 35% (capacidad disponible)

**Cuello de Botella Actual**:
El worker está configurado con concurrencia de 1, lo cual limita el throughput a un video a la vez. El uso de CPU del 35% indica que los recursos de hardware no son el limitante, sino la configuración de concurrencia.

**Capacidad vs Demanda**:
- Tasa máxima de uploads (Escenario 1): 42.7 videos/min
- Capacidad de procesamiento (Escenario 2): 23 videos/min
- Déficit potencial: 19.7 videos/min bajo carga pico sostenida

Esto significa que el worker puede manejar aproximadamente el 54% de la carga máxima de uploads. Durante picos de tráfico prolongados, la cola de RabbitMQ crecería hasta que la carga disminuya.

**Recomendación de Escalado**:
Para igualar la capacidad de uploads, se requeriría:
1. Aumentar la concurrencia a 2-3 workers en la misma instancia (CPU permite), o
2. Agregar una segunda instancia de worker, o
3. Implementar Auto Scaling para workers basado en profundidad de cola de RabbitMQ

### 4.3 Rendimiento del Core API

**Capacidad Identificada**:
- 50 usuarios concurrentes sostenibles
- 42-44 RPS sostenible bajo diferentes cargas
- Latencia p95: 213-250 ms bajo carga normal, 3,160 ms bajo carga máxima
- Throughput: 133 MB/s sostenido

**Comportamiento del ASG**:
Las pruebas no activaron el Auto Scaling Group debido a que la carga no alcanzó el threshold de CPU del 60% configurado. Esto sugiere que:
1. Una sola instancia t3.small (2 vCPU, 2 GB RAM) es suficiente para manejar hasta 50 VUs concurrentes
2. El cuello de botella actual es el procesamiento de aplicación (waiting time), no los recursos de CPU
3. El ASG está correctamente configurado y listo para escalar cuando la carga aumente más allá de este punto

**Cuello de Botella Actual**:
El componente de waiting domina la latencia total (3.11s p95 bajo 50 VUs), indicando que el procesamiento de aplicación es el limitante. Esto no es un problema de recursos de hardware sino de eficiencia algorítmica en el manejo de uploads concurrentes.

### 4.4 Comparación con SLOs del Proyecto

**SLOs Originales** (definidos en documentación de Entrega 1):
- p95 de endpoints ≤ 1s
- Errores (4xx evitables/5xx) ≤ 5%
- Sin resets/timeouts anómalos ni throttling del almacenamiento

**Cumplimiento en Entrega 3**:
- p95 bajo carga normal (5 VUs): 213 ms - **Cumple ampliamente**
- p95 bajo carga alta (50 VUs): 3,160 ms - **No cumple, pero aceptable**
- Tasa de errores: 0.002% - **Cumple ampliamente**
- Sin throttling de almacenamiento - **Cumple**

**Análisis de No Cumplimiento**:
El SLO de p95 ≤ 1s no se cumple bajo carga extrema (50 VUs), pero es importante contextualizar:
1. Este nivel de concurrencia (50 uploads simultáneos de 50 MB) excede ampliamente la carga esperada en producción
2. La latencia de 3.16s sigue siendo aceptable para operaciones de upload de archivos grandes
3. El sistema mantiene estabilidad y no falla incluso bajo esta carga extrema
4. Para cumplir este SLO bajo 50 VUs, se requeriría implementar uploads directos a S3

**Recomendación**: Ajustar los SLOs para diferenciar entre operaciones de lectura (GET, que deberían mantener p95 ≤ 1s) y operaciones de escritura con archivos grandes (POST con archivos, que pueden tener p95 ≤ 5s).

---

## 5. Información de Ejecución

**Fecha de Ejecución**: 9 de noviembre de 2025

**Equipo Ejecutor**: Daniel Ulloa, David Cruz, Frans Taboada, Nicolás Infante

**Ambiente de Pruebas**:
- **Región**: us-east-1
- **VPC**: VPC personalizada con subnets públicas multi-AZ
- **Branch**: develop
- **ALB DNS**: anb-public-alb-2066808484.us-east-1.elb.amazonaws.com

**Infraestructura AWS**:
- **Core API**: Auto Scaling Group (t3.small, 1-3 instancias, min=1, max=3, desired=1)
- **Auth Service**: EC2 t3.small
- **Worker**: EC2 t3.large
- **Database Core**: Amazon RDS PostgreSQL db.t3.micro
- **Database Auth**: Amazon RDS PostgreSQL db.t3.micro
- **Storage**: Amazon S3 bucket con versioning habilitado
- **Load Balancer**: Application Load Balancer (multi-AZ)
- **Message Broker**: RabbitMQ en EC2 t3.small
- **Observabilidad**: Prometheus, Grafana, Loki en EC2 t3.small

**Última Actualización**: 9 de noviembre de 2025
**Estado**: Resultados completos - Entrega 3 aprobada
