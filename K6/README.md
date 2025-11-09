# Scripts de Pruebas de Carga con k6

Este directorio contiene los scripts de k6 para realizar pruebas de carga del sistema ANB Rising Stars Showcase.

## Scripts Disponibles

### Scripts de Prueba Básicos

#### `0unaPeticion.js`
- **Propósito**: Prueba simple de una sola petición
- **Uso**: Validar que el sistema funciona correctamente antes de ejecutar pruebas de carga
- **Configuración**: 1 VU, 1 iteración
- **Endpoint**: POST `/api/videos/upload`

#### `1sanidad.js`
- **Propósito**: Prueba de sanidad (Smoke Test)
- **Uso**: Validar funcionamiento básico del sistema con carga mínima
- **Configuración**: 5 VUs durante 1 minuto
- **Endpoint**: POST `/api/videos/upload`

#### `2escalamiento.js`
- **Propósito**: Prueba de escalamiento progresivo
- **Uso**: Activar el escalado automático del ASG y medir el comportamiento bajo carga creciente
- **Configuración**: 
  - Ramp-up: 0 → 10 → 30 → 50 VUs (8 minutos)
  - Sostenida: 50 VUs durante 5 minutos
  - Ramp-down: 50 → 0 VUs (2 minutos)
- **Endpoint**: POST `/api/videos/upload`

#### `3sostenidaCorta.js`
- **Propósito**: Prueba de carga sostenida
- **Uso**: Evaluar estabilidad del sistema bajo carga constante
- **Configuración**: 
  - Ramp-up: 0 → 50 VUs (30 segundos)
  - Sostenida: 50 VUs durante 10 minutos
  - Ramp-down: 50 → 0 VUs (1 minuto)
- **Endpoint**: POST `/api/videos/upload`

### Scripts de Escenarios Específicos

#### `escenario1_get_public_videos.js`
- **Propósito**: Prueba de capacidad de la capa web (GET requests)
- **Uso**: Medir el rendimiento del endpoint público de listado de videos
- **Configuración**: 
  - Ramp-up: 0 → 50 → 100 → 150 VUs (8 minutos)
  - Sostenida: 150 VUs durante 5 minutos
  - Ramp-down: 150 → 0 VUs (2 minutos)
- **Endpoint**: GET `/api/public/videos` (sin autenticación)
- **Nota**: Este script no requiere autenticación ni archivos de video

#### `escenario2_worker_throughput.js`
- **Propósito**: Prueba de throughput del Worker
- **Uso**: Medir cuántos videos por minuto procesa el Worker
- **Configuración**: 
  - Ramp-up: 0 → 5 VUs (30 segundos)
  - Sostenida: 5 VUs durante 10 minutos
  - Ramp-down: 5 → 0 VUs (1 minuto)
- **Endpoint**: POST `/api/videos/upload`
- **Métricas**: Registra videos subidos, tiempo de upload, tasa de upload (MB/s)

## Variables de Entorno

Todos los scripts utilizan variables de entorno para configuración:

### Variables Requeridas

- `BASE_URL`: URL base del ALB (ej: `http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com`)
- `ACCESS_TOKEN`: Token JWT de autenticación (requerido para scripts de upload)
- `FILE_PATH`: Ruta al archivo de video a subir (requerido para scripts de upload)
- `TITLE`: Título del video (opcional, tiene valor por defecto)
- `UPLOAD_PATH`: Ruta del endpoint de upload (por defecto: `/api/videos/upload`)
- `PUBLIC_VIDEOS_PATH`: Ruta del endpoint público (por defecto: `/api/public/videos`)

### Ejemplo de Uso

```bash
# Desde la instancia k6 (vía SSH)
cd /home/ubuntu/anb-cloud
source k6_config.sh

# Prueba de sanidad
k6 run K6/1sanidad.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH

# Prueba de GET requests (sin autenticación)
k6 run K6/escenario1_get_public_videos.js \
  -e BASE_URL=$BASE_URL

# Prueba de Worker throughput
k6 run K6/escenario2_worker_throughput.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH
```

## Métricas Registradas

### Métricas Estándar de k6
- `http_reqs`: Número total de requests HTTP
- `http_req_duration`: Duración de requests (p50, p95, p99)
- `http_req_failed`: Tasa de errores
- `vus`: Número de usuarios virtuales

### Métricas Personalizadas
- `timing_blocked`: Tiempo bloqueado (DNS, etc.)
- `timing_connecting`: Tiempo de conexión TCP
- `timing_sending`: Tiempo de envío de datos
- `timing_waiting`: Tiempo de espera de respuesta (TTFB)
- `timing_receiving`: Tiempo de recepción de datos
- `upload_rate_mb_s`: Tasa de upload en MB/s
- `videos_uploaded`: Número de videos subidos (solo en escenario2)

## Thresholds (Umbrales)

### Scripts de Upload
- `http_req_duration`: p95 < 10 segundos
- `http_req_failed`: rate < 5%
- `http_req_sending`: p95 < 5 segundos (solo en escalamiento)
- `http_req_waiting`: p95 < 8 segundos (solo en escalamiento)

### Scripts de GET
- `http_req_duration`: p95 < 2 segundos
- `http_req_failed`: rate < 5%
- `http_reqs`: rate > 10 RPS

## Preparación

### 1. Crear Instancia EC2 para k6
Ver guía en `infra/README.md` o `infra/TROUBLESHOOTING_SSH_K6.md`

### 2. Instalar k6
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates gnupg curl
sudo gpg --no-default-keyring \
  --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install -y k6
```

### 3. Clonar Repositorio
```bash
cd /home/ubuntu
git clone https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube.git anb-cloud
cd anb-cloud
git checkout develop
```

### 4. Preparar Videos de Prueba
```bash
# Opción A: Generar videos con FFmpeg
sudo apt-get install -y ffmpeg
mkdir -p /home/ubuntu/videos-test
cd /home/ubuntu/videos-test

# Video de 10MB
ffmpeg -f lavfi -i testsrc=duration=30:size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:duration=30 \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  -t 30 video10mb.mp4

# Video de 50MB
ffmpeg -f lavfi -i testsrc=duration=120:size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:duration=120 \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 128k \
  -t 120 video50mb.mp4

# Video de 100MB
ffmpeg -f lavfi -i testsrc=duration=240:size=1920x1080:rate=30 \
  -f lavfi -i sine=frequency=1000:duration=240 \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 128k \
  -t 240 video100mb.mp4
```

### 5. Configurar Variables de Entorno
```bash
cd /home/ubuntu/anb-cloud
nano k6_config.sh
```

Contenido de `k6_config.sh`:
```bash
#!/bin/bash
export BASE_URL="http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com"
export ACCESS_TOKEN="tu_token_aqui"
export FILE_PATH_10MB="/home/ubuntu/videos-test/video10mb.mp4"
export FILE_PATH_50MB="/home/ubuntu/videos-test/video50mb.mp4"
export FILE_PATH_100MB="/home/ubuntu/videos-test/video100mb.mp4"
export TITLE="Video de prueba de carga"
export UPLOAD_PATH="/api/videos/upload"
export PUBLIC_VIDEOS_PATH="/api/public/videos"
```

```bash
chmod +x k6_config.sh
source k6_config.sh
```

### 6. Obtener Token de Acceso
```bash
# Desde tu máquina local
ALB_DNS="anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com"

# Registrar usuario (si no existe)
curl -X POST "http://$ALB_DNS/auth/api/v1/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_load_user",
    "email": "test_load@example.com",
    "password": "Test123!",
    "first_name": "Test",
    "last_name": "Load",
    "city": "Bogotá"
  }'

# Hacer login y obtener token
curl -X POST "http://$ALB_DNS/auth/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_load@example.com&password=Test123!"

# Copiar el access_token de la respuesta y actualizar k6_config.sh
```

## Ejecución de Pruebas

### Orden Recomendado

1. **Prueba de Sanidad** (`1sanidad.js`)
   - Validar que el sistema funciona correctamente
   - Duración: ~1 minuto

2. **Prueba de Escalamiento** (`2escalamiento.js`)
   - Activar escalado automático
   - Duración: ~15 minutos

3. **Prueba Sostenida** (`3sostenidaCorta.js`)
   - Evaluar estabilidad
   - Duración: ~11 minutos

4. **Prueba GET Requests** (`escenario1_get_public_videos.js`)
   - Medir capacidad de la capa web
   - Duración: ~15 minutos

5. **Prueba Worker Throughput** (`escenario2_worker_throughput.js`)
   - Medir throughput del Worker
   - Duración: ~11 minutos

### Ejecutar Pruebas

```bash
# Cargar variables de entorno
cd /home/ubuntu/anb-cloud
source k6_config.sh

# Prueba de sanidad
k6 run K6/1sanidad.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH

# Prueba de escalamiento
k6 run K6/2escalamiento.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH

# Prueba sostenida
k6 run K6/3sostenidaCorta.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH

# Prueba GET requests
k6 run K6/escenario1_get_public_videos.js \
  -e BASE_URL=$BASE_URL

# Prueba Worker throughput
k6 run K6/escenario2_worker_throughput.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH
```

## Recolectar Datos

### Métricas de k6
- Los resultados se muestran en la consola al finalizar cada prueba
- Métricas clave: RPS, latencia (p95, p99), tasa de errores

### Métricas de AWS CloudWatch
- **ASG**: Número de instancias, CPU promedio
- **ALB**: Requests por segundo, latencia, códigos de estado HTTP
- **RDS**: CPU, conexiones, I/O
- **EC2**: CPU, memoria, red

### Métricas de Prometheus/Grafana
- Métricas de aplicación (requests, latencia, errores)
- Métricas de infraestructura (CPU, memoria, red)
- Métricas de RabbitMQ (colas, mensajes)

### Dashboards
- **Grafana**: `http://<ALB_DNS>/grafana/` (admin/admin)
- **Prometheus**: `http://<ALB_DNS>/prometheus/`
- **CloudWatch**: AWS Console → CloudWatch

## Troubleshooting

### Problemas Comunes

1. **Error: "ACCESS_TOKEN environment variable is required"**
   - Verificar que el token esté configurado en `k6_config.sh`
   - Verificar que el token no haya expirado
   - Obtener un nuevo token con `curl` (ver sección "Obtener Token de Acceso")

2. **Error: "Cannot open file"**
   - Verificar que el archivo de video existe en la ruta especificada
   - Verificar permisos del archivo
   - Verificar que la ruta sea absoluta

3. **Error: "Connection timed out"**
   - Verificar que el ALB esté accesible desde la instancia k6
   - Verificar Security Groups (debe permitir tráfico saliente)
   - Verificar que el ALB DNS sea correcto

4. **Error: "401 Unauthorized"**
   - Verificar que el token sea válido
   - Verificar que el token no haya expirado
   - Obtener un nuevo token

5. **Error: "500 Internal Server Error"**
   - Verificar logs de la aplicación
   - Verificar que los servicios estén corriendo
   - Verificar que la base de datos esté accesible

### Verificar Conectividad

```bash
# Desde la instancia k6
ALB_DNS="anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com"

# Probar health check
curl -v http://$ALB_DNS/api/health

# Probar endpoint público
curl -v http://$ALB_DNS/api/public/videos

# Probar endpoint de upload (requiere token)
curl -v -X POST "http://$ALB_DNS/api/videos/upload" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "video_file=@/home/ubuntu/videos-test/video10mb.mp4" \
  -F "title=Test"
```

## Referencias

- [Documentación de k6](https://k6.io/docs/)
- [Guía de Pruebas de Carga](../capacity-planning/pruebas_de_carga_entrega3.md)
- [Troubleshooting SSH](../infra/TROUBLESHOOTING_SSH_K6.md)

