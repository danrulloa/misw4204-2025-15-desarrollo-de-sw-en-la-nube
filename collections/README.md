# Colección Postman - ANB Basketball API

Colección completa de Postman para probar todos los endpoints de la API ANB Rising Stars Showcase.

**Para documentación detallada sobre testing, ejecución de pruebas y uso avanzado de Newman, consulta la [Wiki - Testing](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Testing).**

---

## Archivos

- `ANB_Basketball_API.postman_collection.json` - Colección con 14 endpoints y tests automatizados
- `ANB_Basketball_API.postman_environment.json` - Environment con variables configuradas para local

---

## Inicio Rápido

### Postman Desktop/Web

1. Abre Postman
2. Click en **Import**
3. Selecciona ambos archivos:
   - `ANB_Basketball_API.postman_collection.json`
   - `ANB_Basketball_API.postman_environment.json`
4. Selecciona el environment "ANB Basketball API - Local Environment" en el dropdown superior derecho
5. Ejecuta los requests en orden

### Newman CLI

Instalar Newman:
```bash
npm install -g newman
```

Ejecutar toda la colección:
```bash
newman run ANB_Basketball_API.postman_collection.json \
  -e ANB_Basketball_API.postman_environment.json
```

---

## Variables de Entorno

El archivo de environment incluye:

| Variable | Valor Default | Descripción |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8080` | URL base de la API |
| `user_email` | Auto-generado | Email con timestamp para evitar conflictos |
| `access_token` | Auto-generado | Token JWT (se guarda automáticamente al login) |
| `refresh_token` | Auto-generado | Token de refresco (se guarda automáticamente) |
| `video_id` | Auto-generado | ID del último video subido |

---

## Configuración del Archivo de Video

El endpoint `POST /api/videos/upload` requiere un archivo .mp4 válido.

**Opción 1: Editar la colección JSON**

1. Editar `ANB_Basketball_API.postman_collection.json`
2. Buscar el request "Subir Video"
3. Actualizar el campo `video_file.src` con la ruta absoluta a un archivo .mp4

```json
{
  "key": "video_file",
  "type": "file",
  "src": "/ruta/absoluta/a/tu/video.mp4"
}
```

**Opción 2: Configurar en Postman UI**

1. En Postman, abre el request "Subir Video"
2. En la pestaña **Body**, selecciona el archivo en el campo `video_file`

---

## Endpoints Incluidos

### Autenticación (3 endpoints)
- `POST /auth/api/v1/signup` - Registro de usuarios
- `POST /auth/api/v1/login` - Inicio de sesión
- `POST /auth/api/v1/refresh` - Refrescar token

### Gestión de Videos (4 endpoints)
- `POST /api/videos/upload` - Subir video
- `GET /api/videos` - Listar mis videos
- `GET /api/videos/{id}` - Consultar video específico
- `DELETE /api/videos/{id}` - Eliminar video

### Endpoints Públicos (3 endpoints)
- `GET /api/public/videos` - Listar videos públicos
- `POST /api/public/videos/{id}/vote` - Votar por un video
- `GET /api/public/rankings` - Ver rankings

### Health Checks (2 endpoints)
- `GET /api/health` - Health check API Core
- `GET /auth/api/v1/health` - Health check Auth Service

---

## Tests Automatizados

Cada request incluye tests que validan:
- Códigos de estado HTTP correctos
- Estructura de las respuestas
- Guardado automático de tokens y IDs en variables de entorno

Para ejecutar los tests y ver reportes detallados:
```bash
newman run ANB_Basketball_API.postman_collection.json \
  -e ANB_Basketball_API.postman_environment.json \
  --reporters cli,htmlextra
```


Consulta la **[Wiki - Testing](https://github.com/danrulloa/misw4204-2025-15-desarrollo-de-sw-en-la-nube/wiki/Testing)**
