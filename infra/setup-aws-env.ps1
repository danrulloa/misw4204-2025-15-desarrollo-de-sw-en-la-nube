# Script para configurar credenciales AWS en PowerShell
# Uso: .\setup-aws-env.ps1
#
# ⚠️ IMPORTANTE: Este script solicita credenciales de manera interactiva
# para evitar exponer secretos en el código.

Write-Host "🔐 Configuración de credenciales AWS" -ForegroundColor Cyan
Write-Host ""

# Verificar si ya están configuradas como variables de entorno
if ($env:AWS_ACCESS_KEY_ID -and $env:AWS_SECRET_ACCESS_KEY -and $env:AWS_SESSION_TOKEN) {
    Write-Host "⚠️  Ya existen credenciales en variables de entorno" -ForegroundColor Yellow
    $sobreescribir = Read-Host "¿Deseas sobreescribirlas? (S/N)"
    if ($sobreescribir -ne "S" -and $sobreescribir -ne "s") {
        Write-Host "✅ Usando credenciales existentes" -ForegroundColor Green
    } else {
        $sobreescribir = $true
    }
} else {
    $sobreescribir = $true
}

if ($sobreescribir) {
    # Solicitar credenciales de manera interactiva
    Write-Host "📋 Ingresa las credenciales desde AWS Academy Lab (AWS Details):" -ForegroundColor Yellow
    Write-Host "   Obtén las credenciales desde: AWS Academy Lab → AWS Details" -ForegroundColor Gray
    Write-Host ""
    
    $accessKey = Read-Host "AWS Access Key ID"
    $secretKey = Read-Host "AWS Secret Access Key"
    $sessionToken = Read-Host "AWS Session Token"
    
    $env:AWS_ACCESS_KEY_ID = $accessKey
    $env:AWS_SECRET_ACCESS_KEY = $secretKey
    $env:AWS_SESSION_TOKEN = $sessionToken
    
    Write-Host ""
    Write-Host "⚠️  Nota: Las credenciales temporales expiran después de un tiempo." -ForegroundColor Yellow
    Write-Host "   Si fallan, obtén nuevas credenciales desde AWS Academy Lab" -ForegroundColor Yellow
    Write-Host ""
}

$env:AWS_REGION = "us-east-1"
$env:AWS_DEFAULT_REGION = "us-east-1"

Write-Host "✅ Credenciales AWS configuradas" -ForegroundColor Green
Write-Host "   Account ID esperado: 758955011573" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verificando identidad..." -ForegroundColor Yellow

# Verificar que las credenciales funcionan
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credenciales válidas" -ForegroundColor Green
        Write-Host $identity
    } else {
        Write-Host "❌ Error verificando credenciales:" -ForegroundColor Red
        Write-Host $identity
        Write-Host ""
        Write-Host "⚠️  Posibles causas:" -ForegroundColor Yellow
        Write-Host "   1. Las credenciales expiraron (son temporales)" -ForegroundColor Yellow
        Write-Host "   2. AWS CLI no está instalado" -ForegroundColor Yellow
        Write-Host "   3. Error de conectividad" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "💡 Solución: Obtén nuevas credenciales desde AWS Academy Lab" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️  AWS CLI no está instalado o no está en PATH" -ForegroundColor Yellow
    Write-Host "   Las variables de entorno están configuradas, pero no se pudo verificar." -ForegroundColor Yellow
    Write-Host "   Instala AWS CLI: https://aws.amazon.com/cli/" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📝 Para usar estas credenciales en Terraform:" -ForegroundColor Cyan
Write-Host "   cd infra" -ForegroundColor White
Write-Host "   terraform init" -ForegroundColor White
Write-Host "   terraform plan -var-file=terraform.tfvars" -ForegroundColor White

