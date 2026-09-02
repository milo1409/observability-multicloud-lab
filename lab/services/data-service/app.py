import logging
import os
import time

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.instrumentation.logging import LoggingInstrumentor

SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "unknown-service")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")

resource = Resource.create({
    "service.name": SERVICE_NAME,
    "deployment.environment.name": os.getenv("DEPLOYMENT_ENVIRONMENT", "sandbox"),
    "cloud.provider": os.getenv("CLOUD_PROVIDER", "local"),
})

trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True),
    export_interval_millis=5000
)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)
meter = metrics.get_meter(__name__)

request_counter = meter.create_counter("app.http.requests", unit="{request}")
error_counter = meter.create_counter("app.http.errors", unit="{error}")
request_duration = meter.create_histogram("app.http.duration", unit="ms")

logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
set_logger_provider(logger_provider)

LoggingInstrumentor().instrument(set_logging_format=True)
logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
logger.addHandler(LoggingHandler(level=logging.INFO, logger_provider=logger_provider))

def current_trace_context():
    span = trace.get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return "0" * 32, "0" * 16
    return format(context.trace_id, "032x"), format(context.span_id, "016x")

def record_request(route, method, status_code, started_at):
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    attrs = {
        "service.name": SERVICE_NAME,
        "http.route": route,
        "http.request.method": method,
        "http.response.status_code": int(status_code),
    }
    request_counter.add(1, attrs)
    request_duration.record(duration_ms, attrs)
    if int(status_code) >= 400:
        error_counter.add(1, attrs)
    trace_id, span_id = current_trace_context()
    logger.info(
        "request_completed service=%s method=%s route=%s status=%s duration_ms=%.2f trace_id=%s span_id=%s",
        SERVICE_NAME, method, route, status_code, duration_ms, trace_id, span_id
    )

from flask import Flask, jsonify
import random
import json
from pathlib import Path
import psycopg
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
PsycopgInstrumentor().instrument()

DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "observability")
DB_USER = os.getenv("DB_USER", "observability")
DB_PASSWORD = os.getenv("DB_PASSWORD", "observability")
CHAOS_ERROR_RATE = float(os.getenv("CHAOS_ERROR_RATE", "0"))
SHARED_DIR = Path("/shared")
SHARED_DIR.mkdir(parents=True, exist_ok=True)

def get_connection():
    return psycopg.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                           user=DB_USER, password=DB_PASSWORD)

def write_failed_trace(trace_id, span_id, status, reason):
    payload = {
        "timestamp_epoch": time.time(),
        "service": SERVICE_NAME,
        "trace_id": trace_id,
        "span_id": span_id,
        "status": status,
        "reason": reason
    }
    (SHARED_DIR / "latest_failed_trace.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

@app.get("/health")
def health():
    started = time.perf_counter()
    record_request("/health", "GET", 200, started)
    return jsonify({"status": "ok", "service": SERVICE_NAME})

@app.get("/data")
def data():
    started = time.perf_counter()
    status = 200
    if CHAOS_ERROR_RATE > 0 and random.random() < CHAOS_ERROR_RATE:
        status = 500
        trace_id, span_id = current_trace_context()
        write_failed_trace(trace_id, span_id, 500, "Injected chaos error")
        logger.error("chaos_error_injected service=%s error_rate=%s trace_id=%s span_id=%s",
                     SERVICE_NAME, CHAOS_ERROR_RATE, trace_id, span_id)
        record_request("/data", "GET", status, started)
        return jsonify({"service": SERVICE_NAME, "error": "Injected chaos error",
                        "trace_id": trace_id}), status
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS lab_requests (
                        id BIGSERIAL PRIMARY KEY,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("INSERT INTO lab_requests DEFAULT VALUES RETURNING id, created_at")
                row = cur.fetchone()
                conn.commit()
        return jsonify({"service": SERVICE_NAME,
                        "db_provider": os.getenv("DB_PROVIDER", "local"),
                        "id": row[0], "created_at": row[1].isoformat()}), 200
    except Exception as exc:
        status = 500
        trace_id, span_id = current_trace_context()
        write_failed_trace(trace_id, span_id, 500, str(exc))
        logger.exception("database_error service=%s trace_id=%s span_id=%s error=%s",
                         SERVICE_NAME, trace_id, span_id, exc)
        return jsonify({"service": SERVICE_NAME, "error": str(exc),
                        "trace_id": trace_id}), status
    finally:
        record_request("/data", "GET", status, started)

app.run(host="0.0.0.0", port=8003)
