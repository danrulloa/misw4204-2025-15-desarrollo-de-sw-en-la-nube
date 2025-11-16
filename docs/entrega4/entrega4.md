# Entrega 4: Escalabilidad en la Capa Batch/Worker

**Fecha**: 16 de Noviembre de 2025
**Curso**: MISW4204 - Desarrollo de Software en la Nube
**Universidad**: Universidad de los Andes

---

## Objetivo

Implementar escalabilidad automática en la capa de procesamiento batch (workers) utilizando servicios gestionados de AWS, completando la transformación del sistema hacia una arquitectura cloud-native totalmente escalable y de alta disponibilidad.

---

## Arquitectura Implementada

La arquitectura de la Entrega 4 completa la migración hacia servicios gestionados de AWS, incorporando auto-scaling tanto en la capa web como en la capa de procesamiento asíncrono.

### Diagrama de Componentes

![Diagrama de Componentes](https://private-user-images.githubusercontent.com/196699299/514815345-07233949-ac91-46c1-8480-e31a264ed79c.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjMzMTczMjMsIm5iZiI6MTc2MzMxNzAyMywicGF0aCI6Ii8xOTY2OTkyOTkvNTE0ODE1MzQ1LTA3MjMzOTQ5LWFjOTEtNDZjMS04NDgwLWUzMWEyNjRlZDc5Yy5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMTE2JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTExNlQxODE3MDNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1jNmEyOGY1MzZhNzE0YTgyZmRmMWU5N2MxYWE1MzM2YjFhYmU5MDZjZTY5ZDE3ZTNmODdkYTQyZjdmMjg5MGM1JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.OOgP_RaiH4BTLjXiOh5KQmFZM63pHo3-pYX85U4C784)

*Fuente: [Wiki del Proyecto - Diagrama de Componentes](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-4#41-diagrama-de-componentes)*

### Diagrama de Despliegue

![Diagrama de Despliegue](https://private-user-images.githubusercontent.com/196699299/514815460-42f0a205-ba0f-4efa-88da-423d3a623f06.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjMzMTczMjMsIm5iZiI6MTc2MzMxNzAyMywicGF0aCI6Ii8xOTY2OTkyOTkvNTE0ODE1NDYwLTQyZjBhMjA1LWJhMGYtNGVmYS04OGRhLTQyM2QzYTYyM2YwNi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMTE2JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTExNlQxODE3MDNaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0yODE2ZjFkYjI0NzI3ZWNiOTQ3ODVkYTMxZjU2NWFjNTkxMzRmYWFkMjE1NmM3YTNmMWRiZDNiMjg5YWY1OTJhJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.XZX21V7Zojz7w181e6VsR-uYKWJvOyC27tLHzqQQ2-M)

*Fuente: [Wiki del Proyecto - Diagrama de Despliegue](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-4#42-diagrama-de-despliegue)*

### Componentes Principales

El sistema está compuesto por los siguientes componentes en AWS:

**Application Load Balancer (ALB)**
Punto de entrada único para todo el tráfico HTTP, distribuye las peticiones entre las instancias del Core API en múltiples zonas de disponibilidad (us-east-1a y us-east-1b).

**Auto Scaling Group - Core API**
Grupo de auto-escalado con instancias t3.small que ejecutan la API REST. Configurado para escalar entre 2 y 4 instancias basándose en el uso de CPU (target: 50%). Desplegado en dos zonas de disponibilidad para garantizar alta disponibilidad.

**Auto Scaling Group - Workers** (Nuevo en Entrega 4)
Grupo de auto-escalado con instancias t3.large optimizadas para procesamiento de video con FFmpeg. Escala entre 1 y 3 instancias según el uso de CPU (target: 60%). Cada worker procesa videos de forma asíncrona consumiendo tareas desde la cola SQS.

**Amazon SQS** (Nuevo en Entrega 4)
Sistema de mensajería gestionado que reemplaza RabbitMQ. Incluye una cola principal (`video_tasks`) y una Dead Letter Queue (DLQ) para manejo de mensajes fallidos. Configurado con long polling y visibilidad de 60 segundos.

**Amazon RDS PostgreSQL**
Dos instancias de bases de datos gestionadas (Core y Auth) en db.t3.micro con backups automáticos, encriptación en reposo y almacenamiento auto-escalable.

**Amazon S3**
Almacenamiento de objetos para videos originales y procesados, con versionado habilitado y encriptación server-side.

**CloudWatch**
Monitorización y métricas de todos los servicios AWS, integrado con Prometheus y Grafana para observabilidad completa.

---

## Cambios Principales vs Entrega 3

La Entrega 4 introduce mejoras significativas en escalabilidad y resiliencia del sistema:

### Escalabilidad de Workers

En la Entrega 3, los workers corrían en una instancia EC2 fija que no podía escalar automáticamente. Ahora, los workers están configurados en un Auto Scaling Group que aumenta o reduce la capacidad según la carga de CPU, permitiendo procesar más videos durante picos de demanda y reducir costos en períodos de baja actividad.

### Sistema de Mensajería Gestionado

RabbitMQ, que corría en una instancia EC2 y representaba un punto único de falla, fue reemplazado por Amazon SQS. Este cambio elimina la necesidad de gestionar manualmente el broker de mensajes, proporciona durabilidad garantizada de mensajes y escala automáticamente sin límites de throughput.

### Alta Disponibilidad Multi-AZ

El Core API ahora está desplegado en dos zonas de disponibilidad (us-east-1a y us-east-1b), lo que permite que el sistema continúe operando incluso si una zona completa falla. El ALB distribuye el tráfico automáticamente entre las zonas disponibles.

### Mejoras en Performance

Las optimizaciones de las entregas anteriores (pool de conexiones, reducción de commits DB, desactivación de buffering Nginx) se mantienen, y ahora se combinan con la capacidad de escalar horizontalmente tanto en la capa web como en la de procesamiento.

Para más detalles sobre la arquitectura y los cambios implementados, consultar la [Wiki de Entrega 4](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-4).

---

## Auto-Scaling Groups

### Core API

El Auto Scaling Group del Core API está configurado con las siguientes características:

- **Capacidad**: Mínimo 2, deseado 2, máximo 4 instancias
- **Tipo de instancia**: t3.small (2 vCPU, 2 GB RAM)
- **Política de escalado**: Target Tracking basado en CPU promedio del ASG al 50%
- **Health check**: ELB-based mediante el endpoint `/api/health`
- **Cooldown**: 120 segundos entre decisiones de escalado
- **Zonas**: us-east-1a y us-east-1b

Código Terraform: `infra/main.tf:712-768`

### Workers

El Auto Scaling Group de Workers está optimizado para procesamiento intensivo de video:

- **Capacidad**: Mínimo 1, deseado 1, máximo 3 instancias
- **Tipo de instancia**: t3.large (2 vCPU, 8 GB RAM)
- **Política de escalado**: Target Tracking basado en CPU promedio del ASG al 60%
- **Health check**: EC2-based (los workers no reciben tráfico HTTP)
- **Cooldown**: 120 segundos
- **Concurrencia**: 1 tarea por worker para evitar saturación

Código Terraform: `infra/main.tf:868-921`

El uso de t3.large para workers se debe a los requerimientos de memoria y CPU de FFmpeg durante el procesamiento de video.

---

## Amazon SQS

Amazon SQS actúa como intermediario entre el Core API y los Workers, permitiendo procesamiento asíncrono desacoplado y confiable.

### Funcionamiento

1. El Core API recibe un video, lo guarda en S3 y publica un mensaje en la cola `video_tasks`
2. Los workers consumen mensajes mediante long polling (espera de 20 segundos)
3. Cada worker descarga el video de S3, lo procesa con FFmpeg y sube el resultado
4. Si el procesamiento es exitoso, el worker elimina el mensaje de la cola
5. Si el procesamiento falla, el mensaje vuelve a estar disponible después del visibility timeout
6. Después de 5 intentos fallidos, el mensaje se mueve automáticamente a la Dead Letter Queue

Código Terraform: `infra/main.tf:1073-1088`

La cola está configurada con retención de mensajes de 14 días y long polling para reducir llamadas API innecesarias. Durante las pruebas de carga, no se observaron mensajes en la DLQ, lo que confirma la confiabilidad del sistema.

---

## Pruebas de Carga y Resultados

Se ejecutaron dos escenarios principales de pruebas de carga utilizando k6:

### Escenario 1: Core API con Auto-Scaling

Se evaluó la capacidad del Core API bajo diferentes cargas con videos de 4MB, 50MB y 100MB. Los resultados mostraron:

- **4MB**: 35 requests/segundo, p95 latencia de 305ms, 100% success rate
- **50MB**: 2.7 requests/segundo, p95 latencia de 4.6s, 100% success rate
- **100MB**: 1.46 requests/segundo, p95 latencia de 9s, 100% success rate

El sistema mantuvo una tasa de éxito del 99.90-100% en todas las pruebas. El cuello de botella principal identificado fue el ancho de banda de red para archivos grandes, mientras que el procesamiento backend mostró ser eficiente.

### Escenario 2: Workers con Auto-Scaling

Se midió el throughput de procesamiento de workers usando la métrica estandarizada de MB/minuto:

- **4MB**: 22 MB/minuto (5.5 videos/min, 1,320 MB/hora)
- **50MB**: 142.5 MB/minuto (2.85 videos/min, 8,550 MB/hora)
- **100MB**: ~140 MB/minuto estimado (~1.4 videos/min, ~8,400 MB/hora)

Los workers procesaron videos de forma consistente durante 60+ minutos con 100% success rate y sin mensajes en la DLQ. Se observó una mejor utilización de recursos con archivos grandes (6.5x mayor throughput en MB/min), lo que indica que el sistema aprovecha eficientemente el hardware disponible.

El componente que más tiempo consume es FFmpeg (70-75% del tiempo total de procesamiento).

**Documentación completa de pruebas**: [capacity-planning/pruebas_de_carga_entrega4.md](../capacity-planning/pruebas_de_carga_entrega4.md) | [Wiki - Pruebas de Carga](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-carga-entrega-4)

---

## Resultados y Cumplimiento

La Entrega 4 cumple con el 100% de los requisitos establecidos:

| Requisito | Evidencia |
|-----------|-----------|
| Auto-scaling de workers | ASG configurado en `infra/main.tf:868-921`, escalado basado en CPU 60% |
| Sistema de mensajería escalable | Amazon SQS implementado en `infra/main.tf:1073-1088` con DLQ |
| Alta disponibilidad multi-AZ | Core API desplegado en us-east-1a y us-east-1b |
| Pruebas de estrés | Escenarios 1 y 2 ejecutados con videos de 4/50/100MB |
| Sistema confiable | 99.90-100% success rate bajo carga sostenida |

El sistema es ahora completamente escalable, con capacidad de auto-scaling tanto en la capa web como en la de procesamiento. La arquitectura implementada permite manejar aumentos de carga sin intervención manual y mantiene alta disponibilidad mediante despliegue multi-AZ.

---

## Lecciones Aprendidas

### Servicios Gestionados

La migración de RabbitMQ en EC2 a Amazon SQS eliminó un punto único de falla y redujo significativamente el overhead operacional. Los servicios gestionados de AWS (RDS, S3, SQS) permiten al equipo enfocarse en la lógica de negocio en lugar de gestionar infraestructura.

### Auto-Scaling Reactivo

Las políticas de auto-scaling basadas en métricas reales (CPU) funcionan bien en la práctica. El cooldown de 120 segundos evita decisiones erráticas de escalado, y el instance warmup garantiza que las nuevas instancias estén completamente listas antes de recibir tráfico.

### Métricas Normalizadas

El uso de MB/minuto como métrica de throughput de workers es más objetivo que videos/minuto, ya que normaliza el rendimiento independientemente del tamaño del archivo. Esta métrica permitió identificar que el sistema aprovecha mejor los recursos con archivos grandes.

### Alta Disponibilidad

El despliegue multi-AZ del Core API garantiza que el sistema continúe operando incluso si una zona de disponibilidad completa falla. Esta redundancia geográfica es esencial para sistemas en producción.