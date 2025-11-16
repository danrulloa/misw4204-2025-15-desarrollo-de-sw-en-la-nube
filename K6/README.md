# Scripts de Pruebas de Carga con k6

Este directorio contiene los scripts de k6 para realizar pruebas de carga del sistema ANB Rising Stars Showcase.

## Scripts Disponibles

- **`0unaPeticion.js`**: Prueba simple de una sola petición (validación rápida)
- **`1sanidad.js`**: Prueba de sanidad - 5 VUs durante 1 minuto
- **`2escalamiento.js`**: Prueba de escalamiento - 0→50 VUs durante 8 minutos
- **`3sostenidaCorta.js`**: Prueba sostenida - 5 VUs durante 5 minutos

Todos los scripts suben videos usando `POST /api/videos/upload` y requieren autenticación.

---

## Opción 1: Ejecutar desde Instancia K6 en AWS Lab (Recomendado)

**Ventaja**: Menor latencia de red, resultados más precisos.

### Pasos Rápidos

1. **Crear instancia K6 en AWS** - Ver sección 11 en [`infra/README.md`](../infra/README.md)

2. **Obtener token de autenticación**:
   - Usar Postman para registrar usuario y hacer login
   - Copiar el `access_token` de la respuesta

3. **Obtener DNS del ALB**:
   ```bash
   cd infra
   terraform output -raw alb_dns_name
   ```

4. **Configurar y ejecutar en la instancia K6**:
   ```bash
   # SSH a la instancia
   ssh -i ~/.ssh/vockey.pem ubuntu@<IP_K6>
   
   # Ir al directorio de scripts
   cd ~/k6  # o cd ~/anb-cloud/K6 si clonaste el repo
   
   # Editar scripts para actualizar:
   nano 1sanidad.js
   # - BASE_URL (línea 10): DNS del ALB
   # - FILE_PATH (línea 12): nombre del archivo (ej: '50MB.mp4')
   # - TITLE (línea 13): título del video
   # - ACCESS_TOKEN (línea 15): token obtenido de Postman
   
   # Ejecutar prueba
   k6 run 1sanidad.js
   ```

**Para más detalles**: Consulta la sección completa **11) Configurar Instancia K6 para Pruebas de Carga** en [`infra/README.md`](../infra/README.md)

---

## Opción 2: Ejecutar desde Local

**Advertencia**: La latencia de red desde tu ubicación al ALB afectará los resultados. Útil para pruebas rápidas, pero no recomendado para pruebas de carga precisas.

### Prerrequisitos

1. **Instalar k6 localmente**:
   ```bash
   # Windows (usando Chocolatey)
   choco install k6
   
   # macOS
   brew install k6
   
   # Linux
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   ```

2. **Obtener token de autenticación** (mismo proceso que Opción 1):
   - Usar Postman con el ALB DNS
   - Registrar usuario y hacer login
   - Copiar el `access_token`

3. **Actualizar scripts**:
   ```bash
   # Editar scripts en K6/
   nano K6/1sanidad.js
   # - BASE_URL (línea 10): DNS del ALB
   # - FILE_PATH (línea 12): ruta local al archivo (ej: 'K6/50MB.mp4')
   # - TITLE (línea 13): título del video
   # - ACCESS_TOKEN (línea 15): token obtenido de Postman
   ```

4. **Ejecutar prueba**:
   ```bash
   cd K6
   k6 run 1sanidad.js
   ```

**Nota sobre latencia**: Las pruebas desde local incluirán el tiempo de red entre tu ubicación y AWS, lo que puede aumentar las latencias medidas. Para métricas precisas, usa Opción 1.

---

## Variables a Configurar en los Scripts

Todos los scripts usan estas variables (con valores por defecto que debes actualizar):

```javascript
// Línea 10: URL del ALB
const BASE_URL = __ENV.BASE_URL || 'http://anb-public-alb-xxxxx.us-east-1.elb.amazonaws.com'

// Línea 12: Ruta al archivo de video
const FILE_PATH = __ENV.FILE_PATH || '50MB.mp4'  // o 'K6/50MB.mp4' si es ruta local

// Línea 13: Título del video
const TITLE = __ENV.TITLE || 'prueba50mb'

// Línea 15: Token JWT de autenticación (obtener de Postman)
const ACCESS_TOKEN = __ENV.ACCESS_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

**Actualizar en**: `1sanidad.js`, `2escalamiento.js`, `3sostenidaCorta.js`, `0unaPeticion.js`

---

## Orden Recomendado de Pruebas

1. **`0unaPeticion.js`** - Validar que todo funciona (opcional)
2. **`1sanidad.js`** - Prueba básica (1 minuto)
3. **`3sostenidaCorta.js`** - Prueba de estabilidad (5 minutos)
4. **`2escalamiento.js`** - Prueba de escalamiento (8 minutos)

---

## Obtener Token con Postman

1. Importar colección `ANB_Basketball_API.postman_collection.json` en Postman
2. Actualizar `base_url` en el environment con el DNS del ALB
3. Ejecutar `POST /auth/api/v1/signup` para registrar usuario (si no existe)
4. Ejecutar `POST /auth/api/v1/login` con credenciales
5. Copiar el `access_token` de la respuesta
6. Pegar el token en los scripts de K6 (línea 15)

---

## Métricas que Verás

Al finalizar cada prueba, k6 muestra:
- **RPS**: Requests por segundo
- **Latencia**: p50, p90, p95, p99
- **Tasa de errores**: Porcentaje de requests fallidos
- **Success rate**: Tasa de éxito

---

## Troubleshooting

**Error: "ACCESS_TOKEN environment variable is required"**
- Actualizar el token en el script (línea 15) o usar variable de entorno

**Error: "Cannot open file"**
- Verificar que el archivo existe en la ruta especificada
- En instancia K6: usar ruta relativa como `'50MB.mp4'`
- En local: usar ruta relativa desde el script como `'K6/50MB.mp4'`

**Error: "Connection timed out"**
- Verificar que el ALB DNS sea correcto
- Verificar conectividad de red (desde local puede haber firewalls/VPN)

**Error: "401 Unauthorized"**
- Token expirado o inválido - obtener nuevo token de Postman
- Verificar que el token esté completo (no cortado)

---

## Referencias

- [Guía completa de despliegue K6 en AWS](../infra/README.md#11-configurar-instancia-k6-para-pruebas-de-carga)
- [Documentación de k6](https://k6.io/docs/)
- [Pruebas de carga - Entrega 4](../capacity-planning/pruebas_de_carga_entrega4.md)
