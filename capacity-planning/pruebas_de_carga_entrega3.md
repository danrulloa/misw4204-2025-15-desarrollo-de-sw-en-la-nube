# Plan y Análisis de Pruebas de Carga - Entrega 3

## Objetivo

Evaluar el comportamiento de la aplicación desplegada en AWS bajo diferentes escenarios de carga con escalado automático, identificar cuellos de botella, y verificar la calidad del código mediante análisis estático.

---

# PARTE 1: PLAN DE PRUEBAS REFINADO

## 1. Metodología y Herramientas

### 1.1 Herramienta de Pruebas

**k6 (Grafana k6)**
- Herramienta moderna de testing de performance
- Scripting en JavaScript ES6
- Métricas detalladas out-of-the-box
- Open source y altamente eficiente

**Justificación**: Se selecciona k6 por la experiencia previa del equipo, su facilidad de uso, y su capacidad para generar reportes detallados de latencia y throughput.

### 1.2 Infraestructura AWS de Pruebas

- **Core API**: Auto Scaling Group (ASG) - t3.small, 1-3 instancias
- **Worker**: EC2 t3.large
- **Database**: Amazon RDS PostgreSQL (db.t3.micro) - 2 instancias (core, auth)
- **Storage**: Amazon S3
- **Load Balancer**: Application Load Balancer (ALB)
- **Message Broker**: RabbitMQ (EC2 t3.small)

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
2. **Prueba de Escalamiento**: Ramp-up progresivo - Activar escalado automático
3. **Prueba Sostenida**: Carga constante - Evaluar estabilidad

**Métricas a evaluar**:
- Latencia (p50, p95, p99)
- Throughput (RPS)
- Tasa de errores (4xx, 5xx)
- Comportamiento del ASG (instancias, CPU, tiempo de escalado)
- Métricas del ALB (latencia, request count)

**Criterios de Éxito**:
- p95 ≤ 2000 ms (considerando procesamiento real)
- Tasa de errores 5xx = 0%
- Tasa de éxito ≥ 95%
- ASG escala correctamente cuando CPU > 60%

### 2.2 Escenario 2: Worker de Procesamiento de Videos

**Objetivo**: Medir el throughput del worker procesando videos de diferentes tamaños y evaluar la capacidad de procesamiento.

**Pruebas a ejecutar**:
1. **Throughput básico**: Procesar videos de tamaño estándar
2. **Diferentes tamaños**: Evaluar rendimiento con videos pequeños, medianos y grandes
3. **Saturación**: Identificar capacidad máxima y puntos de saturación

**Métricas a evaluar**:
- Throughput (videos/minuto)
- Tiempo promedio de procesamiento por video
- Uso de CPU y memoria
- Estado de cola de RabbitMQ
- Operaciones S3 (descargas y subidas)

**Criterios de Éxito**:
- Throughput sostenido medible
- Cola de RabbitMQ estable (sin crecimiento indefinido)
- Sin errores en el procesamiento

### 2.3 Análisis de Calidad de Código

**Objetivo**: Verificar la calidad del código mediante análisis estático con SonarQube.

**Servicios a analizar**:
- Core API
- Auth Service
- Worker

**Métricas a evaluar**:
- Quality Gate (PASSED/FAILED)
- Cobertura de código
- Bugs, vulnerabilidades, code smells
- Deuda técnica

**Criterios de Éxito**:
- Quality Gate: PASSED en todos los servicios
- Cobertura ≥ 80%
- Sin bugs críticos o bloqueantes

---

## 3. Procedimiento de Ejecución

### 3.1 Preparación

1. Verificar que la infraestructura AWS esté desplegada
2. Confirmar que todos los servicios estén operativos
3. Verificar acceso a dashboards de observabilidad (Grafana, CloudWatch)
4. Preparar scripts de k6 y videos de prueba

### 3.2 Ejecución de Pruebas

1. Ejecutar prueba de sanidad para validar el sistema
2. Ejecutar prueba de escalamiento y monitorear comportamiento del ASG
3. Ejecutar prueba sostenida para evaluar estabilidad
4. Ejecutar pruebas del worker con diferentes configuraciones
5. Recolectar métricas de SonarQube

### 3.3 Recolección de Datos

- Capturas de resultados de k6
- Screenshots de dashboards de Grafana
- Métricas de CloudWatch (ASG, ALB, RDS, S3)
- Reportes de SonarQube
- Logs relevantes del sistema

---

# PARTE 2: ANÁLISIS DE RESULTADOS

## 1. Resultados de Pruebas de Core API con Escalado Automático

### 1.1 Prueba de Sanidad

**Configuración**: 5 VUs, 1 minuto

| Métrica | Resultado | Objetivo | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | _[COMPLETAR]_ % | 100% | ✅/❌ |
| Latencia p95 | _[COMPLETAR]_ ms | ≤ 1000 ms | ✅/❌ |
| RPS | _[COMPLETAR]_ | - | - |
| Errores 5xx | _[COMPLETAR]_ | 0 | ✅/❌ |

**ASG**: Instancias iniciales: _[COMPLETAR]_, Finales: _[COMPLETAR]_

**Evidencias**: _[URL capturas k6, Grafana, CloudWatch]_

---

### 1.2 Prueba de Escalamiento

**Configuración**: Ramp-up _[COMPLETAR]_ → _[COMPLETAR]_ VUs, _[COMPLETAR]_ minutos

| Métrica | Resultado | Objetivo | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | _[COMPLETAR]_ % | ≥ 95% | ✅/❌ |
| Latencia p95 | _[COMPLETAR]_ ms | ≤ 2000 ms | ✅/❌ |
| RPS máximo | _[COMPLETAR]_ | - | - |
| Errores 5xx | _[COMPLETAR]_ | 0 | ✅/❌ |

**Comportamiento del ASG**:
- Instancias iniciales: _[COMPLETAR]_
- Instancias máximas: _[COMPLETAR]_
- Tiempo hasta escalado: _[COMPLETAR]_ minutos
- CPU promedio máxima: _[COMPLETAR]_ %

**Evidencias**: _[URL capturas k6, gráficos ASG, CloudWatch]_

---

### 1.3 Prueba Sostenida

**Configuración**: _[COMPLETAR]_ VUs, _[COMPLETAR]_ minutos

| Métrica | Resultado | Objetivo | Estado |
|---------|-----------|----------|--------|
| Peticiones exitosas | _[COMPLETAR]_ % | ≥ 95% | ✅/❌ |
| Latencia p95 | _[COMPLETAR]_ ms | ≤ 2000 ms | ✅/❌ |
| RPS promedio | _[COMPLETAR]_ | - | - |
| Estabilidad | _[Estable/Degradación]_ | Estable | ✅/❌ |

**ASG**: Instancias promedio: _[COMPLETAR]_, ¿Mantuvo estabilidad?: _[Sí/No]_

**Evidencias**: _[URL capturas, dashboards]_

---

### 1.4 Capacidad Máxima Identificada

- Usuarios concurrentes sostenibles: _[COMPLETAR]_
- RPS sostenible: _[COMPLETAR]_
- Latencia p95 en carga máxima: _[COMPLETAR]_ ms
- Cuello de botella principal: _[CPU/RDS/S3/Red]_

---

## 2. Pruebas de Worker

### 2.1 Throughput del Worker

**Configuración**: Videos de _[COMPLETAR]_ MB, _[COMPLETAR]_ videos procesados

| Métrica | Resultado |
|---------|-----------|
| Throughput (videos/min) | _[COMPLETAR]_ |
| Tiempo promedio por video | _[COMPLETAR]_ minutos |
| Videos fallidos | _[COMPLETAR]_ |
| CPU promedio | _[COMPLETAR]_ % |

**RabbitMQ**: Mensajes en cola al inicio: _[COMPLETAR]_, Final: _[COMPLETAR]_

**Evidencias**: _[URL dashboards Grafana, RabbitMQ]_

---

### 2.2 Diferentes Tamaños de Video

| Tamaño | Throughput (videos/min) | Tiempo Promedio (min) | CPU Promedio (%) |
|--------|------------------------|----------------------|------------------|
| _[PEQUEÑO]_ MB | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ |
| _[MEDIANO]_ MB | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ |
| _[GRANDE]_ MB | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ |

---

### 2.3 Capacidad del Worker

- Throughput máximo: _[COMPLETAR]_ videos/minuto
- Tamaño de video óptimo: _[COMPLETAR]_ MB
- Cuello de botella principal: _[CPU/FFmpeg/S3/Red]_

---

## 3. Análisis de Calidad de Código - SonarQube

### 3.1 Resultados por Servicio

| Servicio | Quality Gate | Cobertura | Bugs | Vulnerabilidades | Code Smells | Deuda Técnica |
|----------|--------------|-----------|------|------------------|-------------|---------------|
| Core API | _[PASSED/FAILED]_ | _[COMPLETAR]_ % | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ h |
| Auth Service | _[PASSED/FAILED]_ | _[COMPLETAR]_ % | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ h |
| Worker | _[PASSED/FAILED]_ | _[COMPLETAR]_ % | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ | _[COMPLETAR]_ h |

**Issues Críticos Principales**:
1. _[COMPLETAR]_
2. _[COMPLETAR]_
3. _[COMPLETAR]_

**Evidencias**: _[URL SonarQube]_

---

## 4. Conclusiones y Recomendaciones

### 4.1 Rendimiento

**Core API**:
- Capacidad identificada: _[COMPLETAR]_ usuarios concurrentes, _[COMPLETAR]_ RPS
- ¿ASG escala correctamente?: _[Sí/No]_
- Cuello de botella: _[COMPLETAR]_

**Worker**:
- Throughput máximo: _[COMPLETAR]_ videos/minuto
- Cuello de botella: _[COMPLETAR]_

### 4.2 Calidad de Código

- Quality Gate: _[PASSED/FAILED]_ en todos los servicios
- Cobertura promedio: _[COMPLETAR]_ %
- Áreas de mejora: _[COMPLETAR]_

### 4.3 Recomendaciones

**Corto Plazo**:
1. _[COMPLETAR]_
2. _[COMPLETAR]_

**Mediano/Largo Plazo**:
1. _[COMPLETAR]_
2. _[COMPLETAR]_

---

## 5. Información de Ejecución

**Fecha**: _[COMPLETAR]_

**Ejecutado por**: _[COMPLETAR]_

**Ambiente**: Región _[COMPLETAR]_, VPC _[COMPLETAR]_, Commit _[COMPLETAR]_

**Notas**: _[COMPLETAR]_

---

**Versión**: 1.0.0
