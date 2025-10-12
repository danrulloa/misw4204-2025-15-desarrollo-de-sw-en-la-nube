# misw4204-2025-15-desarrollo-de-sw-en-la-nube

Propósito principal: alojar y facilitar el desarrollo local de una herramienta de procesamiento de video. El sistema objetivo es una API que recibe uploads de video, encola trabajos y un conjunto de workers que procesan esos videos (cortes, marcas de agua, transcodificación, cambio de resolución, etc.).

A continuación encontrará instrucciones rápidas para ejecutar el stack completo, ejecutar servicios por separado y una breve explicación del propósito de cada componente.

## Resumen rápido de lo que hace este repo

- Levantar el ecosistema para el procesamiento de videos para ANB

## Requisitos

- Docker Desktop (o Docker Engine) instalado y corriendo.
- Docker Compose (v2 con el comando `docker compose` o la alternativa `docker-compose`).

Nota: Los ejemplos usan el nombre del archivo `compose.yaml` que está en la raíz del repo.

## Ejecutar todo el stack (rápido)

En PowerShell ejecuta:

```powershell
docker compose -f compose.yaml up -d
```

Esto levantará los servicios definidos en `compose.yaml`. Para detenerlos y remover los contenedores:

```powershell
docker compose -f compose.yaml down
```

Si quieres forzar la descarga de imágenes y recrear:

```powershell
docker compose -f compose.yaml pull ; docker compose -f compose.yaml up -d --force-recreate --remove-orphans
```

## Sección por servicio

### Nginx (proxy inverso)

Propósito: puerta de entrada y protección para la API. Nginx actúa como proxy inverso que recibe las subidas de archivos, las bufferiza en disco temporal y luego entrega el archivo a la API por la red local. De este modo, la API no queda bloqueada atendiendo uploads lentos.

Cómo usar: el `docker compose` incluido levanta un servicio `nginx` que, por defecto, escucha en `http://localhost:8080` y reenvía peticiones a `http://api:8000`.

Puntos clave:
- Protege la API de clientes con conexiones lentas.
- Bufferiza el cuerpo de la petición en `/var/tmp/nginx` (montado en el volumen `proxy_temp`).
- Controla límites como `client_max_body_size` y `client_body_timeout` desde la configuración del proxy.

### RabbitMQ y definición de colas

Propósito: usamos RabbitMQ como broker de tareas para Celery. Elegimos RabbitMQ porque ofrece colas durables, confirmaciones, dead-lettering nativo (DLX/DLQ) y herramientas de operación (management UI) que facilitan manejar jobs largos y críticos como el procesamiento de video.

Archivo de provisión
- Las colas/exchanges/bindings se crean automáticamente al levantar RabbitMQ usando `rabbitmq/definitions.json` (montado en el contenedor). Esto crea las estructuras necesarias antes de que arranque la aplicación.

Topología creada
- Exchanges:
	- `video` (direct) — exchange principal donde se publican tareas de procesamiento.
	- `video-dlx` (direct) — exchange destino para dead-letter (mensajes muertos).
	- `video-retry` (direct) — exchange usado para queues de retry con TTL.

- Queues:
	- `video_tasks` — cola principal (durable). Tiene argumento `x-dead-letter-exchange: video-dlx` y `x-dead-letter-routing-key: video.dlq`. Si un mensaje es rechazado o enviado a DLX, acaba en `video_dlq`.
	- `video_retry_60s` — cola de reintento con `x-message-ttl: 60000` (60s) y `x-dead-letter-exchange: video`. Se usa para backoff automático: publicar en esta cola retrasa la re-entrega ~60s.
	- `video_dlq` — cola DLQ (durable) donde terminan los mensajes que no se pudieron procesar definitivamente.

Flujo de mensajes
- Un productor (por ejemplo la API o Celery) publica un mensaje a la exchange `video` con routing key `video` → el mensaje llega a `video_tasks`.
- El worker consume desde `video_tasks` (col acks tardíos recomendados). Si la tarea falla y se decide reintentar, existen dos opciones:
	1. Reintento por Celery (task.retry) — lógica en la aplicación. No usa necesariamente las colas TTL de Rabbit.
	2. Reintento por colas TTL: el worker publica el mensaje en `video_retry_60s` (o en otra cola retry con TTL mayor); cuando expira el TTL RabbitMQ reenviará el mensaje a la exchange `video` y volverá a `video_tasks`.
- Si un mensaje supera el límite de reintentos o se rechaza sin requeue, la cola está configurada para enviarlo a `video-dlx` y, por binding, terminará en `video_dlq` para inspección manual.

Por qué este diseño
- Durabilidad: las colas son `durable`, por lo que sobreviven a reinicios del broker.
- DLQ nativo: RabbitMQ maneja dead-lettering sin necesidad de código adicional en el broker (lo hicimos con `x-dead-letter-exchange`).
- Retries con backoff: las colas TTL `video_retry_60s` permiten implementar backoff automático sin lógica compleja en el worker.

Configuración recomendada en Celery (worker)
- `task_acks_late = True` (ack sólo después de completar la tarea correctamente).
- `worker_prefetch_multiplier = 1` (evita que un worker reserve muchas tareas que luego perdería si cae).
- Declarar `task_queues` en `worker/celery_app.py` para alinear nombres y argumentos con las definitions (opcional si ya provisionas desde RabbitMQ).

Comprobaciones y herramientas
- UI de management: http://localhost:15672  (user: `rabbit`, pass: `rabbitpass`). Aquí verás exchanges, queues y bindings.
- Ver colas (CLI dentro del contenedor):
	- `docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers`
- Inspeccionar mensajes DLQ desde UI o con `rabbitmqadmin` / `rabbitmqctl`.

Reencolar desde DLQ (opciones)
- Manual via management UI: seleccionar mensajes desde `video_dlq` y re-publicarlos a la exchange `video` o moverlos a `video_tasks` (la UI permite reenviar).
- Script vía Python (kombu/pika): leer la cola `video_dlq`, parsear el payload JSON y volver a publicar con los headers/args deseados a la exchange `video`.
- Comando `rabbitmqadmin` para re-publicar (útil en pipelines operativos).

Notas operativas
- Credenciales en `compose.yaml` son para desarrollo. En producción usa secretos y controles de acceso.
- Si quieres que provisionamiento sea responsabilidad de la app en vez de `definitions.json`, puedo añadir la declaración de colas en `worker/celery_app.py`.

¿Quieres que añada al repo un pequeño script de reencolado (Python) y un snippet en `worker/celery_app.py` que declare las colas en tiempo de arranque? Puedo implementarlo a continuación.

## Decisiones finales sobre retries y configuración aplicada

Hemos decidido implementar reintentos y dead-lettering usando colas TTL en RabbitMQ (patrón TTL -> DLX) en lugar de añadir lógica de retry compleja dentro de la aplicación. Esto mantiene la app más simple y delega el backoff/reintento al broker.

Resumen de la configuración aplicada
- Provisionamiento: `rabbitmq/definitions.json` crea las exchanges/queues/bindings al arrancar RabbitMQ (carga automática con `RABBITMQ_LOAD_DEFINITIONS=1`).
- Cola principal: `video_tasks` (durable) con DLX apuntando a `video-dlx` -> `video_dlq`.
- Cola de retry: `video_retry_60s` con `x-message-ttl: 60000` y dead-letter a la exchange `video`. Publicar en esta cola retrasa la re-entrega ~60s.
- DLQ: `video_dlq` para inspección manual y reencolado.

Cambios en el worker (implementados)
- `worker/celery_app.py` ahora:
	- Lee `CELERY_BROKER_URL` y `CELERY_RESULT_BACKEND` desde las variables de entorno definidas en `compose.yaml`.
	- Declara las `task_queues` (video_tasks, video_retry_60s, video_dlq) con los argumentos necesarios (DLX, TTL) para alinear la app con las definitions de RabbitMQ.
	- Configura `task_acks_late = True` y `worker_prefetch_multiplier = 1` para mejorar la fiabilidad: ack sólo después de procesada la tarea y evitar reservar muchas tareas por worker.
	- Añade un handler `task_failure` que escribe metadata en la exchange `video-dlx` (esto es informativo; la DLX del broker seguirá manejando mensajes rechazados según las policies).

Cómo funcionan los reintentos (operacional)
- Flujo típico para un reintento por TTL (sin tocar la app internamente):
	1. El worker detecta que la tarea debe reintentarse (por política interna o tras fallo) y publica el mensaje en la exchange `video-retry` con routing key `video.retry.60` (es decir, a la cola `video_retry_60s`).
	2. RabbitMQ mantiene el mensaje en `video_retry_60s` durante el TTL (60s).
	3. Cuando expira el TTL el broker re-publica el mensaje automáticamente a la exchange `video` (dead-letter) y el mensaje vuelve a `video_tasks` para ser procesado de nuevo.

Notas operativas y comandos útiles
- Reconstruir y levantar worker después de cambios:

```powershell
docker compose -f compose.yaml build worker
docker compose -f compose.yaml up -d
```

- Inspeccionar colas y mensajes en RabbitMQ Management UI: http://localhost:15672  (rabbit/rabbitpass).
- Listar colas por CLI:

```powershell
docker compose exec rabbitmq rabbitmqctl list_queues name messages consumers
```

- Reencolar manualmente desde DLQ (UI o script): puedes elegir reenviar a `video` o publicarlo en `video_retry_60s` para aplicar backoff.

Consideraciones finales
- Esta aproximación permite gestionar reintentos con backoff sin añadir lógica de retry dentro de las tareas. Es robusta y separa responsabilidades: el broker gestiona reentregas y expiraciones, la app se preocupa solo por ejecutar la tarea.
- Si en el futuro quieres backoff exponencial u otros patrones, podemos añadir múltiples colas de retry con TTLs diferentes (p. ej. 30s, 2m, 10m) y publicar en la cola adecuada según el número de intentos.





