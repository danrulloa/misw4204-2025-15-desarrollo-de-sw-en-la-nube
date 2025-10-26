#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./post-deploy.sh <SSH_KEY_PATH> <REPO_URL>
# Example:
#   ./post-deploy.sh ~/.ssh/anb_lab https://github.com/your-org/anb-cloud.git
#
# Requisitos: awscli v2, jq, ssh/scp, docker compose plugin ya instalado por user-data en las VMs.
#
# Notas:
# - Usuario SSH por defecto: 'ubuntu' (Ubuntu 22.04 de Canonical).
# - Abre temporalmente 22/tcp en tus SG si tu lab lo permite, o usa el keypair del lab (p. ej., vockey).
# - Si no tienes SSH en el lab, usa el Plan B (cloud-init) de la guía.

SSH_KEY="${1:-}"
REPO_URL="${2:-}"
if [[ -z "${SSH_KEY}" || -z "${REPO_URL}" ]]; then
  echo "Uso: $0 <SSH_KEY_PATH> <REPO_URL>"
  exit 1
fi

SSH_OPTS=(-i "${SSH_KEY}" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10)

# 1) Carga IPs desde outputs.json o terraform output -json
if [[ -f outputs.json ]]; then
  echo "[i] Leyendo IPs desde outputs.json"
  PUB_WEB=$(jq -r '.public_ips.value.web' outputs.json)
  PUB_CORE=$(jq -r '.public_ips.value.core' outputs.json)
  PUB_DB=$(jq -r '.public_ips.value.db' outputs.json)
  PUB_MQ=$(jq -r '.public_ips.value.mq' outputs.json)
  PUB_WORKER=$(jq -r '.public_ips.value.worker' outputs.json)
  PUB_OBS=$(jq -r '.public_ips.value.obs' outputs.json)

  PRIV_WEB=$(jq -r '.private_ips.value.web' outputs.json)
  PRIV_CORE=$(jq -r '.private_ips.value.core' outputs.json)
  PRIV_DB=$(jq -r '.private_ips.value.db' outputs.json)
  PRIV_MQ=$(jq -r '.private_ips.value.mq' outputs.json)
  PRIV_WORKER=$(jq -r '.private_ips.value.worker' outputs.json)
  PRIV_OBS=$(jq -r '.private_ips.value.obs' outputs.json)
else
  echo "[i] outputs.json no existe, intento con 'terraform output -json'"
  TO=$(terraform output -json)
  PUB_WEB=$(jq -r '.public_ips.value.web' <<<"$TO")
  PUB_CORE=$(jq -r '.public_ips.value.core' <<<"$TO")
  PUB_DB=$(jq -r '.public_ips.value.db' <<<"$TO")
  PUB_MQ=$(jq -r '.public_ips.value.mq' <<<"$TO")
  PUB_WORKER=$(jq -r '.public_ips.value.worker' <<<"$TO")
  PUB_OBS=$(jq -r '.public_ips.value.obs' <<<"$TO")

  PRIV_WEB=$(jq -r '.private_ips.value.web' <<<"$TO")
  PRIV_CORE=$(jq -r '.private_ips.value.core' <<<"$TO")
  PRIV_DB=$(jq -r '.private_ips.value.db' <<<"$TO")
  PRIV_MQ=$(jq -r '.private_ips.value.mq' <<<"$TO")
  PRIV_WORKER=$(jq -r '.private_ips.value.worker' <<<"$TO")
  PRIV_OBS=$(jq -r '.private_ips.value.obs' <<<"$TO")
fi

echo "[i] IPs públicas:"
printf "  WEB=%s CORE=%s DB=%s MQ=%s WORKER=%s OBS=%s\n" "$PUB_WEB" "$PUB_CORE" "$PUB_DB" "$PUB_MQ" "$PUB_WORKER" "$PUB_OBS"
echo "[i] IPs privadas:"
printf "  WEB=%s CORE=%s DB=%s MQ=%s WORKER=%s OBS=%s\n" "$PRIV_WEB" "$PRIV_CORE" "$PRIV_DB" "$PRIV_MQ" "$PRIV_WORKER" "$PRIV_OBS"

# 2) Espera a que las instancias estén 'instance-status-ok'
echo "[i] Esperando a que las instancias pasen checks de salud de EC2..."
IDS=$(aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=ANB" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].InstanceId' --output text)

if [[ -n "${IDS}" ]]; then
  aws ec2 wait instance-status-ok --instance-ids ${IDS}
else
  echo "[!] No se encontraron instancias con tag Project=ANB en estado running"
  exit 1
fi
echo "[i] EC2 status OK."

# 3) Función remota básica
remote() {
  local host="$1"; shift
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" "$@"
}

remote_bash() {
  local host="$1"; shift
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" 'bash -s' <<'EOS'
set -euo pipefail
which git >/dev/null 2>&1 || sudo apt-get update -y
which git >/dev/null 2>&1 || sudo apt-get install -y git
sudo systemctl enable --now docker || true
sudo usermod -aG docker ubuntu || true
mkdir -p /opt/anb-cloud
EOS
}

# 4) Sincroniza repo a cada host (clona si no existe; si existe, hace pull)
sync_repo() {
  local host="$1"
  remote_bash "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt && { [[ -d anb-cloud/.git ]] || git clone '${REPO_URL}' anb-cloud; } && cd anb-cloud && git pull --ff-only || true"
}

# 5) Despliegue por rol

deploy_web() {
  local host="$1"
  local obs_ip="$2"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    cat > .env <<EOF
APP_ENV=production
LOKI_URL=http://${obs_ip}:3100/loki/api/v1/push
EOF
    docker compose -f docker-compose.multihost.yml --profile web --profile obs-agent --profile obs-agent-web up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

deploy_core() {
  local host="$1"
  local db_ip="$2"
  local mq_ip="$3"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    cat > .env <<EOF
APP_ENV=production
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass
RABBITMQ_HOST=${mq_ip}
POSTGRES_USER=anb_user
POSTGRES_PASSWORD=anb_pass
POSTGRES_CORE_DB=anb_core
POSTGRES_DB=anb_auth
POSTGRES_CORE_HOST=${db_ip}
POSTGRES_AUTH_HOST=${db_ip}
EOF
    docker compose -f docker-compose.multihost.yml --profile core --profile obs-agent up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

deploy_db() {
  local host="$1"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    cat > .env <<EOF
POSTGRES_USER=anb_user
POSTGRES_PASSWORD=anb_pass
POSTGRES_CORE_DB=anb_core
POSTGRES_DB=anb_auth
TZ=America/Bogota
EOF
    docker compose -f docker-compose.multihost.yml --profile db --profile obs-agent --profile obs-agent-db up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

deploy_mq() {
  local host="$1"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    cat > .env <<EOF
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass
EOF
    docker compose -f docker-compose.multihost.yml --profile mq --profile obs-agent up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

deploy_worker() {
  local host="$1"
  local db_ip="$2"
  local mq_ip="$3"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    cat > .env <<EOF
APP_ENV=production
RABBITMQ_DEFAULT_USER=rabbit
RABBITMQ_DEFAULT_PASS=rabbitpass
RABBITMQ_HOST=${mq_ip}
POSTGRES_USER=anb_user
POSTGRES_PASSWORD=anb_pass
POSTGRES_CORE_DB=anb_core
POSTGRES_CORE_HOST=${db_ip}
EOF
    docker compose -f docker-compose.multihost.yml --profile worker --profile obs-agent up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

deploy_obs() {
  local host="$1"
  local web_ip="$2" core_ip="$3" db_ip="$4" mq_ip="$5" worker_ip="$6"
  sync_repo "$host"
  ssh "${SSH_OPTS[@]}" "ubuntu@${host}" bash -lc "cd /opt/anb-cloud && \
    mkdir -p observability/prometheus && \
    cat > observability/prometheus/prometheus.yml <<EOF
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: nginx
    static_configs: [ { targets: [\"${web_ip}:9113\"] } ]
  - job_name: cadvisor
    static_configs: [ { targets: [\"${web_ip}:8080\",\"${core_ip}:8080\",\"${db_ip}:8080\",\"${mq_ip}:8080\",\"${worker_ip}:8080\"] } ]
  - job_name: postgres
    static_configs: [ { targets: [\"${db_ip}:9187\",\"${db_ip}:9188\"] } ]
EOF
    docker compose -f docker-compose.multihost.yml --profile obs up -d && \
    docker ps --format 'table {{.Names}}\t{{.Status}}'"
}

echo "[i] Desplegando WEB...";    deploy_web    "$PUB_WEB"    "$PRIV_OBS"
echo "[i] Desplegando CORE...";   deploy_core   "$PUB_CORE"   "$PRIV_DB" "$PRIV_MQ"
echo "[i] Desplegando DB...";     deploy_db     "$PUB_DB"
echo "[i] Desplegando MQ...";     deploy_mq     "$PUB_MQ"
echo "[i] Desplegando WORKER..."; deploy_worker "$PUB_WORKER" "$PRIV_DB" "$PRIV_MQ"
echo "[i] Desplegando OBS...";    deploy_obs    "$PUB_OBS"    "$PRIV_WEB" "$PRIV_CORE" "$PRIV_DB" "$PRIV_MQ" "$PRIV_WORKER"

echo ""
echo "=== SMOKE TESTS (desde tu máquina) ==="
echo "Nginx:      http://${PUB_WEB}/"
echo "RabbitMQ:   http://${PUB_MQ}:15672/   (rabbit / rabbitpass)"
echo "Grafana:    http://${PUB_OBS}:3000/   (admin / admin si no cambiaste)"
echo "Prometheus: http://${PUB_OBS}:9090/"
echo ""
echo "[OK] Despliegue remoto finalizado."
