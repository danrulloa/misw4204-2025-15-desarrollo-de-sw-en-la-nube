# Configuración Local vs Cloud

Este documento detalla los cambios necesarios para ejecutar el sistema localmente o en cloud.

---

## 📍 AMBIENTE LOCAL

### Archivos a Modificar

#### 1. `compose.yaml`

**RabbitMQ Healthcheck** (ya configurado):
```yaml
rabbitmq:
  healthcheck:
    test: [ "CMD", "rabbitmq-diagnostics", "-q", "ping" ]
    interval: 15s
    timeout: 30s              # ← Crítico para local
    retries: 5
    start_period: 90s         # ← Crítico para local
```

**Variables de Entorno - anb_api**:
```yaml
anb_api:
  environment:
    # ... otras variables ...
    CELERY_BROKER_URL=amqp://${RABBITMQ_DEFAULT_USER:-rabbit}:${RABBITMQ_DEFAULT_PASS:-rabbitpass}@rabbitmq:5672//
    RABBITMQ_URL=amqp://${RABBITMQ_DEFAULT_USER:-rabbit}:${RABBITMQ_DEFAULT_PASS:-rabbitpass}@rabbitmq:5672/  # ← Crítico
```

#### 2. `nginx/nginx.conf`

**Upstreams para Local**:
```nginx
# LOCAL: nombres de servicios Docker (compose.yaml)
upstream api_upstream   { server anb_api:8000;        keepalive 32; }
upstream auth_upstream  { server anb-auth-service:8000; keepalive 16; }
upstream rmq_mgmt_upstream { server rabbitmq:15672; keepalive 8; }
upstream grafana_upstream { server grafana:3000; keepalive 8; }

# MULTIHOST: IPs dinámicas del aprovisionamiento (docker-compose.multihost.yml)
# upstream api_upstream   { server __CORE_IP__:8000;        keepalive 32; }
# upstream auth_upstream  { server __CORE_IP__:8001; keepalive 16; }
# upstream rmq_mgmt_upstream { server __MQ_IP__:15672; keepalive 8; }
# upstream grafana_upstream { server __OBS_IP__:3000; keepalive 8; }
```

#### 3. `core/app/config.py`

**Storage Backend para Local**:
```python
STORAGE_BACKEND: str = "local"  # "local" | "s3"  ← "local" para desarrollo
```

---

## ☁️ AMBIENTE CLOUD (AWS)

### Archivos a Modificar

#### 1. `docker-compose.multihost.yml`

**Usar IPs de provisionamiento** en lugar de nombres de servicio.

Ver `infra/main.tf` para reemplazar:
- `__CORE_IP__` → IP de instancia core
- `__MQ_IP__` → IP de instancia RabbitMQ
- `__OBS_IP__` → IP de instancia observabilidad
- etc.

#### 2. `nginx/nginx.conf`

**Descomentar upstreams de MULTIHOST** y comentar los de LOCAL:
```nginx
# LOCAL: nombres de servicios Docker (compose.yaml)
# upstream api_upstream   { server anb_api:8000;        keepalive 32; }
# upstream auth_upstream  { server anb-auth-service:8000; keepalive 16; }
# upstream rmq_mgmt_upstream { server rabbitmq:15672; keepalive 8; }
# upstream grafana_upstream { server grafana:3000; keepalive 8; }

# MULTIHOST: IPs dinámicas del aprovisionamiento (docker-compose.multihost.yml)
upstream api_upstream   { server __CORE_IP__:8000;        keepalive 32; }
upstream auth_upstream  { server __CORE_IP__:8001; keepalive 16; }
upstream rmq_mgmt_upstream { server __MQ_IP__:15672; keepalive 8; }
upstream grafana_upstream { server __OBS_IP__:3000; keepalive 8; }
```

#### 3. `core/app/config.py`

**Storage Backend para Cloud**:
```python
STORAGE_BACKEND: str = "s3"  # "local" | "s3"  ← "s3" para producción
```

**Variables de Entorno S3** (en `.env` o en cloud):
```bash
S3_BUCKET=anb-basketball-bucket
S3_REGION=us-east-1
S3_PREFIX=uploads
S3_FORCE_PATH_STYLE=0
S3_VERIFY_SSL=1
```

---

## 🔄 Checklist de Cambio de Ambiente

### Local → Cloud

- [ ] Cambiar `nginx/nginx.conf` (upstreams)
- [ ] Cambiar `STORAGE_BACKEND` a `"s3"` en `core/app/config.py`
- [ ] Configurar credenciales S3 en `.env`
- [ ] Usar `docker-compose.multihost.yml` en lugar de `compose.yaml`
- [ ] Verificar `rabbitmq/definitions.json` se carga correctamente
- [ ] Verificar healthchecks no son demasiado agresivos

### Cloud → Local

- [ ] Cambiar `nginx/nginx.conf` (upstreams)
- [ ] Cambiar `STORAGE_BACKEND` a `"local"` en `core/app/config.py`
- [ ] Usar `compose.yaml` en lugar de `docker-compose.multihost.yml`
- [ ] Verificar `rabbitmq` healthcheck tiene `start_period: 90s`
- [ ] Verificar `RABBITMQ_URL` está configurado en `anb_api`

---

## ⚠️ Problemas Comunes

### RabbitMQ No Arranca (Local)

**Síntomas**: Container en estado unhealthy, otros servicios no inician

**Solución**: Verificar en `compose.yaml`:
```yaml
rabbitmq:
  healthcheck:
    timeout: 30s          # ← Mínimo 30s
    start_period: 90s     # ← Mínimo 90s
```

**Razón**: RabbitMQ tarda 60s+ en cargar definitions.json y plugins.

### Nginx Restart Loop (Local)

**Síntomas**: `host not found in upstream "__CORE_IP__:8000"`

**Causa**: `nginx.conf` configurado para cloud en local

**Solución**: Usar upstreams con nombres de servicio:
```nginx
upstream api_upstream { server anb_api:8000; }
```

### Error al Subir Video "Unable to locate credentials"

**Síntomas**: 502 Bad Gateway con error de S3

**Causa**: `STORAGE_BACKEND="s3"` sin credenciales en local

**Solución**: Cambiar a local:
```python
STORAGE_BACKEND: str = "local"
```

### RabbitMQ "configuration missing required env vars"

**Síntomas**: 502 Bad Gateway al encolar procesamiento

**Causa**: Falta `RABBITMQ_URL` en `anb_api`

**Solución**: Agregar en `compose.yaml`:
```yaml
anb_api:
  environment:
    - RABBITMQ_URL=amqp://${RABBITMQ_DEFAULT_USER:-rabbit}:${RABBITMQ_DEFAULT_PASS:-rabbitpass}@rabbitmq:5672/
```

---

## 📝 Notas

1. **No hacer commit** de `.env` con credenciales reales
2. **Verificar** que `rabbitmq/definitions.json` existe y es válido
3. **Limpiar** volúmenes Docker si hay problemas de persistencia:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

