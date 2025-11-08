# Pruebas de Carga y Calidad - Entrega 3

## Objetivo

Evaluar el comportamiento de la aplicación desplegada en AWS bajo diferentes escenarios de carga con escalado automático, identificar cuellos de botella, y verificar la calidad del código mediante análisis estático.

---

## Configuración de Infraestructura

**Herramienta**: k6

**Infraestructura AWS**:
- Core API: Auto Scaling Group (ASG) - t3.small, 1-3 instancias
- Worker: EC2 t3.large
- Database: Amazon RDS PostgreSQL (db.t3.micro)
- Storage: Amazon S3
- Load Balancer: Application Load Balancer (ALB)
- Message Broker: RabbitMQ (EC2 t3.small)

---

## 1. Pruebas de Core API con Escalado Automático

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
