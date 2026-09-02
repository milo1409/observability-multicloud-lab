# Observability Multicloud Lab v3

Incluye:

- 3 microservicios
- PostgreSQL
- OpenTelemetry: traces, metrics y logs
- Prometheus Server
- detector AIOps
- baseline dinámico
- regla `error_rate > baseline + 2σ AND P99 > SLO`
- correlación con `trace_id`
- persistencia de incidentes
- controles de Chaos Engineering

## Arranque

```cmd
docker compose down -v
docker compose up -d --build
docker compose ps
```

## Generar línea base

El detector necesita 60 segundos de baseline. Durante ese minuto genere tráfico normal:

```cmd
docker run --rm --network observability-multicloud-v3_default -v "%cd%\scripts:/scripts" python:3.12-slim sh -c "pip install requests && python /scripts/load_test.py --url http://service-a:8001/api/order --requests 200 --delay 0.2"
```

Ver detector:

```cmd
docker compose logs -f aiops-detector
```

Espere:

```text
[BASELINE READY]
```

## Prometheus

Abrir:

```text
http://localhost:9090
```

## CHAOS-02

Después de `BASELINE READY`:

```yaml
service-b:
  CHAOS_LATENCY_MS: "300"

data-service:
  CHAOS_ERROR_RATE: "0.10"
```

Recrear:

```cmd
docker compose up -d --force-recreate service-b data-service
```

Registrar inicio:

```cmd
echo %date% %time%
```

Generar carga:

```cmd
docker run --rm --network observability-multicloud-v3_default -v "%cd%\scripts:/scripts" python:3.12-slim sh -c "pip install requests && python /scripts/load_test.py --url http://service-a:8001/api/order --requests 300 --delay 0.1"
```

En otra terminal:

```cmd
docker compose logs -f aiops-detector
```

La evidencia esperada es:

```text
AIOPS INCIDENT DETECTED
error_rate > baseline + 2σ
latency_p99_ms > 250
trace_id = ...
status = ACTIONABLE
```

## Consultar incidente

```cmd
docker compose exec aiops-detector cat /shared/latest_incident.json
```

## Restaurar

```yaml
CHAOS_LATENCY_MS: "0"
CHAOS_ERROR_RATE: "0"
```

```cmd
docker compose up -d --force-recreate service-b data-service
```


## AIOps v3.1 — deduplicación y reducción de ruido

El detector aplica:

```text
error_rate > baseline + 2σ
AND
P99 > 250 ms
```

Cuando existe un incidente activo, nuevas detecciones equivalentes durante 60 segundos se suprimen:

```text
[SUPPRESSED] active_incident=OBS-...
```

Resumen cuantitativo:

```cmd
docker compose exec aiops-detector cat /shared/alert_reduction_summary.json
```

Ejemplo:

```json
{
  "static_alert_count": 14,
  "aiops_incident_count": 1,
  "suppressed_alert_count": 13,
  "noise_reduction_percent": 92.86,
  "cooldown_seconds": 60
}
```

Esto permite comparar cuantitativamente el sistema de umbrales independientes con el
sistema AIOps correlacionado y deduplicado.
