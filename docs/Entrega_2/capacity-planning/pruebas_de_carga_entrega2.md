# Pruebas de Carga - Entrega 2

## Objetivo

Evaluar el comportamiento de la aplicación desplegada en AWS bajo diferentes escenarios de carga para identificar cuellos de botella y definir recomendaciones de escalamiento.

---

## Configuración de Pruebas

**Herramienta**: k6

**Infraestructura**: AWS EC2 t3.micro (2 vCPU, 2 GB RAM, 50 GB storage)

**Componentes**: Web Server, Core Services, Worker, Database (PostgreSQL en containers), RabbitMQ

---

## Escenario 1: Prueba de Sanidad

**Descripción**: Validación básica del sistema con carga mínima.

**Configuración**:
- Usuarios virtuales: 5
- Duración: 1 minuto
- Objetivo p95: < 1 segundo

**Resultados**:

![Prueba de Sanidad](https://private-user-images.githubusercontent.com/196724598/505794058-96e5d6eb-c7b9-46d7-8f66-51fb2f348cdb.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjE1Mzc3MzcsIm5iZiI6MTc2MTUzNzQzNywicGF0aCI6Ii8xOTY3MjQ1OTgvNTA1Nzk0MDU4LTk2ZTVkNmViLWM3YjktNDZkNy04ZjY2LTUxZmIyZjM0OGNkYi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDI3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAyN1QwMzU3MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0xZDI0ZmIzZmNlNDgyMGE4ZDgwNzljYjY0NWU0NWNlYTk3NGU3NTBmNjU3N2I0N2YwYzljMTE5ZGE5YzA3MjYzJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.CFczYqLCKhcFsG9iivdKSkmq8SNNQJqiTq65c32_9Q0)

| Métrica | Resultado |
|---------|-----------|
| Peticiones totales | 100% exitosas (0 errores) |
| Tiempo de respuesta p95 | 2.14 s |
| Estado del sistema | Estable |

**Análisis**:
- El sistema maneja correctamente baja carga sin errores
- Sin embargo, el p95 de 2.14s está muy por encima del objetivo de 1s
- Esto indica que hay latencia incluso con carga mínima, probablemente por la comunicación entre instancias o el procesamiento interno

---

## Escenario 2: Prueba de Escalamiento

**Descripción**: Evaluación del comportamiento del sistema con carga progresiva.

**Configuración**:
- Usuarios virtuales: 6
- Duración: 8 minutos
- Patrón: Carga incremental
- Objetivo p95: < 1 segundo

**Resultados**:

![Prueba de Escalamiento](https://private-user-images.githubusercontent.com/196724598/505794069-2fa2a71d-902c-4fe2-be16-800ed464b73d.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjE1Mzc3MzcsIm5iZiI6MTc2MTUzNzQzNywicGF0aCI6Ii8xOTY3MjQ1OTgvNTA1Nzk0MDY5LTJmYTJhNzFkLTkwMmMtNGZlMi1iZTE2LTgwMGVkNDY0YjczZC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDI3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAyN1QwMzU3MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0xMmVlYmQ3MDVmODdjYmRlNWRjZGQ1ZDNkOTRjMjA2MzA2NWUxNDQzZmI3ODJlYTIyNjMxZmU4ZmQ5ODI3NGY4JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.H7mrzYxwJtwQSnNHD-_2R5VNSvJEUOGLlmHHlEiSOsA)

| Métrica | Resultado |
|---------|-----------|
| Peticiones totales | 902 |
| Peticiones exitosas | 902 (100%) |
| Tiempo de respuesta p95 | 6.2 s |
| Errores | 0 |

**Análisis**:
- La aplicación mantiene estabilidad y cero errores bajo carga creciente
- El rendimiento se degrada severamente: p95 de 6.2s (6x peor que el objetivo)
- Este problema no se resolvió aumentando recursos (t3.large no mejoró significativamente el p95)
- Indica cuellos de botella en procesamiento interno o en el proxy/API, no en recursos de cómputo

---

## Escenario 3: Prueba Sostenida Corta

**Descripción**: Evaluación de estabilidad del sistema bajo carga constante.

**Configuración**:
- Usuarios virtuales: 5
- Duración: 5 minutos
- Patrón: Carga constante
- Objetivo p95: < 1 segundo

**Resultados**:

![Prueba Sostenida Corta](https://private-user-images.githubusercontent.com/196724598/505794078-48cedf15-004f-4296-9da3-8247f5ed7880.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjE1Mzc3MzcsIm5iZiI6MTc2MTUzNzQzNywicGF0aCI6Ii8xOTY3MjQ1OTgvNTA1Nzk0MDc4LTQ4Y2VkZjE1LTAwNGYtNDI5Ni05ZGEzLTgyNDdmNWVkNzg4MC5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMDI3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTAyN1QwMzU3MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1lMDhhODRlYzViNTA4NTliMzFlNDQxNjM1NjdlZTBiN2FmZmRmNWM5MTc5ZWJmOGYyZGMxN2ZlNGI0MWZmMmRkJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.cpniMHnk5k8RnADeI_6a9hAfApJgJhStA5ZkjbHflVo)

| Métrica | Resultado |
|---------|-----------|
| Peticiones totales | 477 |
| Peticiones exitosas | 477 (100%) |
| Tiempo de respuesta p95 | 3.01 s |
| Errores | 0 |

**Análisis**:
- El sistema se mantiene estable en el tiempo sin degradarse
- No hay fugas de memoria ni problemas de estabilidad
- El p95 de 3.01s se mantiene constante, lo que confirma que no es problema de recursos sino de optimización de código o configuración del proxy

---

## Análisis de Cuellos de Botella

### 1. Latencia en el Procesamiento
**Problema**: Todos los escenarios muestran tiempos de respuesta muy superiores al objetivo, incluso con baja carga.

**Causa probable**:
- Configuración no optimizada del proxy Nginx
- Procesamiento ineficiente en las APIs
- Falta de optimización en queries a la base de datos

### 2. Comunicación entre Instancias
**Problema**: La arquitectura distribuida introduce latencia adicional.

**Causa probable**:
- Tráfico entre Web Server → Core Services → Database (PostgreSQL en containers)
- Comunicación entre instancias EC2 separadas
- No se están usando conexiones optimizadas o pooling

### 3. Almacenamiento de Archivos
**Problema**: Acceso a archivos compartidos entre Web y Worker.

**Causa probable**:
- Volúmenes Docker para archivos sin optimización
- Lectura/escritura síncrona de archivos grandes
- Falta de servidor NFS dedicado

### 4. Configuración de Instancias
**Observación**: Aumentar de t3.micro a t3.large no resolvió el problema de latencia.
**Conclusión**: El problema no es de recursos de CPU/RAM, sino de optimización de software.

---

## Conclusiones

1. **Estabilidad**: La aplicación es estable y no presenta errores bajo carga. El 100% de peticiones son exitosas en todos los escenarios.

2. **Rendimiento deficiente**: Los tiempos de respuesta están entre 3x y 6x por encima del objetivo en todos los escenarios.

3. **No es problema de recursos**: Aumentar el tamaño de instancia no resolvió la latencia, indicando que el cuello de botella está en el código o configuración.

4. **Arquitectura distribuida**: La separación en múltiples instancias introduce overhead de red que debe optimizarse.

---

## Recomendaciones para Escalar

### Corto Plazo (inmediato)

1. **Optimizar configuración de Nginx**: Revisar timeouts, buffers, y configuración de proxy
2. **Implementar connection pooling**: En las conexiones a PostgreSQL y entre servicios
3. **Optimizar queries**: Revisar y optimizar consultas a base de datos
4. **Migrar a Amazon RDS**: Usar base de datos gestionada en lugar de containers
5. **Implementar NFS Server**: Servidor de archivos compartido dedicado

### Mediano Plazo

1. **Implementar caché distribuido**: Redis para datos frecuentes (rankings, videos públicos)
2. **CDN para archivos estáticos**: CloudFront para servir videos procesados
3. **Load Balancer**: Application Load Balancer para distribuir tráfico entre múltiples instancias del Web Server
4. **Auto Scaling**: Implementar escalado automático basado en métricas de CPU y latencia

### Largo Plazo

1. **Migrar a S3 o EFS**: Usar servicios gestionados de AWS para almacenamiento de archivos
2. **Separar lectura de escritura en DB**: Read replicas en RDS para queries de solo lectura
3. **Implementar API Gateway**: Para rate limiting, throttling y caché
4. **Microservicios optimizados**: Separar componentes críticos y optimizar cada uno independientemente
5. **Monitoring avanzado**: Implementar APM (Application Performance Monitoring) para identificar cuellos de botella en tiempo real

---

## Próximos Pasos

1. Ejecutar profiling de la aplicación para identificar funciones lentas
2. Revisar logs de Nginx y FastAPI para identificar requests lentos
3. Analizar métricas de Prometheus/Grafana durante las pruebas
4. Implementar las optimizaciones de corto plazo y re-ejecutar pruebas
