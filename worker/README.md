# Worker de procesamiento de video (Python + Celery)
 
 ## ⚠️ Configuración Inicial (Requerido)
 
 Este servicio requiere archivos multimedia (assets) para funcionar correctamente (marca de agua, intro/outro). Estos archivos **no están incluidos en el repositorio**.
 
 1. Ve a la Wiki del proyecto: [Assets Worker](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/assets-worker)
 2. Descarga los archivos requeridos (`watermark.png`, `inout.mp4`, etc.).
 3. Colócalos en la carpeta `worker/assets/` dentro de este directorio.
 
 ```bash
 # Estructura esperada
 worker/
 ├── assets/
 │   ├── watermark.png
 │   └── inout.mp4
 ├── ...
 ```
 
 ---

Este worker procesa videos usando ffmpeg y recibe trabajos desde RabbitMQ (vía Celery).
Desde este refactor, el worker ya no depende del filesystem local: descarga los insumos desde S3 y sube los resultados a S3. Además, actualiza el estado en la misma base de datos (RDS) que usa el API core.

## Variables de entorno relevantes

- Celery / MQ
	- CELERY_BROKER_URL
	- CELERY_RESULT_BACKEND

- Almacenamiento (S3)
		- STORAGE_BACKEND=s3 (habilita S3 en el core; el worker detecta rutas `s3://`)
		- S3_BUCKET, S3_REGION
		- S3_ENDPOINT_URL (opcional para S3 compatibles)
		- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, (AWS_SESSION_TOKEN opcional)
			- En este laboratorio son REQUERIDAS (no hay IAM). El worker falla si faltan.

- Base de datos (RDS)
	- DB_URL_CORE (obligatorio) en formato async de SQLAlchemy: `postgresql+asyncpg://...`
		- El worker convierte automáticamente a sync (`postgresql://...`) para `psycopg`.

- Rutas locales (solo si se usa almacenamiento local)
	- UPLOAD_DIR=/app/storage/uploads
	- PROCESSED_DIR=/app/storage/processed

## Cómo ejecutarlo en Docker Compose

```bash
docker compose --profile worker up --build -d
```

## Probar rápido dentro del contenedor

```bash
docker exec -it video-worker python - << 'PY'
from tasks.process_video import run

# Ejemplo S3 (el core publica así):
# run.delay("video-id", "s3://<bucket>/uploads/2025/11/02/archivo.mp4", "corr-id")

print('OK: worker importado')
PY
```

Para pruebas locales sin S3 se mantiene el modo anterior (filesystem), enviando rutas bajo `/mnt/uploads/...`.
