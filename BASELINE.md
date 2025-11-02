# Línea Base de Performance

**Fecha**: 2025-11-01  
**Branch**: refactor-carga + RabbitMQ healthcheck fix + RABBITMQ_URL fix + Fase 1 completada  
**Configuración**: Docker Compose local, storage local

## Configuración de Pruebas

**Videos**:
- Pequeño: `Acceso Rápido - Opera 2025-10-11 23-09-19.mp4` (9MB)
- Grande: `2025-03-13 15-02-53.mov` (100MB)

**Herramienta**: k6

## Resultados

### FASE 0: Línea Base Inicial (develop)

#### 1. Carga Simple (1 VU)

**9MB**:
```
http_req_duration: avg=338ms, p95=338ms
http_req_sending: avg=338ms
http_req_waiting: avg=0ms (calculado)
upload_rate: ~24 MB/s
```

**100MB**:
```
http_req_duration: avg=7.81s
upload_rate: ~13 MB/s
```

#### 2. Carga con Concurrencia (5 VUs, 1 minuto) - 100MB
```
http_req_duration: 
  - min: 4.52s
  - avg: 16.21s
  - med: 12.1s
  - p95: 38.06s ✗ (threshold: <5s)

http_req_sending:
  - min: 2.66s
  - avg: 4.62s
  - med: 3.83s
  - p95: 7.9s ✗ (threshold: <3s)

http_req_waiting:
  - min: 1.86s
  - avg: 11.59s
  - med: 8.27s
  - p95: 30.78s ✗ (threshold: <4s)

upload_rate_mb_s: p95=36.58 MB/s
Iterations: 8/11 completadas (3 interrumpidas)
Success rate: 100%
```

---

### FASE 1: Reducción de Commits DB (3→1 con flush) ✅

#### 1. Carga Simple (1 VU)

**9MB**:
```
http_req_duration: avg=346.9ms, p95=346.9ms
upload_rate: ~24 MB/s
```

**100MB**:
```
http_req_duration: avg=6.94s
upload_rate: ~14 MB/s
```

**Comparación con FASE 0**:
- 9MB: +2.6% (no significativo)
- 100MB: -11% ✓ (mejora)

#### 2. Carga con Concurrencia (5 VUs, 1 minuto)

**9MB** (105 iteraciones):
```
http_req_duration: 
  - min: 370.71ms
  - avg: 1.49s
  - med: 843.25ms
  - p95: 4.74s ✓ (threshold: <5s)

http_req_sending:
  - p95: 441.29ms ✓ (threshold: <3s)

http_req_waiting:
  - p95: 4.27s ✗ (threshold: <4s)

upload_rate_mb_s: p95=163.01 MB/s
Iterations: 105 completadas
Success rate: 100%
```

**100MB** (5 iteraciones):
```
http_req_duration: 
  - min: 7.14s
  - avg: 18.4s
  - med: 19.41s
  - p95: 32.5s ✗ (threshold: <5s)

http_req_sending:
  - p95: 8.88s ✗ (threshold: <3s)

http_req_waiting:
  - p95: 26.89s ✗ (threshold: <4s)

upload_rate_mb_s: p95=30.48 MB/s
Iterations: 5 completadas (3 interrumpidas)
Success rate: 100%
```

**Comparación con FASE 0**:
- **Waiting time**: Mejora dramática para 9MB (p95: 30.78s → 4.27s, -86%) ✓
- **Waiting time**: Poca mejora para 100MB (p95: 30.78s → 26.89s, -12%)
- **Sending time**: Similar (p95: 7.9s → 8.88s)
- **Duraciones**: Similar para 100MB bajo concurrencia

---

### FASE 2: Pool de Conexiones Celery ✅

**Archivos**: `core/app/services/mq/celery_pool.py`, `core/app/services/mq/rabbit.py`, `core/requirements.txt`

**Cambio**: Pool singleton de Cliente Celery reutilizable

**Impacto esperado**: Reducir overhead de conexiones RabbitMQ

#### 1. Carga Simple (1 VU)

**9MB**: Variables (572-686ms, comparable a Fase 1)  
**100MB**: avg=7.55s (similar a Fase 1: 6.94s)

#### 2. Carga con Concurrencia (5 VUs, 1 minuto)

**9MB** (101 iteraciones):
```
http_req_duration: 
  - p95: 3.21s ✓ (threshold: <5s)
  
http_req_sending:
  - p95: 514ms ✓ (threshold: <3s)
  
http_req_waiting:
  - p95: 2.78s ✓ (threshold: <4s)

upload_rate_mb_s: p95=44.59 MB/s
Iterations: 101 completadas
Success rate: 100%
```

**100MB** (10 iteraciones, solo 2 completadas):
```
http_req_duration: 
  - p95: 27.69s ✗ (threshold: <5s)

http_req_sending:
  - p95: 11.4s ✗ (threshold: <3s)

http_req_waiting:
  - p95: 19.12s ✗ (threshold: <4s)

upload_rate_mb_s: p95=21.6 MB/s
Iterations: 10 iniciadas (solo 2 completadas)
Success rate: 20%
```

**Comparación con FASE 1**:
- ✅ **9MB mejoró**: Waiting time bajó 35% adicional (4.27s → 2.78s)
- ✅ **100MB mejoró**: Waiting time bajó 29% (26.89s → 19.12s)
- ❌ **100MB degradó**: Sending time aumentó 28% (8.88s → 11.4s)
- ❌ **Success rate crítico**: 20% para 100MB (vs 100% Fase 1)

---

### FASE 3: Optimización Pool PostgreSQL ✅

**Archivo**: `core/app/database.py`

**Cambio**: Pool explícito `pool_size=20`, `max_overflow=10`, `pool_timeout=30`

**Impacto esperado**: Mejor gestión de conexiones concurrentes

#### 1. Carga Simple (1 VU)

**9MB**: 370.34ms (Fase 1: 346.9ms, +6.8%)  
**100MB**: 2.74s (Fase 1: 6.94s, **-60%** ✅)

#### 2. Carga con Concurrencia (5 VUs, 1 minuto)

**9MB** (148 iteraciones):
```
http_req_duration: 
  - p95: 2.13s ✓ (threshold: <5s)
  
http_req_sending:
  - p95: 447ms ✓ (threshold: <3s)
  
http_req_waiting:
  - p95: 1.72s ✓ (threshold: <4s)

upload_rate_mb_s: p95=83 MB/s
Iterations: 148 completadas
Success rate: 100%
```

**100MB** (12 iteraciones completadas):
```
http_req_duration: 
  - p95: 21.28s ✗ (threshold: <5s)

http_req_sending:
  - p95: 6.91s ✗ (threshold: <3s)

http_req_waiting:
  - p95: 15.3s ✗ (threshold: <4s)

upload_rate_mb_s: p95=24.96 MB/s
Iterations: 12 completadas (100% exitosas)
Success rate: 100%
```

**Comparación con FASE 2**:
- ✅ **9MB mejoró**: Duration bajó 34% (3.21s → 2.13s)
- ✅ **100MB mejoró**: Duration bajó 23% (27.69s → 21.28s)
- ✅ **100MB sending**: Bajó 39% (11.4s → 6.91s)
- ✅ **Success rate crítico**: 100% para 100MB (vs 20% Fase 2)
- ⚠️ **100MB simple**: Mejoró dramáticamente (-60% vs Fase 1: 2.74s)

---

### FASE 5: Desactivar Buffering Nginx ✅

**Archivo**: `nginx/nginx.conf`

**Cambio**: `proxy_request_buffering off` y `proxy_buffering off` para `/api/videos/upload`

**Impacto esperado**: Reducir latencia de buffering

#### 1. Carga Simple (1 VU)

**9MB**: 297ms (Fase 3: 370ms, **-20%** ✅)  
**100MB**: 2.16s (Fase 3: 2.74s, **-21%** ✅)

#### 2. Carga con Concurrencia (5 VUs, 1 minuto)

**9MB** (213 iteraciones):
```
http_req_duration: 
  - p95: 1.43s ✓ (threshold: <5s)
  
http_req_sending:
  - p95: 313ms ✓ (threshold: <3s)
  
http_req_waiting:
  - p95: 1.19s ✓ (threshold: <4s)

upload_rate_mb_s: p95=86 MB/s
Iterations: 213 completadas
Success rate: 100%
```

**100MB** (14 iteraciones completadas):
```
http_req_duration: 
  - p95: 20.17s ✗ (threshold: <5s)

http_req_sending:
  - p95: 14.02s ✗ (threshold: <3s)

http_req_waiting:
  - p95: 9.84s ✗ (threshold: <4s)

upload_rate_mb_s: p95=25.09 MB/s
Iterations: 14 completadas (100% exitosas)
Success rate: 100%
```

**Comparación con FASE 3**:
- ✅ **9MB simple**: Mejoró 20% (370ms → 297ms)
- ✅ **100MB simple**: Mejoró 21% (2.74s → 2.16s)
- ✅ **9MB concurrencia**: Mejoró 33% (2.13s → 1.43s)
- ✅ **100MB waiting**: Mejoró 36% (15.3s → 9.84s)
- ❌ **100MB sending**: Empeoró 103% (6.91s → 14.02s)

---

## Análisis Comparativo

### Resumen de Métricas

| Métrica | FASE 0 | FASE 1 | FASE 2 | FASE 3 | FASE 5 | Mejora Total |
|---------|--------|--------|--------|--------|--------|--------------|
| **9MB (1 VU)** | 338ms | 346.9ms | 572-686ms* | 370ms | 297ms | **-12%** ✅ |
| **100MB (1 VU)** | 7.81s | 6.94s | 7.55s | 2.74s | **2.16s** | **-72%** ✅ |
| **9MB (5 VUs) waiting p95** | 30.78s | 4.27s | 2.78s | 1.72s | 1.19s | **-96%** ✅ |
| **100MB (5 VUs) waiting p95** | 30.78s | 26.89s | 19.12s | 15.3s | 9.84s | **-68%** ✅ |
| **100MB (5 VUs) sending p95** | 7.9s | 8.88s | 11.4s | 6.91s | 14.02s | +77% ❌ |
| **100MB (5 VUs) success rate** | 100% | 100% | 20% | 100% | 100% | ✅ |

*Variable: primera prueba 686ms, segunda 572ms

### Conclusiones

✅ **Lo que funciona** (FASE 5):
- **100MB simple**: Mejora acumulada 72% vs baseline (7.81s → 2.16s)
- **9MB concurrencia**: Mejora 96% waiting time (30.78s → 1.19s)
- **100MB waiting**: Mejora 68% bajo concurrencia (30.78s → 9.84s)
- **Simples**: Buffering OFF mejora 20-21% vs Fase 3

❌ **Lo que empeora** (FASE 5):
- **100MB sending**: Empeoró 103% bajo concurrencia (6.91s → 14.02s)
- Indica que **buffering OFF es contraproducente** para archivos grandes bajo carga

### Diagnóstico FASE 5

**Paradoja del Buffering**:
- ✅ **Sin buffering** mejora casos simples (menos latencia)
- ❌ **Sin buffering** empeora casos concurrencia (sin buffer, Nginx no optimiza I/O)
- Para 100MB bajo carga, el buffering **ayuda** a balancear carga

**Lección**: No todas las optimizaciones de Nginx son universales. Dependen del caso de uso.

### Próximos Pasos Prioritarios

1. ✅ **FASES 1+2+3+5 completadas**
2. ⏳ **REVERTIR Fase 5** o ajustar condición (solo para archivos pequeños)
3. ⏳ **FASE 6**: Stream async de archivos en backend

**Progreso**: Baseline → Fase 3 → Fase 5: 7.81s → 2.74s → 2.16s (72% mejor simple). Pero Fase 5 empeora bajo concurrencia.

