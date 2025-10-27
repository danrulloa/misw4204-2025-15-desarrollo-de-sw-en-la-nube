# Entrega 2 - Despliegue en AWS

## Qué se hizo

Migramos la aplicación ANB Rising Stars Showcase de Docker Compose local a AWS. La aplicación ahora corre en 6 instancias EC2 separadas con PostgreSQL distribuido en containers.

**Video de presentación**: [Ver video en GitHub](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-2#---video-de-presentaci%C3%B3n-de-entrega-2--)

---

## Arquitectura

### Componentes Desplegados

**6 instancias EC2** (t3.micro: 2 vCPU, 2 GB RAM, 50 GB):

1. **Web Server**: Nginx + reverse proxy
2. **Core Services**: API Core + Auth Service (FastAPI)
3. **Worker**: Celery + FFmpeg para procesamiento de videos
4. **Database**: PostgreSQL (containers)
5. **Message Queue**: RabbitMQ
6. **Observability**: Prometheus + Grafana + Loki

> **Nota sobre AWS Academy**: Las IPs públicas de las instancias EC2 cambian cada vez que se levanta el sandbox. Consultar las IPs actuales en la consola de AWS EC2 después del despliegue.

### Componentes Pendientes

Por limitaciones de tiempo, no se implementaron:

- **Amazon RDS**: Se mantiene PostgreSQL en containers (migración pendiente)
- **NFS Server**: Se usan volúmenes Docker compartidos (implementación pendiente)

Ver detalles en [cambios.md](./cambios.md)

### Diagramas

[**Diagrama de Despliegue**](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-2#diagrama-de-despliegue)

[**Diagrama de Componentes**](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-2#diagrama-de-componentes)

[**Diagrama de Flujo**](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-2#diagrama-de-flujo)

---

## Funcionalidad

### Todos los endpoints funcionan correctamente

**Autenticación**:

- `POST /api/auth/signup`
- `POST /api/auth/login`

**Videos**:

- `POST /api/videos/upload`
- `GET /api/videos`
- `GET /api/videos/{id}`
- `DELETE /api/videos/{id}`

**Sistema Público**:

- `GET /api/public/videos`
- `GET /api/public/videos/{id}`
- `POST /api/public/videos/{id}/vote`
- `GET /api/public/rankings`

---

## Pruebas de Carga

Se ejecutaron 3 escenarios de carga con k6:

1. **Sanidad**: 5 usuarios por 1 minuto
2. **Escalamiento**: 6 usuarios por 8 minutos (carga progresiva)
3. **Sostenida Corta**: 5 usuarios por 5 minutos (carga constante)

### Resultados

- **Estabilidad**: 100% de peticiones exitosas en todos los escenarios
- **Rendimiento**: Tiempos de respuesta entre 2.14s y 6.2s (p95)
- **Problema identificado**: Latencia alta no relacionada con recursos, sino con configuración de proxy/API y arquitectura distribuida

Ver análisis completo: [pruebas_de_carga_entrega2.md](./capacity-planning/pruebas_de_carga_entrega2.md)

---

## Cambios vs Entrega 1

Lo principal:

- Docker Compose local → 6 instancias EC2 en AWS
- PostgreSQL en un solo host → PostgreSQL distribuido en containers
- Volúmenes Docker locales → Volúmenes Docker compartidos
- Despliegue manual → Terraform + scripts automatizados

Pendiente:

- Migración a Amazon RDS
- Implementación de NFS Server dedicado

Ver detalle completo: [cambios.md](./cambios.md)

---

## SonarQube

Se implementó y se corrigieron los hallazgos de la Entrega 1 en Worker y auth_service:

- Vulnerabilidades críticas: 0
- Code smells: Reducidos
- Cobertura: >80%
- Quality Gate: Aprobado

Ver reporte: [Arquitectura SonarQube Report](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Arquitectura-SonarQube-Report)

---

## Infraestructura como Código

Todo el despliegue está automatizado con:

- **Terraform**: Define instancias EC2, Security Groups, networking
- **User-data scripts**: Configuran automáticamente cada instancia
- **Docker Compose multihost**: Cada instancia ejecuta su perfil específico

Código: [/infra](../../infra/)

---

## Release

Versión estable: [v2.0.0](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/releases/tag/2.0.0)
