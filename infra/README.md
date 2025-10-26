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

## Prerequisitos

- Instalar el AWS Command Line Interface (AWS CLI). Para esto puede eguir [estas instrucciones](https://docs.aws.amazon.com/es_es/cli/latest/userguide/getting-started-install.html).
- Intalar Terraform. Para esto puede seguir esta [estas instrucciones](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).

## 1) Requisitos (AWS Academy)
- Credenciales temporales (AWS_ACCESS_KEY_ID / SECRET / SESSION_TOKEN). Para esto se debe iniciar el Laboratorio de aprendizaje de AWS Academy. En la pestaña de AWS Details, encuentra estos valores.
- Ejecutar desde tu PC (CloudShell suele estar bloqueado).
- Usar AWS `us-east-1a` y tipos `t3.micro` (o `t2.micro` si aplica).

## 2) Preparación local

Abrir la terminal y ejecuta los siquientes comandos:

Para bash:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_REGION="us-east-1"
```
Si usa powershell:
```powershell
$env:AWS_ACCESS_KEY_ID="..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
$env:AWS_REGION="us-east-1"
```

## 3) Llave SSH

Es posible crear una nueva llave para poder conectarse con las máquinas EC2 que se van a crear, sin embargo ya por defecto hay una creada que puede desacargar desde el laboratorio de aws. Desde el mismo lugar que bajó las credenciales temporales, en la misma pestaña ```AWS details```, abajo hay un botón con el nombre de ```Download PEM```, una vez descargado el archivo por favor muevalo a su home de SSH, en mi caso con máquina windows es ```C:\Users\david\.ssh```

Sino desea usar la llave vockey, puede crear una nueva

```Bash
ssh-keygen -t ed25519 -f ~/.ssh/anb_lab -N ""
```

## 3) Terraform (en carpeta infra/)

Vaya a la carpeta del proyecto e ingrese a ```/infra```, ahí ya puede ejecutar estos comandos desde consola, recuerde ejecutar solo uno de ellos, dependiendo que llave este usando.

Si usa la llave vockey ejecute este comando:

```bash
terraform init
terraform fmt -recursive
terraform validate
MYIP="$(curl -s https://checkip.amazonaws.com)/32"
terraform apply -auto-approve   -var "key_name=vockey" -var "admin_cidr=${MYIP}" -var "az_name=us-east-1a" -var "instance_type_web=t3.micro" -var "instance_type_core=t3.micro" -var "instance_type_db=t3.micro" -var "instance_type_mq=t3.micro" -var "instance_type_worker=t3.micro" -var "instance_type_obs=t3.micro"
terraform output -json > outputs.json
```

Si creó una nueva llave use este comando:

```bash
terraform init
terraform fmt -recursive
terraform validate
MYIP="$(curl -s https://checkip.amazonaws.com)/32"
terraform apply -auto-approve   -var "ssh_public_key=$(cat ~/.ssh/anb_lab.pub)"   -var "admin_cidr=${MYIP}"   -var "az_name=us-east-1a"   -var "instance_type_web=t3.micro"   -var "instance_type_core=t3.micro"   -var "instance_type_db=t3.micro"   -var "instance_type_mq=t3.micro"   -var "instance_type_worker=t3.micro"   -var "instance_type_obs=t3.micro"
terraform output -json > outputs.json
```

Nota: Si tiene algún problema con la variable MYIP, simplemente visite ese sitio de amazon y reemplace con su ip en el parametro de esta manera, repita el comando.

```
"admin_cidr=XXX.XXX.XXX.XXX/32"
```

## 4) Validación rápida

El siguiente comando es una verificación rápida de que las EC2 se crearon y están “running”. El comando lista, vía AWS CLI, todas las instancias con el tag Project=ANB y muestra su Name y su IP pública. Esas IPs las usará en el punto 5 para las variables de los .env.

```bash
aws ec2 describe-instances --filters "Name=tag:Project,Values=ANB" "Name=instance-state-name,Values=running" --query 'Reservations[].Instances[].{Name:Tags[?Key==`Name`]|[0].Value,PublicIP:PublicIpAddress}' --output table
```

Debe recibir una respuesta como esta:

```
---------------------------------
|       DescribeInstances       |
+-------------+-----------------+
|    Name     |    PublicIP     |
+-------------+-----------------+
|  anb-web    |  3.82.143.253   |
|  anb-mq     |  44.203.70.88   |
|  anb-obs    |  107.20.113.2   |
|  anb-db     |  52.70.158.187  |
|  anb-core   |  98.94.72.184   |
|  anb-worker |  18.204.18.6    |
+-------------+-----------------+
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
