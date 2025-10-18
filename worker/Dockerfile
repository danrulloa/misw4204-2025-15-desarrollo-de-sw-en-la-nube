FROM python:3.12-slim

WORKDIR /app

# Install ffmpeg and required OS packages
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   ffmpeg \
	   ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]
