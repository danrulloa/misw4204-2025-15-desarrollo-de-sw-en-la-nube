# Colección Postman - ANB Basketball API

## Uso

### Postman Desktop/Web

Importar ambos archivos en Postman:
- `ANB_Basketball_API.postman_collection.json` (colección)
- `ANB_Basketball_API.postman_environment.json` (entorno)

Seleccionar el entorno "ANB Basketball API - Local Environment" y ejecutar los requests.

### Newman (CLI)

Ejecutar toda la colección:
```bash
newman run ANB_Basketball_API.postman_collection.json -e ANB_Basketball_API.postman_environment.json
```

Ejecutar con reporte detallado:
```bash
newman run ANB_Basketball_API.postman_collection.json -e ANB_Basketball_API.postman_environment.json --reporters cli,htmlextra
```

Ejecutar solo una carpeta específica:
```bash
newman run ANB_Basketball_API.postman_collection.json -e ANB_Basketball_API.postman_environment.json --folder "1. Autenticación"
```

## Configuración requerida

### Archivo de video para testing

El endpoint `POST /api/videos/upload` requiere un archivo .mp4 válido. Antes de ejecutar la colección:

1. Editar `ANB_Basketball_API.postman_collection.json`
2. Buscar el request "Subir Video"
3. En `body.formdata`, actualizar el campo `video_file.src` con la ruta absoluta a un archivo .mp4

Ejemplo:
```json
{
  "key": "video_file",
  "type": "file",
  "src": "/ruta/absoluta/a/tu/video.mp4"
}
```

### Variables de entorno

El archivo `ANB_Basketball_API.postman_environment.json` incluye:

- `base_url`: URL base de la API (default: http://localhost:8080)
- `user_email`: Email generado dinámicamente con timestamp para evitar conflictos
- Variables dinámicas: `access_token`, `refresh_token`, `video_id` (se auto-generan)

## Endpoints implementados vs stubs

### Implementados
- Autenticación (signup, login, refresh)
- Gestión de videos (upload, listar, consultar, eliminar)
- Health checks

### Stubs (retornan 501)
- `GET /api/public/videos`
- `GET /api/public/rankings`
- `POST /api/public/videos/{id}/vote`

Los tests de estos endpoints aceptan tanto 200 como 501 para permitir ejecución exitosa mientras se implementan.

