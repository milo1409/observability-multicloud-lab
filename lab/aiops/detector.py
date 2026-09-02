import csv
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
SLO_P99_MS = float(os.getenv("SLO_P99_MS", "250"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))
WARMUP_SECONDS = int(os.getenv("WARMUP_SECONDS", "60"))
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "60"))

SHARED_DIR = Path("/shared")
SHARED_DIR.mkdir(parents=True, exist_ok=True)

baseline_samples = []
baseline_ready = False
baseline_mean = 0.0
baseline_std = 0.0
start_time = time.time()

active_incident = None
incident_opened_at = 0.0
static_alert_count = 0
aiops_incident_count = 0
suppressed_alert_count = 0

def prom_query(query):
    r = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=5
    )
    r.raise_for_status()
    data = r.json()
    results = data.get("data", {}).get("result", [])
    if not results:
        return 0.0
    value = results[0].get("value", [None, "0"])[1]
    if value in ("NaN", "+Inf", "-Inf"):
        return 0.0
    return float(value)

def get_error_rate():
    total = prom_query(
        'sum(rate(app_http_requests_total{service_name="service-a"}[1m]))'
    )
    errors = prom_query(
        'sum(rate(app_http_requests_total{service_name="service-a",http_response_status_code=~"5.."}[1m]))'
    )
    return (errors / total) if total > 0 else 0.0

def get_p99():
    return prom_query(
        'histogram_quantile(0.99, sum by (le) '
        '(rate(app_http_duration_milliseconds_bucket{service_name="service-a"}[1m])))'
    )

def latest_failed_trace():
    p = SHARED_DIR / "latest_failed_trace.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def append_baseline(ts, error_rate, p99):
    p = SHARED_DIR / "baseline_samples.csv"
    exists = p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["timestamp_utc", "error_rate", "p99_ms"])
        w.writerow([ts, error_rate, p99])

def append_incident(incident):
    with (SHARED_DIR / "incidents.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(incident) + "\n")
    (SHARED_DIR / "latest_incident.json").write_text(
        json.dumps(incident, indent=2), encoding="utf-8"
    )

def write_summary():
    reduction = 0.0
    if static_alert_count > 0:
        reduction = (static_alert_count - aiops_incident_count) / static_alert_count * 100.0

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "static_alert_count": static_alert_count,
        "aiops_incident_count": aiops_incident_count,
        "suppressed_alert_count": suppressed_alert_count,
        "noise_reduction_percent": round(reduction, 2),
        "cooldown_seconds": COOLDOWN_SECONDS
    }
    (SHARED_DIR / "alert_reduction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

print("AIOps detector v3.1 starting")
print(
    f"Warmup={WARMUP_SECONDS}s Poll={POLL_SECONDS}s "
    f"SLO_P99={SLO_P99_MS}ms Cooldown={COOLDOWN_SECONDS}s"
)

while True:
    try:
        now_epoch = time.time()
        now_utc = datetime.now(timezone.utc).isoformat()

        error_rate = get_error_rate()
        p99 = get_p99()

        if not baseline_ready:
            baseline_samples.append(error_rate)
            append_baseline(now_utc, error_rate, p99)
            elapsed = now_epoch - start_time
            print(
                f"[BASELINE] elapsed={elapsed:.0f}s "
                f"error_rate={error_rate:.4f} p99_ms={p99:.2f}"
            )

            if elapsed >= WARMUP_SECONDS and len(baseline_samples) >= 6:
                baseline_mean = statistics.mean(baseline_samples)
                baseline_std = statistics.pstdev(baseline_samples)
                baseline_ready = True
                print(
                    f"[BASELINE READY] mean={baseline_mean:.6f} "
                    f"std={baseline_std:.6f} "
                    f"threshold={baseline_mean + 2 * baseline_std:.6f}"
                )
        else:
            threshold = baseline_mean + 2 * baseline_std

            error_anomaly = error_rate > threshold and error_rate > 0
            latency_violation = p99 > SLO_P99_MS

            # Simula el ruido del sistema de umbrales estáticos:
            # cada ciclo que cumple cualquiera de los dos umbrales cuenta como alerta.
            if error_anomaly or latency_violation:
                static_alert_count += 1

            correlated = error_anomaly and latency_violation

            print(
                f"[CHECK] error_rate={error_rate:.4f} "
                f"threshold={threshold:.4f} "
                f"p99_ms={p99:.2f} slo={SLO_P99_MS:.2f} "
                f"error_anomaly={error_anomaly} "
                f"latency_violation={latency_violation} "
                f"correlated={correlated}"
            )

            if correlated:
                failed = latest_failed_trace()

                if (
                    active_incident is not None
                    and now_epoch - incident_opened_at < COOLDOWN_SECONDS
                ):
                    suppressed_alert_count += 1
                    print(
                        f"[SUPPRESSED] active_incident={active_incident} "
                        f"suppressed_total={suppressed_alert_count}"
                    )
                else:
                    aiops_incident_count += 1
                    active_incident = f"OBS-{int(now_epoch)}"
                    incident_opened_at = now_epoch

                    failed_ts = failed.get("timestamp_epoch")
                    technical_detection_seconds = None
                    if isinstance(failed_ts, (int, float)):
                        technical_detection_seconds = round(now_epoch - failed_ts, 3)

                    incident = {
                        "incident_id": active_incident,
                        "detected_at_utc": now_utc,
                        "detected_at_epoch": now_epoch,
                        "service": "data-service",
                        "error_rate": error_rate,
                        "baseline_mean": baseline_mean,
                        "baseline_std": baseline_std,
                        "dynamic_threshold": threshold,
                        "latency_p99_ms": p99,
                        "slo_threshold_ms": SLO_P99_MS,
                        "trace_id": failed.get("trace_id", "unknown"),
                        "failed_trace": failed,
                        "technical_detection_seconds": technical_detection_seconds,
                        "status": "ACTIONABLE",
                        "cooldown_seconds": COOLDOWN_SECONDS
                    }
                    append_incident(incident)

                    print("=" * 72)
                    print("AIOPS INCIDENT DETECTED")
                    print(json.dumps(incident, indent=2))
                    print("=" * 72)

            write_summary()
            time.sleep(POLL_SECONDS)

    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        time.sleep(POLL_SECONDS)
