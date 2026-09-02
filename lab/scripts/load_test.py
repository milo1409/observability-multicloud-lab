import argparse
import time
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://localhost:8001/api/order")
parser.add_argument("--requests", type=int, default=100)
parser.add_argument("--delay", type=float, default=0.2)
args = parser.parse_args()

ok = 0
errors = 0
latencies = []

for i in range(args.requests):
    start = time.perf_counter()
    try:
        response = requests.get(args.url, timeout=10)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)
        if response.ok:
            ok += 1
        else:
            errors += 1
        print(i + 1, response.status_code, f"{elapsed:.2f} ms")
    except Exception as exc:
        errors += 1
        print(i + 1, "ERROR", exc)
    time.sleep(args.delay)

latencies.sort()

def percentile(values, p):
    if not values:
        return 0
    index = min(len(values) - 1, int((p / 100) * len(values)))
    return values[index]

total = ok + errors
print()
print("SUMMARY")
print("total:", total)
print("ok:", ok)
print("errors:", errors)
print("error_rate:", round(errors / total * 100, 2) if total else 0, "%")
print("p95_ms:", round(percentile(latencies, 95), 2))
print("p99_ms:", round(percentile(latencies, 99), 2))
