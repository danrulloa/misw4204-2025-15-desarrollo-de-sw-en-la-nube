# Plan de Optimizaciones de Performance - Upload de Videos

## 🎯 Objetivo

**Meta**: Lograr **<1s** de tiempo de respuesta para upload de videos de **100MB** bajo condiciones de carga normal.

**Contexto**: Sistema debe soportar cientos de usuarios subiendo videos simultáneamente.

---

## 📊 Línea Base Actual (Branch: develop)

### Métricas de Referencia

| Escenario | Tiempo | Estado |
|-----------|--------|--------|
| **9MB (1 VU)** | 338ms | ✅ OK |
| **100MB (1 VU)** | 7.81s | ❌ Objetivo: <1s |
| **100MB (5 VUs)** | p95=38.06s | ❌ Crítico |

### Análisis de Línea Base

**Bajo carga simple** (1 petición):
- 9MB: Excelente performance (338ms)
- 100MB: 7.81s indica bottleneck en I/O de red/archivos

**Bajo concurrencia** (5 VUs):
- `http_req_waiting` p95=**30.78s** (dominante)
- `http_req_sending` p95=7.9s
- Indica **cuello de botella crítico** en:
  - Base de datos (bloqueo de transacciones)
  - RabbitMQ (conexiones síncronas sin pool)

**Métricas de red**:
- `upload_rate_mb_s` p95=36.58 MB/s (aceptable)
- Throughput de red no es el problema principal

---

## ✅ Optimizaciones Completadas

### Paso 0: RabbitMQ Healthcheck Fix ✅

**Archivo**: `compose.yaml`

**Problema**: RabbitMQ no llegaba a estado "healthy", bloqueando otros servicios.

**Solución**:
```yaml
rabbitmq:
  healthcheck:
    timeout: 30s          # Antes: 15s
    start_period: 90s     # Nuevo: permite inicialización completa
```

**Resultado**: RabbitMQ inicializa correctamente, servicios dependientes arrancan.

---

### Paso 0.1: Configuración Nginx Local ✅

**Archivo**: `nginx/nginx.conf`

**Problema**: Nginx restart loop con error `host not found in upstream "__CORE_IP__:8000"`.

**Solución**: Upstreams flexibles para local y cloud:
```nginx
# LOCAL: nombres de servicios Docker
upstream api_upstream { server anb_api:8000; keepalive 32; }
# ... otros upstreams ...

# MULTIHOST: IPs (comentado para local)
# upstream api_upstream { server __CORE_IP__:8000; keepalive 32; }
```

**Resultado**: Nginx funciona correctamente en local.

---

### Paso 0.2: Storage Backend Local ✅

**Archivo**: `core/app/config.py`

**Problema**: Error "Unable to locate credentials" al intentar usar S3 en local.

**Solución**:
```python
STORAGE_BACKEND: str = "local"  # Para desarrollo local
```

**Resultado**: Almacenamiento funciona correctamente en local.

---

### Paso 0.3: RABBITMQ_URL Configuration ✅

**Archivo**: `compose.yaml`

**Problema**: Error "RabbitMQ configuration missing required env vars" desde anb_api.

**Solución**:
```yaml
anb_api:
  environment:
    - RABBITMQ_URL=amqp://${RABBITMQ_DEFAULT_USER:-rabbit}:${RABBITMQ_DEFAULT_PASS:-rabbitpass}@rabbitmq:5672/
```

**Resultado**: RabbitMQ connectivity funcionando.

---

## 🎯 Optimizaciones Pendientes (Orden de Implementación)

### Fase 1: Reducción de Commits a Base de Datos

**Objetivo**: Reducir round-trips a PostgreSQL

**Cambio**: De 3 commits → 1 commit usando `db.flush()` intermedio

**Archivos**:
- `core/app/services/uploads/local.py`

**Cambios**:
```python
# ANTES: 3 commits
db.add(video)
await db.commit()           # Commit 1
await db.refresh(video)

video.correlation_id = correlation_id
video.status = VideoStatus.processing
await db.commit()           # Commit 2
await db.refresh(video)

# Si falla MQ:
await db.commit()           # Commit 3 (rollback)

# DESPUÉS: 1 commit
db.add(video)
await db.flush()            # Obtiene ID sin commit

# ... lógica ...
await db.commit()           # 1 solo commit al final
```

**Impacto esperado**: 15-20% mejora en tiempo de respuesta.

**Estado**: ⏳ Pendiente de implementar.

---

### Fase 2: Pool de Conexiones Asíncrono para RabbitMQ

**Objetivo**: Reducir overhead de conexiones RabbitMQ

**Problema**: Cada `RabbitPublisher` crea una nueva conexión síncrona.

**Solución**: Pool singleton de Cliente Celery reutilizable con `kombu`.

**Archivos modificados**:
- `core/app/services/mq/celery_pool.py` (nuevo: pool singleton)
- `core/app/services/mq/rabbit.py` (refactorizado para usar pool)
- `core/requirements.txt` (agregar `kombu>=5.3`)

**Cambios**:
```python
# ANTES: Crear cliente Celery por mensaje
class RabbitPublisher:
    def __init__(self):
        self._celery = Celery('api_client', broker=broker_url)  # Nuevo cada vez
        # ... configuración ...

# DESPUÉS: Pool singleton reutilizable
class CeleryPool:
    _instance = None
    def get_client(self):
        if not self._celery_app:
            self._initialize_celery()  # Solo una vez
        return self._celery_app

class RabbitPublisher:
    def __init__(self):
        pool = get_pool()
        self._celery = pool.get_client()  # Reutiliza
```

**Impacto medido**: 
- ✅ Waiting time 9MB: -35% adicional (vs Fase 1)
- ✅ Waiting time 100MB: -29% (vs Fase 1)
- ⚠️ Sending time 100MB: +28% (trade-off)
- ❌ Success rate 100MB: 20% (vs 100% Fase 1)

**Estado**: ✅ Completada.

---

### Fase 3: Optimización de Pool PostgreSQL ✅

**Objetivo**: Ajustar pool de conexiones para carga concurrente

**Archivos modificados**:
- `core/app/database.py`

**Implementación**:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Aumentar de default (5) a 20
    max_overflow=10,        # Permitir burst de conexiones
    pool_timeout=30,        # Timeout razonable
    pool_pre_ping=True,     # Health checks de conexiones
    future=True,
)
```

**Impacto medido**:
- ✅ **100MB simple**: -60% vs Fase 1 (2.74s vs 6.94s)
- ✅ **9MB concurrencia**: -34% vs Fase 2 (2.13s vs 3.21s)
- ✅ **100MB concurrencia**: -23% vs Fase 2 (21.28s vs 27.69s)
- ✅ **Success rate**: 100% para 100MB (vs 20% Fase 2)
- ✅ **Sending time**: -39% vs Fase 2 (6.91s vs 11.4s)

**Diagnóstico**: El pool PostgreSQL optimizado resuelve la regresión de Fase 2 y mejora dramáticamente 100MB simple.

**Estado**: ✅ Completada.

---

### Fase 4: Investigación de Bloqueos en Base de Datos

**Objetivo**: Identificar deadlocks o locks excesivos

**Acciones**:
1. Revisar logs de PostgreSQL durante prueba de carga
2. Verificar isolation level de transacciones
3. Verificar índices en tabla `videos`:
   - `idx_video_user_status` en (user_id, status)
   - `idx_video_created` en created_at
4. Considerar `SELECT FOR UPDATE NOWAIT` para casos críticos

**Archivos**:
- `core/app/models/video.py` (verificar índices)
- `core/app/database.py` (isolation level)

**Impacto esperado**: Resolver problema de concurrencia si existe.

**Estado**: ⏳ Pendiente de investigar.

---

### Fase 5: Desactivar Buffering en Nginx para Uploads ✅

**Objetivo**: Reducir latencia de buffering

**Archivo modificado**:
- `nginx/nginx.conf` (agregado location específico para uploads)

**Implementación**:
```nginx
location /api/videos/upload {
    proxy_pass http://api_upstream/videos/upload;
    proxy_request_buffering off;
    proxy_buffering off;
}
```

**Impacto medido**:
- ✅ **9MB simple**: Mejoró 20% (370ms → 297ms)
- ✅ **100MB simple**: Mejoró 21% (2.74s → 2.16s)
- ✅ **9MB concurrencia**: Mejoró 33% (2.13s → 1.43s)
- ✅ **100MB waiting**: Mejoró 36% (15.3s → 9.84s)
- ❌ **100MB sending**: Empeoró 103% (6.91s → 14.02s)

**Diagnóstico**: Buffering OFF mejora casos simples pero empeora archivos grandes bajo concurrencia. Nginx sin buffer no puede optimizar I/O correctamente.

**Estado**: ✅ Completada (pero REGRESIÓN en 100MB concurrencia)

---

### Fase 6: Async File Writing con Streaming

**Objetivo**: Escritura de archivos en chunks asíncronos

**Problema anterior**: Intentamos `aiofiles` leyendo todo en memoria → empeoró performance.

**Solución correcta**: Streaming por chunks:
```python
async def _async_save_file(self, fileobj, dest_path):
    async with aiofiles.open(dest_path, 'wb') as f:
        while chunk := await asyncio.to_thread(fileobj.read, 8192):
            await f.write(chunk)
```

**Archivos**:
- `core/app/services/uploads/local.py`

**Impacto esperado**: 15-20% mejora en sending time para archivos grandes.

**Estado**: ⏳ Pendiente de implementar (versión correcta).

---

### Fase 7: Escalamiento Horizontal de Workers

**Objetivo**: Procesar videos más rápido (no afecta upload)

**Cambios** en `compose.yaml`:
```yaml
worker:
  deploy:
    replicas: 3  # Antes: 1
```

**Impacto esperado**: Mejora procesamiento asíncrono, no upload.

**Estado**: ⏳ Pendiente de implementar.

---

## 🔍 Análisis del Problema Principal

### Waiting Time Bajo Concurrencia

**Métrica crítica**: `http_req_waiting` p95=30.78s (vs 7.81s aislado)

**Indica**:
1. Bloqueos en base de datos (más probable)
2. RabbitMQ sin pool de conexiones
3. Transacciones demasiado largas
4. Falta de índices adecuados

**Hipótesis principales**:
- Transacciones bloquean tabla `videos` durante el commit
- Cada mensaje a RabbitMQ abre conexión nueva
- Pool de PostgreSQL insuficiente para 5 VUs concurrentes

**Acción**: Implementar Fases 1, 2, 3 y 4 en orden, midiendo después de cada una.

---

## 📋 Orden Recomendado de Implementación

1. ✅ **Fase 0**: Configuración inicial (completado)
2. ✅ **Fase 0.1-0.3**: Fixes de infraestructura (completado)
3. ✅ **Fase 1**: Reducción de commits DB (completado)
4. ✅ **Fase 2**: Pool Celery singleton (completado)
5. ✅ **Fase 3**: Optimización pool PostgreSQL (completado)
6. ✅ **Fase 5**: Nginx buffering OFF (completado pero REGRESIÓN)
7. ⏳ **Fase 4**: Investigación bloqueos DB
8. ⏳ **Fase 6**: Async file writing streaming
9. ⏳ **Fase 7**: Escalamiento workers

---

## 🧪 Proceso de Validación

### Después de Cada Fase:

1. **Ejecutar pruebas**:
   ```bash
   # 1 VU - 100MB
   k6 run K6/0unaPeticion.js \
     -e BASE_URL=http://localhost:8080 \
     -e FILE_PATH='/path/to/100MB.mov' \
     -e TITLE='Test' \
     -e ACCESS_TOKEN='...'

   # 5 VUs - 100MB
   k6 run K6/1sanidad.js \
     -e BASE_URL=http://localhost:8080 \
     -e FILE_PATH='/path/to/100MB.mov' \
     -e TITLE='Test' \
     -e ACCESS_TOKEN='...'
   ```

2. **Documentar resultados**:
   - Tiempo 1 VU
   - Tiempo p95 bajo 5 VUs
   - Waiting vs Sending time

3. **Decidir**: Continuar con siguiente fase o investigar problemas

---

## ⚠️ Lecciones Aprendidas

### ✅ Lo que FUNCIONA:
- Ajustar healthchecks de infraestructura
- Separar configuración local vs cloud

### ❌ Lo que NO funciona:
- `aiofiles` sin streaming (leer todo en memoria) → empeora performance
- Quitar `seek(0)` antes de leer → causa archivos vacíos

### 🎓 Principios:
1. **Medir primero**, optimizar después
2. **Una fase a la vez**, midiendo impacto
3. **Async no siempre es mejor**: overhead puede empeorar
4. **Concurrencia es el problema real**, no velocidad individual

---

## 📈 Métricas de Éxito

**Meta final**: 100MB en **<1s** bajo condiciones normales

**Indicadores**:
- ✅ 1 VU: <1s para 100MB
- ✅ 5 VUs: p95 <3s para 100MB
- ✅ Waiting time <30% del total
- ✅ Success rate >99%

---

**Última actualización**: 2025-11-01  
**Branch**: develop  
**Línea base**: ver `BASELINE.md`
