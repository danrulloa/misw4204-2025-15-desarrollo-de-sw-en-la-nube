FROM python:3.12-slim

WORKDIR /app

# Install ffmpeg and required OS packages
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   ffmpeg \
	   ca-certificates \
	   curl \
	   build-essential \
	   libcurl4-openssl-dev \
	   libssl-dev \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Agregar script de entrada
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
