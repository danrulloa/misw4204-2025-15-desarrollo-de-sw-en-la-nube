# Cambios vs Entrega 1

---

## Comparativa Entrega 1 vs Entrega 2

| Aspecto | Entrega 1 (Local) | Entrega 2 (AWS) |
|---------|-------------------|-----------------|
| **Infraestructura** | Docker Compose en local | 6 instancias EC2 en AWS |
| **Base de Datos** | PostgreSQL en containers | Amazon RDS (2 instancias) |
| **Almacenamiento** | Volúmenes Docker locales | NFS Server (EC2) compartido |
| **Networking** | Red Docker interna | VPC + Security Groups |
| **Deployment** | `docker compose up` | Terraform + user-data scripts |
| **Configuración** | `.env` local | Variables en user-data |
| **Rendimiento** | Optimizado para local | Degradado por latencia de red |

---

## Componentes Nuevos

### NFS File Server
- **Instancia**: EC2 t3.micro (2vCPU, 2GB RAM, 50GB)
- **Puerto**: 2049
- **Directorio**: `/mnt/anb-storage/`
- **Contenido**: uploads/, processed/, assets/
- **Clientes**: Web Server y Worker

### Amazon RDS
- **Core DB**: anb_core (videos, votos)
- **Auth DB**: anb_auth (usuarios, tokens)
- **Tipo**: db.t3.micro (development)
- **Configuración**: Sin replicación ni alta disponibilidad

### Infraestructura Distribuida
- **6 instancias EC2** separadas por rol
- **Security Groups** específicos por componente
- **Terraform** para provisioning automático
- **User-data scripts** para configuración automática

---

## Arquitectura de Red

### Security Groups
| Rol | Puertos | Acceso | Descripción |
|-----|---------|--------|-------------|
| **Web** | 80, 8080 | Público | Nginx reverse proxy |
| **Core** | 8000, 8001 | Desde Web | API Core + Auth Service |
| **Worker** | - | Interno | Solo procesamiento |
| **NFS** | 2049 | Desde Web/Worker | File sharing |
| **DB** | 5432, 5433 | Desde Core/Worker | PostgreSQL |
| **MQ** | 5672, 15672 | Interno/Admin | RabbitMQ |
| **OBS** | 9090, 3000, 3100 | Admin | Prometheus/Grafana/Loki |

### IPs de Despliegue
```
Web Server:     44.203.113.255 (público) / 172.31.87.226 (privado)
Core Services:  13.221.222.65 (público) / 172.31.87.84 (privado)
Worker:         3.91.152.104 (público) / 172.31.92.106 (privado)
NFS Server:     [No implementado aún]
Database:       54.172.174.197 (público) / 172.31.88.209 (privado)
Message Queue:  54.166.253.172 (público) / 172.31.92.143 (privado)
Observability:  54.91.191.43 (público) / 172.31.92.52 (privado)
```

---

## Código

**Sin cambios en lógica de negocio.**

### Cambios Menores
- Variables de entorno para rutas NFS
- Connection strings para RDS
- Volúmenes Docker apuntan a NFS mount
- URLs de servicios actualizadas

### Archivos Modificados
- `infra/main.tf` - Infraestructura Terraform
- `infra/userdata.sh.tftpl` - Scripts de configuración
- `docker-compose.multihost.yml` - Compose por perfiles
- `collections/ANB_Basketball_API.postman_environment.json` - Environment AWS

---

## Validación Funcional

### Endpoints Validados
✅ **Autenticación**
- POST /api/auth/signup
- POST /api/auth/login

✅ **Gestión de Videos**
- POST /api/videos/upload
- GET /api/videos
- GET /api/videos/{id}
- DELETE /api/videos/{id}

✅ **Sistema Público**
- GET /api/public/videos
- POST /api/public/videos/{id}/vote
- GET /api/public/rankings

### Servicios de Infraestructura
✅ **RabbitMQ Management**: http://54.166.253.172:15672
✅ **Grafana Dashboards**: http://54.91.191.43:3000
✅ **Prometheus Metrics**: http://54.91.191.43:9090
✅ **API Documentation**: http://44.203.113.255:8080/api/docs

---

## Próximos Pasos

### Implementación Pendiente
- [ ] **NFS File Server**: Instancia EC2 + configuración NFS
- [ ] **Migración completa a RDS**: Eliminar PostgreSQL containers
- [ ] **Optimización de rendimiento**: Tuning de configuración
- [ ] **Monitoreo avanzado**: Alertas y métricas de negocio

### Mejoras Recomendadas
- [ ] **Auto-scaling**: Implementar escalado automático
- [ ] **Load Balancer**: Distribución de carga
- [ ] **CDN**: Aceleración de contenido estático
- [ ] **Backup Strategy**: Estrategia de respaldo