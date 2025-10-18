# Arquitectura de RabbitMQ - Sistema de Procesamiento de Videos

## Propósito

Usamos RabbitMQ como broker de tareas para Celery. Elegimos RabbitMQ porque ofrece colas durables, confirmaciones, dead-lettering nativo (DLX/DLQ) y herramientas de operación (management UI) que facilitan manejar jobs largos y críticos como el procesamiento de video.

## Provisión Automática

Las colas, exchanges y bindings se crean automáticamente al levantar RabbitMQ usando `rabbitmq/definitions.json` (montado en el contenedor). Esto crea las estructuras necesarias antes de que arranque la aplicación.

## Topología Creada

### Exchanges

- **`video`** (direct) - Exchange principal donde se publican tareas de procesamiento
- **`video-dlx`** (direct) - Exchange destino para dead-letter (mensajes muertos)
- **`video-retry`** (direct) - Exchange usado para queues de retry con TTL

### Queues

#### `video_tasks` (cola principal)
- Tipo: durable
- Argumentos:
  - `x-dead-letter-exchange: video-dlx`
  - `x-dead-letter-routing-key: video.dlq`
- Descripción: Si un mensaje es rechazado o enviado a DLX, acaba en `video_dlq`

#### `video_retry_60s` (cola de reintento)
- Tipo: durable
- Argumentos:
  - `x-message-ttl: 60000` (60 segundos)
  - `x-dead-letter-exchange: video`
- Descripción: Se usa para backoff automático. Publicar en esta cola retrasa la re-entrega aproximadamente 60 segundos

#### `video_dlq` (Dead Letter Queue)
- Tipo: durable
- Descripción: Cola DLQ donde terminan los mensajes que no se pudieron procesar definitivamente

## Flujo de Mensajes

### Flujo Normal

1. Un productor (API o Celery) publica un mensaje a la exchange `video` con routing key `video`
2. El mensaje llega a `video_tasks`
3. El worker consume desde `video_tasks` (con acks tardíos recomendados)

### Flujo de Reintento

Si la tarea falla y se decide reintentar, existen dos opciones:

#### Opción 1: Reintento por Celery (task.retry)
- Lógica en la aplicación
- No usa necesariamente las colas TTL de RabbitMQ

#### Opción 2: Reintento por colas TTL (recomendado)
1. El worker publica el mensaje en `video_retry_60s` (o en otra cola retry con TTL mayor)
2. RabbitMQ mantiene el mensaje durante el TTL (60s)
3. Cuando expira el TTL, el broker re-publica el mensaje automáticamente a la exchange `video`
4. El mensaje vuelve a `video_tasks` para ser procesado de nuevo

### Flujo de Dead Letter

Si un mensaje supera el límite de reintentos o se rechaza sin requeue:
1. La cola está configurada para enviarlo a `video-dlx`
2. Por binding, terminará en `video_dlq`
3. El mensaje queda disponible para inspección manual

## Ventajas de este Diseño

- **Durabilidad**: Las colas son `durable`, sobreviven a reinicios del broker
- **DLQ nativo**: RabbitMQ maneja dead-lettering sin necesidad de código adicional en el broker (usando `x-dead-letter-exchange`)
- **Retries con backoff**: Las colas TTL permiten implementar backoff automático sin lógica compleja en el worker
- **Separación de responsabilidades**: El broker gestiona reentregas y expiraciones, la app se preocupa solo por ejecutar la tarea

## Configuración Recomendada en Celery (Worker)

```python
# worker/celery_app.py
task_acks_late = True                # Ack solo después de completar la tarea
worker_prefetch_multiplier = 1      # Evita que un worker reserve muchas tareas
```

Declarar `task_queues` en `worker/celery_app.py` para alinear nombres y argumentos con las definitions (opcional si ya provisionas desde RabbitMQ).

## Herramientas de Monitoreo y Operación

### Management UI
- URL: http://localhost:15672
- Usuario: `rabbit`
- Contraseña: `rabbitpass`
- Funcionalidad: Ver exchanges, queues, bindings, mensajes en tiempo real

### CLI - Ver colas
```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

### CLI - Inspeccionar mensajes DLQ
Desde UI o con `rabbitmqadmin` / `rabbitmqctl`

## Reencolar desde DLQ

### Opción 1: Manual vía Management UI
1. Seleccionar mensajes desde `video_dlq`
2. Re-publicarlos a la exchange `video` o moverlos directamente a `video_tasks`
3. La UI permite reenviar mensajes con facilidad

### Opción 2: Script Python (kombu/pika)
Leer la cola `video_dlq`, parsear el payload JSON y volver a publicar con los headers/args deseados a la exchange `video`.

### Opción 3: Comando rabbitmqadmin
Útil en pipelines operativos para re-publicar mensajes de forma automatizada.

## Backoff Exponencial (Futuro)

Si en el futuro quieres backoff exponencial u otros patrones, puedes:
1. Añadir múltiples colas de retry con TTLs diferentes:
   - `video_retry_30s` (30 segundos)
   - `video_retry_2m` (2 minutos)
   - `video_retry_10m` (10 minutos)
2. Publicar en la cola adecuada según el número de intentos
3. El patrón sigue siendo el mismo: TTL → DLX → vuelve a `video_tasks`

## Comandos Útiles

### Reconstruir y levantar worker después de cambios
```bash
docker compose build worker
docker compose up -d
```

### Listar colas
```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

### Ver definiciones cargadas
```bash
docker compose exec rabbitmq cat /etc/rabbitmq/definitions.json
```

## Notas Operativas

- Las credenciales en `compose.yaml` son para desarrollo. En producción usa secretos y controles de acceso.
- Si quieres que provisionamiento sea responsabilidad de la app en vez de `definitions.json`, puedes añadir la declaración de colas en `worker/celery_app.py`.
- Esta arquitectura está diseñada para desarrollo local. Para producción considera RabbitMQ en cluster con alta disponibilidad.

## Referencias

- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Celery with RabbitMQ](https://docs.celeryproject.org/en/stable/getting-started/brokers/rabbitmq.html)
- [RabbitMQ Dead Letter Exchanges](https://www.rabbitmq.com/dlx.html)
- [RabbitMQ TTL](https://www.rabbitmq.com/ttl.html)
