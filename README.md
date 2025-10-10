# misw4204-2025-15-desarrollo-de-sw-en-la-nube

Propósito principal: alojar y facilitar el desarrollo local de una herramienta de procesamiento de video. El sistema objetivo es una API que recibe uploads de video, encola trabajos y un conjunto de workers que procesan esos videos (cortes, marcas de agua, transcodificación, cambio de resolución, etc.).

Observabilidad: además del motor de procesamiento, este repositorio incluye un stack de observabilidad (Grafana, Prometheus, Loki, Promtail y Tempo) para monitorizar métricas, logs y trazas mientras desarrollas y pruebas la solución.

A continuación encontrará instrucciones rápidas para ejecutar el stack completo, ejecutar servicios por separado y una breve explicación del propósito de cada componente.

## Resumen rápido de lo que hace este repo

- Levantar el ecosistema para el procesamiento de videos para ANB
- Provisión de un stack de observabilidad listo para usar en Docker Compose.
- Configuraciones de Prometheus, Loki, Promtail y Tempo incluidas.
- Provisionamiento de datasources y dashboards para Grafana (carpeta `./grafana/provisioning` y `./grafana/dashboards`).

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

## Ejecutar un servicio por separado

Puede levantar solo el servicio que necesites. Ejemplos (PowerShell):

```powershell
# Levantar solo Grafana
docker compose -f compose.yaml up -d grafana

# Levantar solo Prometheus
docker compose -f compose.yaml up -d prometheus

# Levantar solo Loki
docker compose -f compose.yaml up -d loki

# Levantar solo Promtail
docker compose -f compose.yaml up -d promtail

# Levantar solo Tempo
docker compose -f compose.yaml up -d tempo
```

Para ver logs en vivo de un servicio:

```powershell
docker compose -f compose.yaml logs -f grafana
```

Y para listar contenedores creados por el compose:

```powershell
docker compose -f compose.yaml ps
```

## Puertos expuestos por defecto

- Grafana: http://localhost:3000  (user: admin / pass: admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100
- Tempo (OTLP HTTP): http://localhost:4318
- Tempo (Jaeger UI): http://localhost:16686

## Rutas importantes en este repo

- `compose.yaml` — archivo Docker Compose principal.
- `./grafana/provisioning/` — configuración para provisionar datasources y dashboards en Grafana.
- `./grafana/dashboards/` — dashboards JSON que Grafana cargará por defecto (si existen).
- `./prometheus/prometheus.yml` — configuración de Prometheus.
- `./loki/config.yml` — configuración de Loki.
- `./promtail/config.yml` — configuración de Promtail (recolección de logs).
- `./tempo/config.yml` — configuración de Tempo (tracing).

## Sección por servicio

### Nginx (proxy inverso)

Propósito: puerta de entrada y protección para la API. Nginx actúa como proxy inverso que recibe las subidas de archivos, las bufferiza en disco temporal y luego entrega el archivo a la API por la red local. De este modo, la API no queda bloqueada atendiendo uploads lentos.

Cómo usar: el `docker compose` incluido levanta un servicio `nginx` que, por defecto, escucha en `http://localhost:8080` y reenvía peticiones a `http://api:8000`.

Puntos clave:
- Protege la API de clientes con conexiones lentas.
- Bufferiza el cuerpo de la petición en `/var/tmp/nginx` (montado en el volumen `proxy_temp`).
- Controla límites como `client_max_body_size` y `client_body_timeout` desde la configuración del proxy.

### Grafana

Propósito: Panel de visualización único. Grafana muestra métricas, logs y trazas en dashboards amigables. Aquí se pueden visualizar métricas de Prometheus, logs desde Loki y trazas almacenadas en Tempo.

Cómo usar: abrir http://localhost:3000 y entrar con `admin` / `admin`. Los datasources prometheus/loki/tempo deberían estar provisionados automáticamente si las carpetas están presentes.

### Prometheus

Propósito: recolectar y almacenar métricas numéricas (por ejemplo latencias, contadores de requests, uso de CPU/RAM). Prometheus 'raspa' endpoints `/metrics` expuestos por servicios instrumentados.

Cómo usar: abre http://localhost:9090 para ejecutar queries y verificar targets. Asegúrate de que tu aplicación exponga `/metrics` si quieres que Prometheus la raspe.

### Loki

Propósito: almacenamiento y búsqueda de logs. Loki indexa metadatos (labels) y guarda el contenido de logs, optimizando búsquedas por etiquetas (por ejemplo `job_id` o `service`).

Cómo usar: Grafana usa Loki como datasource para buscar logs. Promtail (o Fluent Bit) se encarga de enviar logs a Loki.

### Promtail

Propósito: recolector de logs que envía entradas a Loki. En este repo la configuración de Promtail está lista para leer logs de contenedores Docker o archivos del host según lo configures.

Cómo usar: revisa `./promtail/config.yml` para ajustar las rutas que Promtail debe vigilar.

### Tempo

Propósito: almacenamiento de trazas distribuidas (OpenTelemetry/Jaeger compatible). Permite seguir una petición o un job a través de servicios (API → worker → ffmpeg → storage).

Cómo usar: configura tus SDKs OpenTelemetry para enviar spans a `http://localhost:4318` (OTLP HTTP). Luego podrás ver trazas en Grafana o en la Jaeger UI en `:16686`.


## Consejos rápidos y resolución de problemas

- Si un puerto ya está en uso, cambia el mapeo en `compose.yaml` antes de levantar.
- Si Grafana no muestra datasources, verifica que `./grafana/provisioning` exista y tenga los archivos `.yaml` con la configuración.
- Ver logs de un servicio con `docker compose -f compose.yaml logs -f <servicio>`.
- Si el disco temporal del proxy (si lo agregas) se llena, revisa la configuración del volumen y limpia archivos temporales.

## ¿Qué puedo hacer ahora?

- Puedo añadir un `docker-compose.override.yml` de ejemplo con un Nginx proxy delante de tu API para pruebas de upload.
- Puedo crear dashboards base para uploads (latencias, tamaño, errores) y para el pipeline de video.
- Puedo añadir instrucciones para instrumentar una API en Python (FastAPI) con Prometheus + OpenTelemetry.

Elige qué prefieres que haga a continuación y lo implemento.



