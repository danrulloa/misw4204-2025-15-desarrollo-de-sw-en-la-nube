#!/bin/bash
set -e

# Descargar archivos desde S3
echo "Descargando archivos desde S3..."
aws s3 cp s3://$S3_BUCKET/assets/inout.mp4 /app/assets/inout.mp4
aws s3 cp s3://$S3_BUCKET/assets/watermark.png /app/assets/watermark.png

echo "Iniciando el Worker..."
exec "$@"