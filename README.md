# Laboratorio Integrador de Observabilidad Multicloud

## Observabilidad, AIOps, Chaos Engineering y Seguridad en AWS

Este repositorio contiene la implementación de un laboratorio integrador de observabilidad orientado a microservicios, telemetría distribuida, detección inteligente de anomalías, Chaos Engineering y observabilidad de seguridad en AWS.

La solución fue construida con una arquitectura de tres servicios instrumentados con OpenTelemetry, PostgreSQL, Prometheus, un detector AIOps y componentes cloud desplegados mediante Terraform.

---

## 1. Objetivo

Diseñar e implementar una arquitectura observable que permita:

- Capturar trazas, métricas y logs.
- Propagar contexto distribuido entre microservicios.
- Observar operaciones de base de datos.
- Detectar anomalías mediante una regla AIOps.
- Ejecutar experimentos controlados de Chaos Engineering.
- Analizar tráfico North-South y East-West.
- Detectar vulnerabilidades en imágenes de contenedores.
- Detectar autenticaciones fallidas.
- Centralizar señales de seguridad en un dashboard.
- Administrar infraestructura AWS mediante Infrastructure as Code.

---

## 2. Arquitectura

La arquitectura principal del laboratorio es:

```text
Client
  |
  v
service-a :8001
  |
  v
service-b :8002
  |
  v
data-service :8003
  |
  v
PostgreSQL / AWS RDS
```

La capa de observabilidad utiliza:

```text
service-a
service-b
data-service
     |
     | OTLP
     v
OpenTelemetry Collector
     |
     +------------------+
     |                  |
     v                  v
Prometheus         Traces / Logs
     |
     v
AIOps Detector
```

La parte AWS incorpora:

```text
Internet
   |
   | North-South
   v
EC2 / service-a
   |
   | East-West
   v
Amazon RDS PostgreSQL

VPC Flow Logs
CloudWatch Logs
CloudTrail
Security Hub CSPM
Amazon ECR
Amazon Inspector
CloudWatch Dashboard
```

---

## 3. Tecnologías utilizadas

### Aplicación y observabilidad

- Python
- Flask
- PostgreSQL
- Docker
- Docker Compose
- OpenTelemetry SDK
- OpenTelemetry Collector
- Prometheus

### AIOps y resiliencia

- Detector de anomalías basado en baseline
- Prometheus Query API
- Chaos Engineering
- Inyección de latencia
- Inyección de errores
- SLO y MTTD

### AWS

- Amazon EC2
- Amazon RDS PostgreSQL
- Amazon ECR
- Amazon Inspector
- Amazon VPC
- VPC Flow Logs
- Amazon CloudWatch
- AWS CloudTrail
- AWS Config
- AWS Security Hub CSPM
- AWS Systems Manager Session Manager
- IAM

### Infrastructure as Code

- Terraform
- AWS CLI

---

## 4. Estructura del repositorio

```text
observability-multicloud-lab/
│
├── lab/
│   ├── aiops/
│   ├── otel/
│   ├── prometheus/
│   ├── scripts/
│   ├── services/
│   │   ├── service-a/
│   │   ├── service-b/
│   │   └── data-service/
│   └── docker-compose.yml
│
├── terraform/
│   └── aws/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── config.tf
│       ├── cloudtrail.tf
│       ├── security-dashboard.tf
│       └── ...
│
├── evidencias/
│
└── README.md
```

---

## 5. Módulo A - Observabilidad de la arquitectura

Se implementaron tres servicios:

- `service-a`
- `service-b`
- `data-service`

La comunicación observada es:

```text
service-a -> service-b -> data-service -> PostgreSQL
```

Todos los servicios fueron instrumentados mediante OpenTelemetry.

### Tres pilares de observabilidad

#### Traces

Propagación del mismo `trace_id` entre los servicios.

```text
service-a
  trace_id = X
      |
service-b
  trace_id = X
      |
data-service
  trace_id = X
      |
PostgreSQL span
```

#### Metrics

Se capturaron contadores e histogramas mediante OpenTelemetry y Prometheus.

Principales métricas:

- Requests totales.
- Requests con error.
- Latencia.
- P95.
- P99.

#### Logs

Los logs fueron exportados mediante OpenTelemetry e incluyen contexto de trazas:

```text
trace_id
span_id
service.name
```

---

## 6. Observabilidad de base de datos

`data-service` utiliza PostgreSQL.

Las operaciones SQL se instrumentaron mediante OpenTelemetry DB instrumentation.

Se observaron spans de base de datos con atributos como:

```text
db.system = postgresql
db.statement = INSERT ...
```

En AWS se desplegó además una instancia privada de Amazon RDS PostgreSQL.

```text
EC2
 |
 | TCP 5432
 v
Amazon RDS PostgreSQL
```

La comunicación fue validada mediante VPC Flow Logs.

---

## 7. Módulo B - AIOps

Se implementó un detector de anomalías que utiliza un baseline dinámico.

La regla implementada es:

```text
error_rate > baseline + 2σ
AND
latency_p99 > SLO_threshold
```

El umbral del SLO de latencia utilizado fue:

```text
P99 < 250 ms
```

Cuando ambas condiciones se cumplen, se genera un incidente enriquecido con el `trace_id` de una solicitud fallida.

### Resultado del incidente

```text
Incident ID:
OBS-1788301457

Error rate:
0.93 %

P99:
487.801 ms

Trace ID:
7410f0686f39afb2a438bda682d38924

MTTD técnico:
2.333 segundos
```

Clasificación:

```text
ACTIONABLE
```

### Reducción de ruido

```text
Static alerts: 12
AIOps incidents: 1
Suppressed alerts: 11
Noise reduction: 91.67 %
```

Resultado:

```text
Reducción de alertas ruidosas = 91.67 %
```

---

## 8. Módulo C - Observabilidad de Seguridad AWS

AWS fue seleccionada como nube para la implementación del componente de seguridad.

### VPC Flow Logs

Se habilitaron VPC Flow Logs para la VPC del laboratorio.

Log Group:

```text
/obs-multicloud/vpc-flow-logs
```

Se observaron eventos:

```text
ACCEPT
REJECT
```

### North-South Traffic

Se generó tráfico desde Internet hacia:

```text
service-a :8001
```

VPC Flow Logs registró tráfico `ACCEPT`.

También se generó tráfico intencional hacia el puerto:

```text
TCP 8004
```

El resultado fue:

```text
REJECT
```

### East-West Traffic

Se validó tráfico interno desde EC2 hacia Amazon RDS:

```text
EC2
 |
 | TCP 5432
 v
RDS PostgreSQL
```

Los VPC Flow Logs registraron tráfico `ACCEPT`.

---

## 9. AWS Security Hub CSPM

Se habilitó AWS Security Hub CSPM con:

```text
AWS Foundational Security Best Practices v1.0.0
```

Estado:

```text
READY
```

Security Hub quedó integrado con:

```text
AWSConfigurationRecorderForSecurityHubCSPM
```

### Findings detectados

Entre los hallazgos observados:

```text
CRITICAL
Hardware MFA should be enabled for the root user

HIGH
CloudTrail should be enabled and configured with a multi-Region trail

HIGH
GuardDuty should be enabled

MEDIUM
EBS default encryption should be enabled

MEDIUM
VPC endpoints should be configured

INFORMATIONAL
ECR private repositories should have image scanning configured

INFORMATIONAL
Port 8001 is reachable from an Internet Gateway
```

---

## 10. Vulnerabilidades de contenedores

Las imágenes fueron publicadas en Amazon ECR:

```text
obs-multicloud/service-a
obs-multicloud/service-b
obs-multicloud/data-service
```

Amazon Inspector realizó el escaneo de vulnerabilidades.

Resultados por imagen:

| Severity | Findings |
|---|---:|
| Critical | 6 |
| High | 10 |
| Medium | 11 |
| Low | 2 |
| Total | 29 |

Las tres imágenes presentaron el mismo perfil de vulnerabilidades.

El total agregado de findings entre las tres imágenes es:

```text
87 findings
```

Esto no representa necesariamente 87 CVEs únicas, debido a vulnerabilidades compartidas entre imágenes.

### Ejemplos de CVEs

```text
CVE-2026-5450
Severity: CRITICAL
Package: glibc 2.41

CVE-2026-13221
Severity: CRITICAL
Package: perl 5.40.1

CVE-2026-12087
Severity: CRITICAL
Package: perl 5.40.1

CVE-2026-11822
Severity: HIGH
Package: sqlite3 3.46.1

CVE-2026-25645
Severity: MEDIUM
Package: requests 2.32.3
```

---

## 11. Failed Authentication

Se generaron intentos controlados de autenticación fallida sobre un usuario IAM.

CloudTrail registró:

```text
eventName = ConsoleLogin
userName = observability-lab
errorMessage = Failed authentication
ConsoleLogin = Failure
MFAUsed = No
```

Los eventos fueron enviados a:

```text
CloudTrail
   |
   v
CloudWatch Logs
/aws/cloudtrail/observability
```

Se creó un Metric Filter:

```text
{ ($.eventName = ConsoleLogin) &&
  ($.errorMessage = "Failed authentication") }
```

La métrica resultante fue:

```text
Namespace:
Observability/Security

Metric:
FailedAuthentication
```

Resultado validado:

```text
FailedAuthentication = 2
```

---

## 12. Golden Signals de Seguridad

Se creó el dashboard:

```text
obs-multicloud-golden-signals-security
```

en Amazon CloudWatch.

Las métricas personalizadas son:

```text
FailedAuthentication
AcceptedNetworkFlows
RejectedNetworkFlows
```

El dashboard integra:

- Failed Authentication.
- Network Traffic ACCEPT/REJECT.
- Active CVEs.
- Security Posture.

---

## 13. CloudTrail

Se creó un trail:

```text
obs-multicloud-trail
```

Características:

```text
Multi-region: true
Logging: true
Log file validation: enabled
```

CloudWatch Log Group:

```text
/aws/cloudtrail/observability
```

---

## 14. Módulo D - Chaos Engineering

Se realizaron dos experimentos controlados.

### Experimento 1 - Latencia

Se inyectaron:

```text
+200 ms
```

en `service-b`.

Resultados:

```text
P95 = 267.01 ms
P99 = 278.64 ms
Availability = 100 %
```

SLO:

```text
P99 < 250 ms
```

Resultado:

```text
SLO VIOLATED
```

### Experimento 2 - Error injection

Se configuró:

```text
CHAOS_ERROR_RATE = 0.10
```

en `data-service`.

Durante la prueba de carga:

```text
Requests: 500
Successful: 492
Errors: 8
Observed error rate: 1.6 %
P95: 327.96 ms
P99: 357.24 ms
```

La combinación de error rate y latencia activó el detector AIOps.

### Mean Time To Detect

```text
MTTD = 2.333 segundos
```

Por tanto:

```text
MTTD < 2 minutos
```

---

## 15. Error Budget y SLO

SLO definido para el laboratorio:

```text
Availability >= 99.9 %
Error rate < 1 %
P99 < 250 ms
```

Los experimentos demostraron cómo las fallas afectan:

- Latencia.
- Error rate.
- Consumo del error budget.
- Cumplimiento del SLO.
- Acción operativa.

---

## 16. Infraestructura como Código

La infraestructura AWS fue gestionada mediante Terraform.

Entre los recursos desplegados:

```text
VPC
Subnets
Security Groups
EC2
RDS PostgreSQL
ECR
VPC Flow Logs
CloudWatch
CloudTrail
AWS Config
Security Hub
Security Dashboard
IAM
S3
```

Comandos principales:

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

---

## 17. Resultados principales

| Indicador | Resultado |
|---|---:|
| AIOps noise reduction | 91.67 % |
| MTTD | 2.333 s |
| Chaos latency | +200 ms |
| Chaos P99 | 278.64 ms |
| Load test P99 | 357.24 ms |
| Failed Authentication | 2 |
| CVEs Critical / imagen | 6 |
| CVEs High / imagen | 10 |
| CVEs Medium / imagen | 11 |
| CVEs Low / imagen | 2 |
| Security Hub | READY |
| CloudTrail | Logging |
| VPC Flow Logs | Enabled |

---

## 18. Observability Foundation Blueprint

La solución fue evaluada sobre ocho dominios de madurez de observabilidad.

Fortalezas:

- Instrumentación distribuida.
- OpenTelemetry.
- Correlación mediante trace ID.
- Métricas y SLO.
- AIOps.
- Chaos Engineering.
- Security Observability.
- Infrastructure as Code.

Áreas de evolución:

- Service Mesh.
- Policy as Code.
- Automated remediation.
- Continuous vulnerability remediation.
- SLO-based deployment gates.
- Runbooks automatizados.

---

## 19. Roadmap de madurez - 3 meses

### Mes 1

- Endurecer imágenes Docker.
- Actualizar dependencias vulnerables.
- Reducir CVEs Critical y High.
- Agregar alarmas sobre Security Hub.

### Mes 2

- Implementar service mesh.
- Implementar mTLS entre servicios.
- Centralizar políticas de resiliencia.
- Incorporar dashboards operacionales adicionales.

### Mes 3

- Automatizar remediación.
- Incorporar Policy as Code.
- Integrar observabilidad con CI/CD.
- Incorporar quality gates basados en SLO.
- Automatizar ejecución de experimentos de Chaos Engineering.

---

## 20. Ejecución local

Desde:

```bash
cd lab
```

Ejecutar:

```bash
docker compose up -d --build
```

Validar:

```bash
curl http://localhost:8001/api/order
```

Servicios:

```text
service-a     :8001
service-b     :8002
data-service  :8003
PostgreSQL    :5432
Prometheus    :9090
```

---

## 21. AWS

La infraestructura se encuentra en:

```text
terraform/aws
```

Inicializar:

```bash
terraform init
```

Validar:

```bash
terraform validate
```

Plan:

```bash
terraform plan
```

Aplicar:

```bash
terraform apply
```

---

## 22. Seguridad

No se deben publicar:

```text
terraform.tfstate
terraform.tfvars
AWS Access Keys
AWS Secret Keys
Passwords
Tokens
Secrets
```

Estos archivos deben permanecer excluidos mediante `.gitignore`.

---

## 23. Evidencias

Las evidencias del laboratorio incluyen:

- Trazas OpenTelemetry.
- Logs correlacionados.
- Métricas Prometheus.
- Incidentes AIOps.
- Ejecuciones Chaos.
- VPC Flow Logs.
- Security Hub findings.
- ECR scan findings.
- CVEs de Amazon Inspector.
- CloudTrail failed authentication.
- CloudWatch dashboard.
- Terraform plans y applies.

---

## 24. Video demostrativo

El video de demostración debe mostrar:

1. Arquitectura del laboratorio.
2. Flujo `service-a → service-b → data-service`.
3. OpenTelemetry.
4. Prometheus.
5. Detector AIOps.
6. Chaos Engineering.
7. AWS VPC Flow Logs.
8. Security Hub.
9. ECR / Inspector.
10. Failed Authentication.
11. CloudWatch Golden Signals Dashboard.

**Enlace del video:**

```text
PENDIENTE_AGREGAR_URL_DEL_VIDEO
```

---

## 25. Entregables

La entrega incluye:

```text
Repositorio GitHub
IaC Terraform
Código fuente
Configuración OpenTelemetry
Configuración Prometheus
Detector AIOps
Experimentos Chaos
Dashboard de seguridad
Informe PDF
Video demostrativo
```

---

## 26. Conclusiones

El laboratorio demuestra una estrategia integral de observabilidad que combina observabilidad tradicional, AIOps, resiliencia y seguridad.

La utilización de OpenTelemetry permite desacoplar la instrumentación de una plataforma específica, mientras que Prometheus permite evaluar SLI y SLO.

Los experimentos de Chaos Engineering demostraron la capacidad del sistema para detectar degradaciones en segundos.

La incorporación de AWS Security Hub, CloudTrail, VPC Flow Logs, ECR y Amazon Inspector amplía el alcance hacia Security Observability, permitiendo correlacionar tráfico, vulnerabilidades, autenticaciones fallidas y postura de seguridad.

Finalmente, Terraform permite reproducir la infraestructura y mantener las configuraciones cloud bajo control de versiones.

---

## Autor

**Camilo Andres Porras**

Maestría en Arquitectura de Software

2026
