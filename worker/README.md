# Worker de procesamiento de video (Python + Celery + Redis)

Este worker ejecuta tareas Celery que simulan el procesamiento de archivos de video.

## Cómo ejecutarlo

```bash
docker compose up --build
```

## Comprobar que funciona

Una vez corriendo, abre una shell dentro del contenedor `video-worker`:

```bash
docker exec -it video-worker python3
```

Y ejecuta:

```python
from tasks.process_video import run
run.delay('/videos/demo.mp4')
```
