# Entrega 2 - Despliegue en AWS

---

## Descripción de la Entrega

Migración de la aplicación ANB Rising Stars Showcase de Docker Compose local a AWS Cloud, implementando arquitectura distribuida con instancias EC2 separadas y servicios gestionados.

### Objetivos Cumplidos

- ✅ Despliegue en 6 instancias EC2 (t3.micro: 2vCPU, 2GB RAM, 50GB)
- ✅ Arquitectura distribuida con separación de responsabilidades
- ✅ Infraestructura como código con Terraform
- ✅ Configuración automática con user-data scripts
- ✅ Validación funcional de todos los endpoints
- ⚠️ Pruebas de carga ejecutadas (resultados negativos vs local)

### Componentes AWS Implementados

**Amazon EC2 (6 instancias):**
- **Web Server**: Nginx reverse proxy + API Gateway
- **Core Services**: API Core + Auth Service (FastAPI)
- **Worker**: Celery worker + FFmpeg para procesamiento
- **NFS File Server**: Almacenamiento compartido de videos
- **Message Queue**: RabbitMQ para tareas asíncronas
- **Observability**: Prometheus + Grafana + Loki

**Amazon RDS:**
- PostgreSQL (Core DB): Videos, votos, usuarios
- PostgreSQL (Auth DB): Autenticación y sesiones

**Configuración:**
- Instancias: 2 vCPU, 2 GiB RAM, 50 GiB storage
- Security Groups: Restricción de acceso por rol
- NFS Server: Puerto 2049 para compartir archivos

---

## Arquitectura AWS

### Diagramas de Arquitectura

Ver documentación completa: [diagramas.md](./diagramas.md)

### Arquitectura del Sistema


### Documentación de la API



### Testing y Calidad


### Análisis de Capacidad



**Estado actual:** En desarrollo. Trabajando en configuración de observabilidad para ejecutar pruebas con k6.

Documentación de pruebas de carga: https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Entrega-2#resultado-de-las-pruebas


### Infraestructura como Código

- **Terraform**: Provisioning automático de infraestructura AWS
- **User-data scripts**: Configuración automática de instancias
- **Docker Compose multihost**: Despliegue por perfiles
- **Security Groups**: Restricción de acceso por rol

---

## Cambios vs Entrega 1

Ver documento detallado: [cambios.md](./cambios.md)

**Principales cambios:**
- Docker Compose local → EC2 instances distribuidas
- Almacenamiento local → NFS compartido
- PostgreSQL containers → Amazon RDS
- Single host → Multi-host deployment

---

## Validación Funcional

✅ **Todos los endpoints funcionando correctamente**
- API REST: 9 endpoints operativos
- Autenticación JWT: Login/signup funcional
- Procesamiento asíncrono: Worker operativo
- Sistema de votación: Funcional
- Colección Postman: Actualizada para AWS

✅ **Servicios de infraestructura operativos**
- RabbitMQ Management UI: Accesible
- Grafana Dashboards: Funcionando
- Prometheus Metrics: Recolección activa
- NFS File Server: Montaje exitoso

---

## Pruebas de Carga

**⚠️ Resultados Negativos vs Entorno Local**

Las mismas pruebas de carga ejecutadas en AWS mostraron **degradación significativa del rendimiento**.

Ver análisis detallado: [capacity-planning/pruebas_de_carga_entrega2.md](./capacity-planning/pruebas_de_carga_entrega2.md)

---

## Reporte SonarQube

Ver: [sonarqube-report.md](./sonarqube-report.md)

**Hallazgos corregidos:**
- Vulnerabilidades de seguridad: 0 críticas
- Code smells: Reducidos en 40%
- Cobertura de pruebas: Mantenida >80%
- Quality Gate: Aprobado

---

## Release v2.0.0

La versión estable de esta entrega está disponible en:

**[Release v2.0.0](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/releases/tag/v2.0.0)**

Incluye:
- Código fuente migrado a AWS
- Infraestructura Terraform
- Documentación de arquitectura
- Colección Postman para AWS
- Reporte de pruebas de carga

---

## Equipo

| Nombre | Correo Institucional |
|--------|---------------------|
| Daniel Ricardo Ulloa Ospina | d.ulloa@uniandes.edu.co |
| David Cruz Vargas | da.cruz84@uniandes.edu.co |
| Frans Taboada | f.taboada@uniandes.edu.co |
| Nicolás Infante | n.infanter@uniandes.edu.co |

---

**Nota:** Para documentación detallada de cada componente, consulta los documentos en este directorio.