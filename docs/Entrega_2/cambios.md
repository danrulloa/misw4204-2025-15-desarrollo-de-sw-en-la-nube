# Cambios vs Entrega 1

## Migración: Local → AWS

La migración principal consiste en pasar de un entorno Docker Compose local a una arquitectura distribuida en AWS.

### Antes (Entrega 1)

- Todo corriendo en un solo host con Docker Compose
- PostgreSQL en contenedores
- Volúmenes Docker para archivos
- Red interna de Docker
- Comando: `docker compose up`

### Después (Entrega 2)

- 6 instancias EC2 independientes (t3.micro: 2 vCPU, 2 GB RAM, 50 GB)
- PostgreSQL en containers distribuidos (RDS pendiente)
- Volúmenes Docker para archivos compartidos (NFS pendiente)
- VPC con Security Groups
- Despliegue con Terraform + scripts automatizados

---

## Componentes Implementados

### Arquitectura Distribuida

[Diagrama de Despliegue](https://github.com/user-attachments/assets/69306b90-567b-4f51-b017-aa9a9a8dcc25)

**6 instancias EC2**:

| Componente | Función | Puertos |
|------------|---------|---------|
| **Web Server** | Nginx + reverse proxy | 80, 8080 |
| **Core Services** | API Core + Auth Service | 8000, 8001 |
| **Worker** | Procesamiento de videos | - |
| **Database** | PostgreSQL (containers) | 5432, 5433 |
| **Message Queue** | RabbitMQ | 5672, 15672 |
| **Observability** | Prometheus + Grafana + Loki | 9090, 3000, 3100 |

### Infraestructura como Código

**Terraform**: Define toda la infraestructura AWS

- Instancias EC2
- Security Groups
- Networking (VPC, subnets)
- Variables de configuración

**User-data scripts**: Configuran automáticamente cada instancia

- Instalan dependencias
- Configuran Docker
- Inician servicios

---

## Componentes Pendientes

### 1. Amazon RDS

**Estado**: No implementado

**Actual**: PostgreSQL corriendo en containers Docker en instancia EC2

**Razón**: Por limitaciones de tiempo, se mantuvo PostgreSQL en containers

**Próximo paso**: Migrar a Amazon RDS para tener base de datos gestionada

### 2. NFS File Server

**Estado**: No implementado

**Actual**: Volúmenes Docker para archivos compartidos

**Razón**: Por limitaciones de tiempo, se mantuvieron volúmenes Docker

**Próximo paso**: Implementar servidor NFS dedicado o migrar a EFS/S3

---

## Arquitectura de Red

### Security Groups

Cada componente tiene reglas específicas de firewall:

- **Web**: Abierto al público (80, 8080)
- **Core**: Solo accesible desde Web
- **Worker**: Solo interno
- **DB**: Solo desde Core y Worker (5432, 5433)
- **MQ**: Interno + admin UI (5672, 15672)
- **Observability**: Admin UI (9090, 3000, 3100)

### Comunicación entre Componentes

[Diagrama de Componentes](https://github.com/user-attachments/assets/35e87e6e-4a70-47ba-964a-44e37856f721)

```
Usuario → Web Server → Core Services → Database (containers)
                    ↓
                  Worker → Database + Volúmenes compartidos
                    ↓
              RabbitMQ (mensajería)
```

---

## Cambios en el Código

**Buenas noticias**: Prácticamente ningún cambio en la lógica de negocio.

### Lo que se modificó:

1. **Variables de entorno**:
   - Rutas de archivos apuntan a volúmenes Docker
   - Connection strings para PostgreSQL en instancias separadas
   - URLs de servicios usan IPs privadas de EC2

2. **Docker Compose**:
   - `docker-compose.multihost.yml`: Versión con perfiles por componente
   - Cada instancia ejecuta solo su perfil específico

3. **Colección Postman**:
   - Environment actualizado con IPs públicas de AWS
   - Mismo funcionamiento, solo cambian las URLs

### Archivos principales modificados:

- `infra/main.tf` - Terraform para AWS
- `infra/userdata.sh.tftpl` - Scripts de configuración
- `docker-compose.multihost.yml` - Compose distribuido
- `collections/ANB_Basketball_API.postman_environment.json` - Environment AWS

---

## Validación Funcional

### Todos los endpoints funcionan correctamente

**Autenticación**:

- `POST /api/auth/signup` ✅
- `POST /api/auth/login` ✅

**Videos**:

- `POST /api/videos/upload` ✅
- `GET /api/videos` ✅
- `GET /api/videos/{id}` ✅
- `DELETE /api/videos/{id}` ✅

**Sistema Público**:

- `GET /api/public/videos` ✅
- `GET /api/public/videos/{id}` ✅
- `POST /api/public/videos/{id}/vote` ✅
- `GET /api/public/rankings` ✅

### Servicios operativos

Una vez desplegado el ambiente en AWS Academy, se puede acceder a:

- **API Docs**: `http://<WEB_SERVER_IP>:8080/api/docs`
- **RabbitMQ UI**: `http://<MESSAGE_QUEUE_IP>:15672`
- **Grafana**: `http://<OBSERVABILITY_IP>:3000`
- **Prometheus**: `http://<OBSERVABILITY_IP>:9090`

> **Nota**: Las IPs públicas de las instancias EC2 cambian cada vez que se levanta el sandbox de AWS Academy. Consultar las IPs actuales en la consola de AWS EC2.

---

## Diferencias de Rendimiento

Según las pruebas de carga (ver [pruebas_de_carga_entrega2.md](./capacity-planning/pruebas_de_carga_entrega2.md)):

- **Estabilidad**: 100% de peticiones exitosas en todos los escenarios ✅
- **Latencia**: p95 entre 2.14s y 6.2s (muy superior al objetivo de <1s) ⚠️
- **Causa**: No es por recursos (t3.large no mejoró significativamente), sino por configuración de proxy/API y latencia entre instancias

**Conclusión**: La arquitectura distribuida funciona pero necesita optimización en configuración y código.

---

## Próximos Pasos

1. ✅ Migración a AWS completada
2. ✅ Validación funcional exitosa
3. 🔜 Migrar a Amazon RDS
4. 🔜 Implementar NFS Server o migrar a EFS
5. ⚠️ Optimización de rendimiento pendiente
6. 🔜 Implementar recomendaciones de las pruebas de carga
