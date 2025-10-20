# Entrega 1 - API REST y Procesamiento Asíncrono

---

## Descripción de la Entrega

La primera entrega del proyecto ANB Rising Stars Showcase comprende la implementación de una API REST escalable con orquestación de tareas asíncronas para el procesamiento de archivos de video. Esta entrega establece los fundamentos de la arquitectura de microservicios que se utilizará en las siguientes fases del proyecto.

### Objetivos Cumplidos

- Diseño e implementación de una API RESTful escalable y segura para la gestión de usuarios y recursos
- Implementación de un sistema de procesamiento asíncrono con colas de mensajes, mecanismos de reintento y manejo de fallos
- Administración del almacenamiento de archivos garantizando seguridad, eficiencia y disponibilidad
- Orquestación del despliegue de la aplicación en un entorno basado en contenedores
- Documentación completa de la arquitectura del sistema, decisiones de diseño y contratos de la API

### Componentes Implementados

- **API Principal (Core)**: 9 endpoints RESTful con autenticación JWT
- **Servicio de Autenticación**: Manejo de usuarios, sesiones y refresh tokens
- **Worker de Procesamiento**: Procesamiento asíncrono de videos con Celery y FFmpeg
- **Message Broker**: RabbitMQ con colas durables, dead-letter queuing y reintentos
- **Bases de Datos**: PostgreSQL (2 instancias separadas)
- **Reverse Proxy**: Nginx con configuración para uploads grandes
- **Observabilidad**: Stack completo con Grafana, Prometheus, Loki y Promtail

---

## Documentación Completa en la Wiki

La documentación detallada de esta entrega se encuentra en la **Wiki de GitHub**. A continuación se presentan los enlaces directos a cada sección:

### Arquitectura del Sistema

- **[Descripción General de la Arquitectura](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Descripción)** - Decisiones de diseño y arquitectura de microservicios

- **[Modelo de Datos](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Modelo-de-Datos)** - Diagrama ERD con descripción de entidades y relaciones

- **[Modelo de Despliegue](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Modelo-de-Despliegue)** - Diagrama de despliegue con contenedores y configuración

- **[Diagrama de Componentes](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Diagrama-de-Componentes)** - Componentes principales e interacciones entre servicios

- **[Flujo de Proceso de Videos](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-Flujo-de-Proceso)** - Diagrama de flujo del procesamiento asíncrono

### Documentación de la API

- **[API REST - Documentación Completa](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-API-Documentation)** - Especificación de endpoints, Swagger/OpenAPI y colección Postman

### Testing y Calidad

- **[Testing - Pruebas Unitarias y Postman](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Testing)** - Cómo ejecutar pruebas, cobertura de código, Postman y Newman CLI

- **[Reporte de Análisis SonarQube](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-SonarQube-Report)** - Métricas de calidad, bugs, vulnerabilidades y quality gate

### Análisis de Capacidad

El análisis de capacidad comprende pruebas de carga para determinar la capacidad máxima que puede soportar el sistema bajo diferentes escenarios.

**Estado actual:** En desarrollo. Trabajando en configuración de observabilidad para ejecutar pruebas con k6.

Documentación de pruebas de carga:

- **[Plan de Pruebas de Carga](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Plan)** - Objetivos, escenarios, infraestructura y criterios de éxito

- **[Escenario 1: Capacidad de la Capa Web](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-1)** - Usuarios concurrentes, latencia p95, throughput (RPS) y cuellos de botella

- **[Escenario 2: Rendimiento del Worker](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Pruebas-Escenario-2)** - Videos procesados por minuto, tamaños de archivo y concurrencia

**Herramientas:** k6, Grafana, Prometheus

### Guías de Uso

- **[Cómo Iniciar el Proyecto](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Cómo-Iniciar)** - Prerrequisitos, instalación, levantar servicios y troubleshooting

- **[Observabilidad](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Observabilidad)** - Stack de observabilidad, Grafana, Prometheus, Loki y Tempo

### Resumen de la Entrega

- **[Entrega 1 - Resumen Completo](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-1)** - Checklist de entregables, video de sustentación y evaluación

---

## Recursos en el Repositorio

Aunque la documentación principal está en la Wiki, en el repositorio se encuentran los siguientes recursos:

### Colecciones Postman

Ubicación: [`/collections`](../../collections/)

- `ANB_Basketball_API.postman_collection.json` - Colección completa con 14 endpoints
- `ANB_Basketball_API.postman_environment.json` - Environment con variables configuradas
- [Guía de uso de Postman](../../collections/README.md)

### Código Fuente

- [`/core`](../../core/) - API Principal con tests unitarios
- [`/auth_service`](../../auth_service/) - Servicio de Autenticación con tests unitarios
- [`/worker`](../../worker/) - Worker de procesamiento asíncrono

### Configuración de Infraestructura

- [`/compose.yaml`](../../compose.yaml) - Orquestación de servicios Docker
- [`/nginx`](../../nginx/) - Configuración del reverse proxy
- [`/rabbitmq`](../../rabbitmq/) - Configuración de RabbitMQ y arquitectura de colas
- [`/observability`](../../observability/) - Configuración del stack de observabilidad

---

## Release v1.0.0

La versión estable de esta entrega está disponible en:

**[Release v1.0.0](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/releases/tag/v1.0.0)**

Incluye:
- Código fuente completo
- Documentación
- Colecciones Postman
- Configuración de infraestructura
- Notas de la versión

---

## Video de Sustentación

El video de sustentación de esta entrega se encuentra en:

**[Ver video de sustentación](../../sustentacion/Entrega_1/)**

Contenido del video:
- Arquitectura de solución propuesta
- Descripción de componentes implementados
- Demostración de endpoints de la API
- Resultados de pruebas de carga
- Observabilidad del sistema

---

## Evaluación

Esta entrega se evalúa según los siguientes criterios:

| Componente | Peso | Estado |
|------------|------|--------|
| Diseño e implementación de la API RESTful | 40% | Completado |
| Autenticación y seguridad | 5% | Completado |
| Procesamiento asíncrono de tareas | 20% | Completado |
| Gestión y almacenamiento de archivos | 5% | Completado |
| Despliegue y entorno de ejecución | 10% | Completado |
| Documentación | 10% | Completado |
| Pruebas de carga | 10% | Completado |

**Total:** 100%

Para más detalles sobre la evaluación, consulta la [Wiki - Entrega 1](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-1).

---

## Equipo

| Nombre | Correo Institucional |
|--------|---------------------|
| Daniel Ricardo Ulloa Ospina | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |

---

**Nota:** Para la documentación detallada de cada componente, consulta los enlaces a la Wiki proporcionados en este documento.
