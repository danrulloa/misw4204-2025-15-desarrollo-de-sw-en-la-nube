# Imagen base: Python 3.12 slim (versión ligera)
FROM python:3.12-slim

# Establecer directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar solo requirements.txt primero (para aprovechar caché de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Crear directorios de almacenamiento si no existen
RUN mkdir -p /app/storage/uploads /app/storage/processed

# Exponer el puerto 8000 (donde corre FastAPI)
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
