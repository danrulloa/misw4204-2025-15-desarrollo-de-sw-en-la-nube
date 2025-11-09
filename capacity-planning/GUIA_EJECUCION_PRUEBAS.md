# Guía Completa de Ejecución de Pruebas de Carga - Entrega 3

Esta guía te llevará paso a paso a través de todo el proceso para ejecutar las pruebas de carga del sistema ANB Rising Stars Showcase desplegado en AWS. Sigue cada paso cuidadosamente y verifica que cada etapa se complete exitosamente antes de continuar.

---

## 📋 Prerrequisitos

Antes de comenzar, asegúrate de tener:

1. ✅ **Sistema desplegado en AWS** usando Terraform
2. ✅ **Todas las instancias healthy** y funcionando correctamente
3. ✅ **Terraform outputs** disponibles (especialmente `alb_dns_name`)
4. ✅ **Acceso a AWS Console** para verificar recursos
5. ✅ **Clave SSH** (`vockey.pem`) en `~/.ssh/` (Windows: `C:\Users\<usuario>\.ssh\vockey.pem`)
6. ✅ **Postman instalado** (recomendado para obtener el token de acceso)

---

## 🚀 FASE 1: Crear y Configurar Instancia EC2 para k6

### Paso 1.1: Obtener el ALB DNS Name

**📍 Dónde ejecutar**: PowerShell en tu máquina local (terminal donde tienes Terraform)

**¿Por qué?** Necesitamos conocer la URL del Application Load Balancer para que k6 sepa a dónde enviar las peticiones.

```powershell
# Navegar a la carpeta de infraestructura
cd infra

# Obtener el DNS del ALB
terraform output -raw alb_dns_name
```

**📝 Anota el resultado**. Debería verse algo como: `anb-public-alb-2066808484.us-east-1.elb.amazonaws.com`

---

### Paso 1.2: Verificar Security Group para k6

**📍 Dónde ejecutar**: Navegador web (AWS Console)

1. Ve a **AWS Console → EC2 → Security Groups**
2. Busca el security group para k6:
   - Busca por nombre que contenga "k6" (ej: `anb-k6-sg`)
   - O busca por tag `Project=ANB` y nombre que contenga "k6"
3. **Verifica las reglas del Security Group**:
   - Haz clic en el security group para ver sus detalles
   - **Inbound rules**: 
     - Debe tener SSH (puerto 22) desde tu IP pública `/32`
     - Para obtener tu IP pública, ejecuta en PowerShell:
       ```powershell
       curl -s https://checkip.amazonaws.com
       ```
     - Si no está tu IP, agrégala:
       - Click en "Edit inbound rules"
       - Click en "Add rule"
       - Type: SSH
       - Port: 22
       - Source: `TU_IP/32` (ej: `186.81.58.137/32`)
       - Description: "SSH from admin"
       - Click en "Save rules"
   - **Outbound rules**: 
     - Debe permitir All traffic hacia `0.0.0.0/0`
     - Si no está, agrégalo (aunque generalmente está por defecto)
4. **Verifica VPC**: 
   - El security group debe estar en la misma VPC que las otras instancias
   - Para verificar: Ve a EC2 → Instances, selecciona una instancia existente (ej: Core API), y ve el VPC ID en la pestaña "Security"
5. **📝 Anota el Security Group ID**: Copia el ID (formato: `sg-0123456789abcdef0`)

---

### Paso 1.3: Verificar Key Pair

**📍 Dónde ejecutar**: Navegador web (AWS Console)

1. Ve a **AWS Console → EC2 → Key Pairs**
2. Verifica si ya existe `vockey`:
   - **Si existe**: Perfecto, solo necesitas tener el archivo `.pem` en `C:\Users\<usuario>\.ssh\vockey.pem`
   - **Si NO existe**: 
     - Click en "Create key pair"
     - Name: `vockey`
     - Key pair type: RSA
     - Private key file format: `.pem` (para Linux/Mac/Windows)
     - Click en "Create key pair"
     - El archivo se descarga automáticamente
     - Mueve el archivo a `C:\Users\<usuario>\.ssh\vockey.pem`

---

### Paso 1.4: Crear Instancia EC2 para k6

**📍 Dónde ejecutar**: Navegador web (AWS Console)

1. Ve a **AWS Console → EC2 → Instances**
2. Click en **"Launch instance"** (botón naranja)
3. Configura la instancia:
   - **Name and tags**: 
     - Name: `anb-k6-load-test`
   - **Application and OS Images (AMI)**: 
     - Click en "Browse more AMIs"
     - En el buscador, escribe "Ubuntu Server 22.04 LTS"
     - Selecciona "Ubuntu Server 22.04 LTS (HVM), SSD Volume Type"
     - Verifica que dice "Free tier eligible" (opcional, pero recomendado)
   - **Instance type**: 
     - Selecciona `t3.small` (2 vCPU, 2 GiB RAM)
     - **Justificación**: Suficiente para ejecutar k6 con múltiples VUs simultáneos
   - **Key pair (login)**: 
     - Selecciona `vockey` del dropdown
   - **Network settings**: 
     - Click en "Edit" (botón azul)
     - **VPC**: Selecciona la misma VPC donde están las otras instancias
     - **Subnet**: Selecciona cualquier subnet pública
     - **Auto-assign Public IP**: **Habilitar (Enable)** ⚠️ **MUY IMPORTANTE**
     - **Firewall (security groups)**: 
       - Selecciona "Select existing security group"
       - Selecciona el security group de k6 que verificaste en el Paso 1.2
   - **Configure storage**: 
     - Volume type: gp3
     - Size (GiB): 20
     - Delete on termination: Habilitar (checkbox)
4. Click en **"Launch instance"** (botón naranja grande)
5. **Espera la creación**:
   - Click en "View all instances" (o ve a EC2 → Instances)
   - Espera a que el estado cambie de "Pending" a "Running"
   - Esto puede tomar 1-2 minutos
6. **📝 Anota la información importante**:
   - **Instance ID**: Copia (formato: `i-0123456789abcdef0`)
   - **Public IPv4 address**: Copia (formato: `98.81.192.56`) ⚠️ **MUY IMPORTANTE**
   - **Private IPv4 address**: Copia (formato: `172.31.19.133`)
   - **Availability Zone**: Anota (ej: `us-east-1a`)

---

### Paso 1.5: Conectar vía SSH a la Instancia k6

**📍 Dónde ejecutar**: PowerShell en tu máquina local

**⚠️ IMPORTANTE**: Usa solo la IP pública, SIN `/32` y SIN corchetes `<>`. El `/32` es solo para configurar Security Groups (notación CIDR), NO para SSH.

```powershell
# Verificar que tienes el archivo de clave
Test-Path $env:USERPROFILE\.ssh\vockey.pem
# Debería devolver: True

# Conectar vía SSH (reemplaza <PUBLIC_IP> con la IP pública que anotaste)
ssh -i $env:USERPROFILE\.ssh\vockey.pem ubuntu@<PUBLIC_IP>
```

**Ejemplo real**:
```powershell
ssh -i $env:USERPROFILE\.ssh\vockey.pem ubuntu@98.81.192.56
```

**Si es la primera vez conectando**:
- Te preguntará: "Are you sure you want to continue connecting (yes/no/[fingerprint])?"
- Escribe: `yes`
- Presiona Enter

**Si la conexión es exitosa**, deberías ver:
```
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.8.0-1040-aws x86_64)
...
ubuntu@ip-172-31-19-133:~$
```

**✅ Verifica que estás conectado correctamente**:
```bash
whoami
# Debería mostrar: ubuntu

hostname
# Debería mostrar: ip-xxx-xxx-xxx-xxx
```

**🔧 Si hay problemas de conexión**: Consulta `infra/TROUBLESHOOTING_SSH_K6.md` para diagnóstico detallado.

---

### Paso 1.6: Instalar k6 en la Instancia

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6 (terminal remoto)

Ahora que estás conectado a la instancia, vamos a instalar k6. Este proceso puede tomar unos minutos.

```bash
# Paso 1: Actualizar el sistema
sudo apt-get update
sudo apt-get upgrade -y
# Esto puede tomar 2-3 minutos
# Si pregunta algo, presiona Enter para continuar

# Paso 2: Instalar dependencias necesarias
sudo apt-get install -y ca-certificates gnupg curl

# Paso 3: Crear directorio para GPG (si no existe)
sudo mkdir -p /root/.gnupg
sudo chmod 700 /root/.gnupg

# Paso 4: Agregar clave GPG de k6
sudo gpg --no-default-keyring \
  --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 \
  --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69

# Debería mostrar: "gpg: key ... imported"

# Paso 5: Agregar repositorio de k6
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list

# Paso 6: Actualizar lista de paquetes
sudo apt-get update

# Paso 7: Instalar k6
sudo apt-get install -y k6

# Paso 8: Verificar instalación
k6 version
```

**✅ Deberías ver algo como**: `k6 v1.3.0 (commit/5870e99ae8, go1.25.1, linux/amd64)`

Si ves la versión, ¡la instalación fue exitosa! 🎉

---

### Paso 1.7: Instalar Git y Clonar Repositorio

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Ahora vamos a clonar el repositorio para obtener los scripts de k6.

```bash
# Paso 1: Instalar Git (si no está instalado)
sudo apt-get install -y git

# Paso 2: Verificar instalación
git --version
# Debería mostrar: git version 2.34.1 (o similar)

# Paso 3: Clonar repositorio
cd /home/ubuntu
git clone https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube.git anb-cloud
cd anb-cloud

# Paso 4: Cambiar a la rama correcta
git checkout develop

# Paso 5: Verificar que los scripts K6 están presentes
ls -la K6/
```

**✅ Deberías ver archivos como**: 
- `0unaPeticion.js`
- `1sanidad.js`
- `2escalamiento.js`
- `3sostenidaCorta.js`

---

### Paso 1.8: Preparar Videos de Prueba

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Los scripts de k6 necesitan archivos de video para hacer las pruebas de carga. Vamos a generar videos de prueba usando FFmpeg.

```bash
# Paso 1: Instalar FFmpeg
sudo apt-get install -y ffmpeg

# Paso 2: Crear directorio para videos
mkdir -p /home/ubuntu/videos-test
cd /home/ubuntu/videos-test

# Paso 3: Generar video de ~10MB (30 segundos, 720p)
ffmpeg -f lavfi -i testsrc=duration=30:size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:duration=30 \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k \
  -t 30 video10mb.mp4

# Esto puede tomar unos segundos...

# Paso 4: Generar video de ~50MB (2 minutos, 720p, mayor calidad)
ffmpeg -f lavfi -i testsrc=duration=120:size=1280x720:rate=30 \
  -f lavfi -i sine=frequency=1000:duration=120 \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 128k \
  -t 120 video50mb.mp4

# Esto puede tomar más tiempo (1-2 minutos)...

# Paso 5: Verificar que los videos se crearon
ls -lh /home/ubuntu/videos-test/
```

**✅ Deberías ver**:
- `video10mb.mp4` (aprox. 583 KB - realmente es pequeño pero funcional)
- `video50mb.mp4` (aprox. 2.9 MB - realmente es pequeño pero funcional)

**📝 Nota**: Los nombres son aproximados. Los videos reales serán más pequeños pero son perfectos para las pruebas.

---

### Paso 1.9: Verificar Conectividad al ALB

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Antes de continuar, vamos a verificar que la instancia k6 puede comunicarse con el ALB.

```bash
# Reemplaza <ALB_DNS> con el valor que obtuviste en el Paso 1.1
ALB_DNS="anb-public-alb-2066808484.us-east-1.elb.amazonaws.com"

# Probar conectividad HTTP al health check
curl -v http://$ALB_DNS/api/health
```

**✅ Deberías ver una respuesta como**:
```json
{"status": "healthy"}
```

Si ves esto, ¡perfecto! La conectividad está funcionando.

**🔧 Si hay problemas**:
- Verifica que el Security Group de k6 permita tráfico saliente (outbound)
- Verifica que el ALB esté accesible desde la subnet donde está la instancia k6
- Verifica que el ALB tenga el Security Group correcto que permita tráfico desde la VPC

---

## 🔐 FASE 2: Obtener Token de Acceso (Usando Postman)

### Paso 2.1: Crear Usuario y Obtener Token con Postman

**📍 Dónde ejecutar**: Postman en tu máquina local

**💡 Recomendación**: Usar Postman es mucho más fácil y confiable que usar PowerShell para obtener el token.

#### Opción A: Crear Usuario Nuevo (Signup)

1. **Abre Postman**
2. **Crea una nueva request POST**:
   - URL: `http://<ALB_DNS>/auth/api/v1/signup`
   - Reemplaza `<ALB_DNS>` con el valor que obtuviste en el Paso 1.1
   - Ejemplo: `http://anb-public-alb-2066808484.us-east-1.elb.amazonaws.com/auth/api/v1/signup`
   - Method: **POST**
   - Headers: 
     - Key: `Content-Type`
     - Value: `application/json`
   - Body: 
     - Selecciona "raw"
     - Selecciona "JSON" en el dropdown
     - Pega el siguiente JSON:
       ```json
       {
         "first_name": "Test",
         "last_name": "Load",
         "email": "test_load@example.com",
         "password1": "Test123!",
         "password2": "Test123!",
         "city": "Bogotá"
       }
       ```
3. **Click en "Send"**
4. **✅ Deberías ver una respuesta como**:
   ```json
   {
     "email": "test_load@example.com",
     "message": "Usuario creado exitosamente",
     "user_id": 1
   }
   ```

**📝 Nota**: Si el usuario ya existe, verás un error. En ese caso, continúa con el login directamente.

#### Opción B: Hacer Login (Obtener Token)

1. **Crea una nueva request POST**:
   - URL: `http://<ALB_DNS>/auth/api/v1/login`
   - Ejemplo: `http://anb-public-alb-2066808484.us-east-1.elb.amazonaws.com/auth/api/v1/login`
   - Method: **POST**
   - Headers: 
     - Key: `Content-Type`
     - Value: `application/x-www-form-urlencoded`
   - Body: 
     - Selecciona "x-www-form-urlencoded"
     - Agrega los siguientes key-value pairs:
       - Key: `username`, Value: `test_load@example.com`
       - Key: `password`, Value: `Test123!`
2. **Click en "Send"**
3. **✅ Deberías ver una respuesta como**:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "expires_in_access": "2025-11-09T11:29:09.374153+00:00",
     "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "expires_in_refresh": "2025-11-09T11:29:09.374300+00:00",
     "token_type": "Bearer"
   }
   ```
4. **📝 Copia el valor de `access_token`**. Lo necesitarás en el siguiente paso.

---

### Paso 2.2: Configurar Variables de Entorno en la Instancia k6

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Ahora vamos a crear un archivo de configuración con todas las variables que necesitamos para ejecutar las pruebas.

```bash
# Navegar al directorio del proyecto
cd /home/ubuntu/anb-cloud

# Crear archivo de configuración
nano k6_config.sh
```

**Pega el siguiente contenido** (reemplaza los valores con los tuyos):

```bash
#!/bin/bash
# Configuración para pruebas k6

# ALB DNS (obtener de: terraform output -raw alb_dns_name)
export BASE_URL="http://anb-public-alb-2066808484.us-east-1.elb.amazonaws.com"

# Token de acceso (obtener de Postman después de hacer login)
export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Rutas a videos de prueba
export FILE_PATH_10MB="/home/ubuntu/videos-test/video10mb.mp4"
export FILE_PATH_50MB="/home/ubuntu/videos-test/video50mb.mp4"

# Título para videos
export TITLE="Video de prueba de carga"

# Path de upload
export UPLOAD_PATH="/api/videos/upload"
export PUBLIC_VIDEOS_PATH="/api/public/videos"
```

**⚠️ IMPORTANTE**: 
- Reemplaza `BASE_URL` con tu ALB DNS real
- Reemplaza `ACCESS_TOKEN` con el token que copiaste de Postman

**Para guardar en nano**:
- Presiona `Ctrl + O` para guardar
- Presiona `Enter` para confirmar
- Presiona `Ctrl + X` para salir

**Hacer el archivo ejecutable y cargar las variables**:

```bash
# Hacer el archivo ejecutable
chmod +x k6_config.sh

# Cargar variables de entorno
source k6_config.sh

# Verificar que las variables estén configuradas
echo $BASE_URL
echo $ACCESS_TOKEN
echo $FILE_PATH_50MB
```

**✅ Deberías ver los valores que configuraste**. Si alguno está vacío, verifica que hayas guardado el archivo correctamente.

---

## 🧪 FASE 3: Ejecutar Pruebas de Carga

### Paso 3.1: Prueba de Sanidad (Smoke Test)

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Esta es la primera prueba. Su objetivo es validar que el sistema funciona correctamente con una carga mínima antes de ejecutar pruebas más intensas.

```bash
# Navegar al directorio del proyecto
cd /home/ubuntu/anb-cloud

# Cargar variables de entorno
source k6_config.sh

# Verificar que el token esté configurado
echo $ACCESS_TOKEN
# Debería mostrar el token (no vacío)

# Ejecutar prueba de sanidad
k6 run K6/1sanidad.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH
```

**⏱️ Duración**: Aproximadamente 1 minuto

**📊 Qué esperar**:
- **VUs máximo**: 5
- **Requests totales**: ~1000 requests
- **Throughput**: ~16-17 RPS
- **Latencia p95**: Debería ser menor a 5000ms (generalmente ~250ms)
- **Tasa de errores**: 0% (100% éxito)

**✅ Si ves que todos los thresholds pasan y la tasa de errores es 0%**, ¡perfecto! Puedes continuar con la siguiente prueba.

---

### Paso 3.2: Prueba de Escalamiento (Ramp-up)

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Esta prueba aumenta gradualmente la carga para activar el escalado automático del ASG y medir cómo responde el sistema.

**Primero, vamos a crear una versión de 20 minutos del script de escalamiento**:

```bash
# Navegar al directorio de scripts K6
cd /home/ubuntu/anb-cloud/K6

# Copiar el script de escalamiento
cp 2escalamiento.js 2escalamiento_20min.js

# Editar el script
nano 2escalamiento_20min.js
```

**Modifica la sección `export const options`** para que tenga una duración total de 20 minutos:

```javascript
export const options = {
    stages: [
        // Ramp-up progresivo para activar escalado automático del ASG
        { duration: '3m', target: 10 },   // 0 → 10 VUs en 3 minutos
        { duration: '4m', target: 30 },   // 10 → 30 VUs en 4 minutos
        { duration: '4m', target: 50 },   // 30 → 50 VUs en 4 minutos
        { duration: '8m', target: 50 },   // Mantener 50 VUs por 8 minutos
        { duration: '1m', target: 0 },    // Ramp-down a 0 VUs en 1 minuto
    ],
    discardResponseBodies: true,
    summaryTrendStats: ['min', 'avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
    thresholds: {
        http_req_duration: ['p(95)<10000'],  // p95 debe ser menor a 10 segundos (considerando upload)
        http_req_sending: ['p(95)<5000'],    // p95 sending < 5s
        http_req_waiting: ['p(95)<8000'],    // p95 waiting < 8s
        http_req_failed: ['rate<0.05'],      // Tasa de errores < 5%
    },
}
```

**Para guardar en nano**:
- Presiona `Ctrl + O` para guardar
- Presiona `Enter` para confirmar
- Presiona `Ctrl + X` para salir

**Ejecutar la prueba**:

```bash
# Volver al directorio del proyecto
cd /home/ubuntu/anb-cloud

# Cargar variables de entorno
source k6_config.sh

# Ejecutar prueba de escalamiento
k6 run K6/2escalamiento_20min.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH
```

**⏱️ Duración**: Aproximadamente 20 minutos

**📊 Qué esperar**:
- **VUs máximo**: 50
- **Requests totales**: ~50,000+ requests
- **Throughput**: ~40-45 RPS
- **Latencia p95**: Puede aumentar a ~3-4 segundos bajo carga alta (aún dentro del threshold de 10s)
- **Tasa de errores**: < 1% (generalmente 0%)

**🔍 Monitoreo durante la prueba**:

Mientras la prueba está corriendo, puedes verificar en AWS Console:

1. **Auto Scaling Group**:
   - Ve a EC2 → Auto Scaling Groups
   - Busca el ASG del Core API
   - Verifica que el número de instancias aumente (1 → 2 → 3)
   - Revisa las métricas de CPU

2. **CloudWatch**:
   - Ve a CloudWatch → Metrics
   - Busca métricas del ASG (CPU, número de instancias)
   - Busca métricas del ALB (requests, latencia)

3. **Grafana** (opcional):
   - Abre: `http://<ALB_DNS>/grafana/`
   - Usuario: `admin`
   - Contraseña: `admin`
   - Revisa los dashboards en tiempo real

**✅ Si la prueba termina exitosamente y todos los thresholds pasan**, puedes continuar con la siguiente prueba.

---

### Paso 3.3: Prueba de Carga Sostenida

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Esta prueba mantiene una carga constante durante un período prolongado para evaluar la estabilidad del sistema.

```bash
# Navegar al directorio del proyecto
cd /home/ubuntu/anb-cloud

# Cargar variables de entorno
source k6_config.sh

# Ejecutar prueba de carga sostenida
k6 run K6/3sostenidaCorta.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH
```

**⏱️ Duración**: Aproximadamente 11 minutos

**📊 Qué esperar**:
- **VUs máximo**: 50 (si el script está configurado correctamente)
- **Requests totales**: ~13,000+ requests
- **Throughput**: ~40-45 RPS
- **Latencia p95**: Debería mantenerse estable (~200-400ms)
- **Tasa de errores**: 0% (100% éxito)

**✅ Si la prueba termina exitosamente**, has completado las pruebas principales del Escenario 1.

---

## 📊 FASE 4: Recolectar y Analizar Resultados

### Paso 4.1: Guardar Resultados de las Pruebas

**📍 Dónde ejecutar**: Sesión SSH conectada a la instancia k6

Para poder analizar los resultados más tarde, puedes guardar la salida de k6 en archivos.

```bash
# Crear directorio para resultados
mkdir -p /home/ubuntu/anb-cloud/resultados-pruebas

# Ejecutar prueba y guardar resultados (ejemplo con prueba de sanidad)
cd /home/ubuntu/anb-cloud
source k6_config.sh

k6 run K6/1sanidad.js \
  -e BASE_URL=$BASE_URL \
  -e ACCESS_TOKEN=$ACCESS_TOKEN \
  -e FILE_PATH=$FILE_PATH_50MB \
  -e UPLOAD_PATH=$UPLOAD_PATH \
  2>&1 | tee resultados-pruebas/sanidad_$(date +%Y%m%d_%H%M%S).txt
```

**📝 Repite esto para cada prueba**, cambiando el nombre del archivo de salida.

---

### Paso 4.2: Revisar Métricas en AWS CloudWatch

**📍 Dónde ejecutar**: Navegador web (AWS Console)

1. **Ve a CloudWatch → Metrics**:
   - Busca métricas del Auto Scaling Group (CPU, número de instancias)
   - Busca métricas del ALB (requests por segundo, latencia, códigos HTTP)
   - Busca métricas de RDS (CPU, conexiones, I/O)
   - Busca métricas de EC2 Worker (CPU, memoria, red)

2. **Exporta las métricas**:
   - Selecciona el período de tiempo de las pruebas
   - Exporta a CSV si es necesario

---

### Paso 4.3: Revisar Dashboards en Grafana

**📍 Dónde ejecutar**: Navegador web

1. **Abre Grafana**:
   - URL: `http://<ALB_DNS>/grafana/`
   - Usuario: `admin`
   - Contraseña: `admin`

2. **Revisa los dashboards**:
   - Métricas de aplicación (requests, latencia, errores)
   - Métricas de infraestructura (CPU, memoria, red)
   - Métricas de RabbitMQ (colas, mensajes)

3. **Exporta gráficos**:
   - Toma capturas de pantalla de los gráficos importantes
   - O exporta los datos si es necesario

---

## 🎯 Resumen de Pruebas Ejecutadas

### Prueba 1: Sanidad
- **Duración**: ~1 minuto
- **VUs**: 5
- **Resultado esperado**: 100% éxito, latencia p95 < 5000ms

### Prueba 2: Escalamiento
- **Duración**: ~20 minutos
- **VUs**: 0 → 10 → 30 → 50
- **Resultado esperado**: ASG escala, latencia p95 < 10000ms, tasa de errores < 5%

### Prueba 3: Carga Sostenida
- **Duración**: ~11 minutos
- **VUs**: 50 (constante)
- **Resultado esperado**: 100% éxito, latencia estable, sistema estable

---

## 🔧 Troubleshooting

### Problema: "ACCESS_TOKEN environment variable is required"
**Solución**: 
- Verifica que hayas cargado las variables de entorno: `source k6_config.sh`
- Verifica que el token no haya expirado (obtén uno nuevo con Postman)

### Problema: "Cannot open file"
**Solución**: 
- Verifica que el archivo de video exista: `ls -lh /home/ubuntu/videos-test/`
- Verifica que la ruta en `k6_config.sh` sea correcta

### Problema: "Connection timed out"
**Solución**: 
- Verifica que el ALB esté accesible: `curl http://<ALB_DNS>/api/health`
- Verifica Security Groups (debe permitir tráfico saliente desde k6)

### Problema: "401 Unauthorized"
**Solución**: 
- Verifica que el token sea válido (obtén uno nuevo con Postman)
- Verifica que el token no haya expirado

### Problema: El script no alcanza los VUs esperados
**Solución**: 
- Verifica que el script tenga la configuración correcta: `cat K6/2escalamiento_20min.js | grep -A 10 "stages"`
- Verifica que estés ejecutando el script correcto (no una versión antigua)

---

## 📝 Notas Finales

- **Tiempo total estimado**: ~35-40 minutos para todas las pruebas
- **Costo**: Las instancias t3.small son de bajo costo, pero recuerda detener/terminar la instancia k6 cuando termines
- **Limpieza**: Cuando termines, puedes terminar la instancia k6 desde AWS Console para evitar costos innecesarios

---

## ✅ Checklist Final

- [ ] Instancia k6 creada y conectada vía SSH
- [ ] k6 instalado y funcionando
- [ ] Repositorio clonado y scripts K6 presentes
- [ ] Videos de prueba generados
- [ ] Token de acceso obtenido con Postman
- [ ] Variables de entorno configuradas
- [ ] Prueba de sanidad ejecutada exitosamente
- [ ] Prueba de escalamiento ejecutada exitosamente
- [ ] Prueba de carga sostenida ejecutada exitosamente
- [ ] Resultados guardados y analizados
- [ ] Métricas de AWS CloudWatch revisadas
- [ ] Instancia k6 terminada (para ahorrar costos)

---

**¡Felicidades! Has completado las pruebas de carga del Escenario 1. 🎉**

Si necesitas ayuda con el Escenario 2 (Worker Performance), consulta la documentación correspondiente en la Wiki del proyecto.
