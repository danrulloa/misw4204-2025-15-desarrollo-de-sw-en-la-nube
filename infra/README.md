# README — Despliegue ANB en AWS Academy (Lab)

## 0) Contexto y arquitectura
Este lab levanta **6 VMs** (EC2) con Ubuntu + Docker/Compose preinstalados (user-data) y despliega la plataforma en **multihost** con un `docker-compose.multihost.yml` usando **profiles** por rol.

**Topología (6 VMs):**
- WEB: Nginx (reverse proxy) + nginx-exporter + cAdvisor + promtail
- CORE: anb_api + anb-auth-service + cAdvisor + promtail
- DB: Postgres (core/auth) + exporters + cAdvisor + promtail
- MQ: RabbitMQ (broker/UI) + cAdvisor + promtail
- WORKER: Celery worker + cAdvisor + promtail
- OBS: Prometheus + Grafana + Loki

## 1) Requisitos (AWS Academy)
- Credenciales temporales (AWS_ACCESS_KEY_ID / SECRET / SESSION_TOKEN).
- Ejecutar desde tu PC (CloudShell suele estar bloqueado).
- Usar AWS `us-east-1a` y tipos `t3.micro` (o `t2.micro` si aplica).

## 2) Preparación local
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_REGION="us-east-1"
aws configure set aws_access_key_id     "$AWS_ACCESS_KEY_ID" --profile lab                                
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile lab
aws configure set aws_session_token     "$AWS_SESSION_TOKEN" --profile lab
aws configure set region                us-east-1            --profile lab
export AWS_PROFILE=lab
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
ssh-keygen -t ed25519 -f ~/.ssh/anb_lab -N ""
```

aws ec2 describe-security-groups \                              
  --filters Name=vpc-id,Values=$VPC_ID Name=group-name,Values='anb-*-sg' \
  --query 'SecurityGroups[].{ID:GroupId,Name:GroupName}' --output table
  
terraform state rm aws_security_group.web    2>/dev/null || true
terraform state rm aws_security_group.core   2>/dev/null || true     
terraform state rm aws_security_group.db     2>/dev/null || true
terraform state rm aws_security_group.worker 2>/dev/null || true
terraform state rm aws_security_group.mq     2>/dev/null || true
terraform state rm aws_security_group.obs    2>/dev/null || true  

terraform import aws_security_group.web    sg-01cb0a8bdb9b6ef2b 
terraform import aws_security_group.core   sg-02514540403ee6516 
terraform import aws_security_group.db     sg-01af27cfa756c56af 
terraform import aws_security_group.worker sg-05621f0b6ce6c29d8 
terraform import aws_security_group.mq     sg-05ca1bcc54417ef1d 
terraform import aws_security_group.obs    sg-02ed299e0f587147e 

## 3) Terraform (en carpeta infra/)
```bash
terraform init
terraform fmt -recursive
terraform validate
MYIP="$(curl -s https://checkip.amazonaws.com | tr -d '\r\n')" 
terraform plan -var "admin_cidr=${MYIP}/32"  
terraform apply -auto-approve -var "admin_cidr=${MYIP}/32"
terraform output -json > outputs.json
```

## 4) Validación rápida
```bash
aws ec2 describe-instances   --filters "Name=tag:Project,Values=ANB" "Name=instance-state-name,Values=running"   --query 'Reservations[].Instances[].{Name:Tags[?Key==`Name`]|[0].Value,PublicIP:PublicIpAddress}' --output table
```

## 5) Despliegue contenedores (multihost)
Copia `deploy-package/` a **cada VM** (p.ej. `/opt/anb-cloud`). En cada VM crea su `.env` con IPs:
- WEB: `LOKI_URL=http://<OBS_IP>:3100/loki/api/v1/push`
- CORE: `DB_URL_CORE=postgresql://anb_user:anb_pass@<DB_IP>:5432/anb_core`, `DB_URL_AUTH=postgresql://anb_user:anb_pass@<DB_IP>:5433/anb_auth`, `RABBITMQ_HOST=<MQ_IP>`
- DB/MQ/WORKER/OBS según plantilla del README del repo.

**Arranque por perfiles:**
```bash
# WEB
docker compose -f docker-compose.multihost.yml --profile web --profile obs-agent --profile obs-agent-web up -d
# CORE
docker compose -f docker-compose.multihost.yml --profile core --profile obs-agent up -d
# DB
docker compose -f docker-compose.multihost.yml --profile db --profile obs-agent --profile obs-agent-db up -d
# MQ
docker compose -f docker-compose.multihost.yml --profile mq --profile obs-agent up -d
# WORKER
docker compose -f docker-compose.multihost.yml --profile worker --profile obs-agent up -d
# OBS
docker compose -f docker-compose.multihost.yml --profile obs up -d
```

## 6) Observabilidad
- **Promtail** usa `${LOKI_URL}`; ya está habilitado `-config.expand-env=true` en el compose.
- **Prometheus**: edita `observability/prometheus/prometheus.yml` con targets por IP:
```yaml
global: { scrape_interval: 15s }
scrape_configs:
  - job_name: nginx
    static_configs: [ { targets: ["${WEB_IP}:9113"] } ]
  - job_name: cadvisor
    static_configs: [ { targets: ["${WEB_IP}:8080","${CORE_IP}:8080","${DB_IP}:8080","${MQ_IP}:8080","${WORKER_IP}:8080"] } ]
  - job_name: postgres
    static_configs: [ { targets: ["${DB_IP}:9187","${DB_IP}:9188"] } ]
```

## 7) Limpieza
```bash
terraform destroy -auto-approve
```

## 8) Notas
- Mantén `admin_cidr` con tu IP/32 (no expongas UIs).
- Si el rol del lab no permite `ec2:RunInstances`, consulta al instructor.
