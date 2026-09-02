# AWS Observability Lab — Low Cost

Esta variante minimiza el costo del laboratorio.

## Qué crea por defecto

- VPC
- 2 subredes públicas
- Internet Gateway
- Security Group
- 3 repositorios ECR
- VPC Flow Logs
- CloudWatch Log Group con retención de 1 día

## Qué NO crea por defecto

- ALB
- ECS/Fargate
- NAT Gateway
- RDS
- Security Hub
- Container Insights

Los servicios más costosos se habilitan solo cuando sean necesarios para producir evidencia.

## Perfil recomendado

```hcl
enable_flow_logs    = true
enable_rds          = false
enable_security_hub = false
```

## Fase 1 — Network Observability

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

Con esto se pueden obtener evidencias de VPC Flow Logs sin mantener ALB, ECS ni RDS activos.

## Fase 2 — RDS solo durante la evidencia

Cambiar temporalmente:

```hcl
enable_rds = true
```

Aplicar:

```bash
terraform apply
```

Obtener evidencias y después volver a:

```hcl
enable_rds = false
```

y ejecutar:

```bash
terraform apply
```

## Fase 3 — Security Hub solo durante la evidencia

Cambiar:

```hcl
enable_security_hub = true
```

Aplicar, tomar capturas de Findings y luego desactivar:

```hcl
enable_security_hub = false
```

## Contenedores

Los repositorios ECR permiten publicar:

- service-a
- service-b
- data-service

La ejecución cloud completa puede hacerse en una instancia EC2 pequeña de laboratorio usando Docker Compose,
evitando mantener ALB y tres tareas Fargate encendidas.

## Estrategia de costo

Para el laboratorio:

1. Crear infraestructura.
2. Obtener evidencias.
3. Habilitar temporalmente RDS/Security Hub.
4. Tomar capturas.
5. Deshabilitarlos.
6. Ejecutar `terraform destroy` al terminar.

## Destrucción

```bash
terraform destroy
```

Nunca dejar el sandbox desplegado después de finalizar la práctica.


## EC2 low-cost para ejecutar el laboratorio

Por defecto:

```hcl
enable_ec2 = false
```

Para crear una sola EC2:

```hcl
enable_ec2 = true
ec2_instance_type = "t3.micro"
```

No se abre el puerto 22. La administración se realiza con AWS Systems Manager Session Manager.

Después de aplicar:

```bash
terraform output ec2_instance_id
terraform output ec2_public_ip
```

Validar SSM:

```bash
aws ssm describe-instance-information --region us-east-1
```

Abrir sesión:

```bash
aws ssm start-session --target INSTANCE_ID --region us-east-1
```

Dentro de la instancia:

```bash
docker --version
systemctl status docker
```

La instancia instala automáticamente Docker y Git mediante user_data.

Para minimizar costo, cuando termine la evidencia:

```hcl
enable_ec2 = false
```

y luego:

```bash
terraform apply
```
