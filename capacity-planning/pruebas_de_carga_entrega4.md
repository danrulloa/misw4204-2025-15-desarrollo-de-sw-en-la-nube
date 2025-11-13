# Plan y Análisis de Pruebas de Carga - Entrega 4

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
