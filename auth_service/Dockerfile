
# Etapa base
FROM python:3.13-slim AS base

# Establece el directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos de requisitos e instala dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el código fuente de la aplicación
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/ app/
COPY README.md ./
COPY tests/ tests/

RUN useradd -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Puerto expuesto (ajusta si es diferente en tu app)    
EXPOSE 8001

# Comando por defecto para ejecutar la app con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
