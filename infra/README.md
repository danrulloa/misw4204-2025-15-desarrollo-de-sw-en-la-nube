# README — Despliegue ANB en AWS Academy (Lab)

## 0) Contexto y arquitectura

Este lab levanta **6 VMs** (EC2) con Ubuntu. La instalación puede ser:

- **Automática** (recomendada): vía `user-data` (cloud-init) se instala Docker/Compose, se clona el repo y se levanta el stack multihost.
- **Manual**: copias el paquete y ejecutas `docker compose` por perfiles.

El despliegue multihost usa `deploy/compose/docker-compose.multihost.yml` con **profiles** por rol.

**Topología (6 VMs / roles):**
- **WEB**: Nginx (reverse proxy) + nginx-exporter + cAdvisor + promtail  
- **CORE**: anb_api + anb-auth-service + cAdvisor + promtail  
- **DB**: PostgreSQL (core/auth) + exporters + cAdvisor + promtail  
- **MQ**: RabbitMQ (broker/UI) + cAdvisor + promtail  
- **WORKER**: Celery worker + cAdvisor + promtail  
- **OBS**: Prometheus + Grafana + Loki

---

## 1) Prerrequisitos

- **AWS CLI** instalado. Guía oficial: <https://docs.aws.amazon.com/es_es/cli/latest/userguide/getting-started-install.html>
- **Terraform** instalado. Guía: <https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli>
- **Tu PC local** (en AWS Academy, CloudShell suele estar restringido).
- Región recomendada: **us-east-1** (AZ: `us-east-1a`).
- Tipos sugeridos: `t3.micro` (o `t2.micro` si aplica en el lab).

---

## 2) Preparación local (variables de entorno)

En **bash** (Linux/macOS):

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_REGION="us-east-1"
```

En **PowerShell** (Windows):

```powershell
$env:AWS_ACCESS_KEY_ID="..."
$env:AWS_SECRET_ACCESS_KEY="..."
$env:AWS_SESSION_TOKEN="..."
$env:AWS_REGION="us-east-1"
```

> **Tip**: crea un perfil `lab` (opcional pero recomendado):

```bash
aws configure set aws_access_key_id     "$AWS_ACCESS_KEY_ID" --profile lab
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile lab
aws configure set aws_session_token     "$AWS_SESSION_TOKEN" --profile lab
aws configure set region                us-east-1            --profile lab
export AWS_PROFILE=lab
```

---

## 3) Llave SSH

**Opción A (recomendada en AWS Academy):** usar la llave **vockey**.  
Desde la pestaña **AWS Details** del lab, descarga **Download PEM** y guárdalo en tu carpeta SSH (p. ej., en Windows: `C:\Users\<tu-usuario>\.ssh`).

**Opción B:** crear una **nueva** llave:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/anb_lab -N ""
```

> Asegúrate de tener el perfil `lab` activo si lo usas:
```bash
export AWS_PROFILE=lab
```

### (Opcional) Importar Security Groups existentes

Si el instructor ya creó SGs y quieres **importarlos** al estado de Terraform:

```bash
export VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)

aws ec2 describe-security-groups   --filters Name=vpc-id,Values=$VPC_ID Name=group-name,Values='anb-*-sg'   --query 'SecurityGroups[].{ID:GroupId,Name:GroupName}' --output table

# Limpia del estado los SG gestionados previamente (si aplica)
terraform state rm aws_security_group.web    2>/dev/null || true
terraform state rm aws_security_group.core   2>/dev/null || true
terraform state rm aws_security_group.db     2>/dev/null || true
terraform state rm aws_security_group.worker 2>/dev/null || true
terraform state rm aws_security_group.mq     2>/dev/null || true
terraform state rm aws_security_group.obs    2>/dev/null || true

# Importa tus SG (IDs de ejemplo; reemplaza por los tuyos)
terraform import aws_security_group.web    sg-01cb0a8bdb9b6ef2b
terraform import aws_security_group.core   sg-02514540403ee6516
terraform import aws_security_group.db     sg-01af27cfa756c56af
terraform import aws_security_group.worker sg-05621f0b6ce6c29d8
terraform import aws_security_group.mq     sg-05ca1bcc54417ef1d
terraform import aws_security_group.obs    sg-02ed299e0f587147e
```

> **Si no necesitas SGs preexistentes**, deja que Terraform los cree y **omite** esta sección.

---

## 4) Terraform (carpeta `infra/`)

Entra a la carpeta `infra/` del proyecto y ejecuta:

### Ejecutamos

```bash
terraform init
terraform fmt -recursive
terraform validate

MYIP="$(curl -s https://checkip.amazonaws.com | tr -d '
')"
terraform plan -var "admin_cidr=${MYIP}/32"
terraform apply -auto-approve -var "admin_cidr=${MYIP}/32"

terraform output -json > outputs.json
```

> Si `MYIP` te falla, abre https://checkip.amazonaws.com en el navegador y usa manualmente:
>
> ```
> -var "admin_cidr=XXX.XXX.XXX.XXX/32"
> ```

---

## 5) Validación rápida de EC2

Lista las instancias con el tag `Project=ANB` y sus IPs públicas:

```bash
aws ec2 describe-instances   --filters "Name=tag:Project,Values=ANB" "Name=instance-state-name,Values=running"   --query 'Reservations[].Instances[].{Name:Tags[?Key==`Name`]|[0].Value,PublicIP:PublicIpAddress}'   --output table
```

Ejemplo de salida:

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

---

## 6) Despliegue de contenedores (multihost)

### Modo A — **Automático** (con `user-data`)

Si usaste el `user-data` provisto, cada VM ya debe:
1) instalar Docker/Compose,  
2) clonar el repo en **`/opt/anb-cloud`**,  
3) generar `.env` con IPs y `ROLE`,  
4) levantar con:
   ```
   docker compose -f deploy/compose/docker-compose.multihost.yml up -d [perfiles/servicios]
   ```

**Verifica estado** (en cada VM):
```bash
cd /opt/anb-cloud
docker compose -f deploy/compose/docker-compose.multihost.yml ps
docker ps --format 'table {{.Names}}	{{.Status}}	{{.Ports}}'
```

### Modo B — **Manual**

1) Copia el paquete del repo a **cada VM** (p. ej., a `/opt/anb-cloud`).
2) En **cada VM**, crea un `.env` con las IPs relevantes:

- **WEB**:
  ```
  LOKI_URL=http://<OBS_IP>:3100/loki/api/v1/push
  ```

- **CORE**:
  ```
  DB_URL_CORE=postgresql://anb_user:anb_pass@<DB_IP>:5432/anb_core
  DB_URL_AUTH=postgresql://anb_user:anb_pass@<DB_IP>:5433/anb_auth
  RABBITMQ_HOST=<MQ_IP>
  ```

- **DB/MQ/WORKER/OBS**: según las variables definidas en tu repo (consulta el README del repo/compose).

3) **Arranque por perfiles** (en `/opt/anb-cloud`):

```bash
# WEB
docker compose -f deploy/compose/docker-compose.multihost.yml --profile web --profile obs-agent --profile obs-agent-web up -d
# CORE
docker compose -f deploy/compose/docker-compose.multihost.yml --profile core --profile obs-agent up -d
# DB
docker compose -f deploy/compose/docker-compose.multihost.yml --profile db --profile obs-agent --profile obs-agent-db up -d
# MQ
docker compose -f deploy/compose/docker-compose.multihost.yml --profile mq --profile obs-agent up -d
# WORKER
docker compose -f deploy/compose/docker-compose.multihost.yml --profile worker --profile obs-agent up -d
# OBS
docker compose -f deploy/compose/docker-compose.multihost.yml --profile obs up -d
```

> Si tu compose **no** usa profiles, levanta servicios concretos, p. ej.:
> ```bash
> docker compose -f deploy/compose/docker-compose.multihost.yml up -d web
> ```

---

## 7) Observabilidad
- **Promtail** usa `${LOKI_URL}` y el compose ya tiene `-config.expand-env=true`.
- **Prometheus**: ajusta `observability/prometheus/prometheus.yml` con las IPs/puertos:

```yaml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: nginx
    static_configs:
      - targets: ["${WEB_IP}:9113"]
  - job_name: cadvisor
    static_configs:
      - targets:
          - "${WEB_IP}:8080"
          - "${CORE_IP}:8080"
          - "${DB_IP}:8080"
          - "${MQ_IP}:8080"
          - "${WORKER_IP}:8080"
  - job_name: postgres
    static_configs:
      - targets:
          - "${DB_IP}:9187"    # postgres-exporter (core)
          - "${DB_IP}:9188"    # postgres-exporter (auth) - si aplica
```

> **Grafana**: por defecto suele ser `admin / admin` (a menos que lo sobrescribas en el compose).

---

## 8) Limpieza

```bash
terraform destroy -auto-approve
```

---

## 9) Notas y buenas prácticas

- Mantén `admin_cidr` con tu IP `/32` (no expongas UIs a Internet).
- Si tu rol en el lab **no** permite `ec2:RunInstances`, consulta al instructor.
- Asegura que **todas las VMs** puedan resolver/alcanzar las IPs privadas/públicas configuradas en los `.env`.
- Considera usar **rutas absolutas** para `COMPOSE_FILE` si automatizas con user-data:
  - `/opt/anb-cloud/deploy/compose/docker-compose.multihost.yml`

---

## 10) Troubleshooting

**Ruta del compose**
- Asegúrate de ejecutar desde `/opt/anb-cloud`:
  ```bash
  cd /opt/anb-cloud
  test -f deploy/compose/docker-compose.multihost.yml || echo "No existe el compose en esa ruta"
  ```
- Valida sintaxis/servicios:
  ```bash
  docker compose -f deploy/compose/docker-compose.multihost.yml config --services
  ```

**Perfiles vs servicios**
- Si el compose **no** define el profile `db` (o similar), usa servicios concretos:  
  `docker compose -f ... up -d db`  
- Lista perfiles disponibles:
  ```bash
  docker compose -f deploy/compose/docker-compose.multihost.yml config --profiles
  ```

**Contenedores/health**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml ps
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
for id in $(docker compose -f deploy/compose/docker-compose.multihost.yml ps -q); do
  echo "$(docker inspect -f '{{.Name}} -> {{.State.Status}} / {{if .State.Health}}{{.State.Health.Status}}{{end}}' $id)"
done
```

**Puertos publicados**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml port web 443 || true
docker compose -f deploy/compose/docker-compose.multihost.yml port grafana 3000 || true
```

**Logs rápidos**
```bash
docker compose -f deploy/compose/docker-compose.multihost.yml logs -n 200 web core db mq worker grafana prometheus loki
```

**Permisos Docker**
- Si tu usuario no puede usar Docker sin `sudo`, agrega al grupo:
  ```bash
  sudo usermod -aG docker $USER && newgrp docker
  ```

---

¿Necesitas que integre este README con tus **valores exactos** de `.env` (los que inyecta tu `user-data`) y con **nombres de servicio** 1:1 del `docker-compose.multihost.yml`? Pega el bloque `services:` y lo ajusto al 100%.
