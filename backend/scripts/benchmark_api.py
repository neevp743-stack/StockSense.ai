import time
import json
from fastapi.testclient import TestClient
from backend.main import app

def run_benchmarks():
    client = TestClient(app)

    endpoints = [
        ("GET", "/api/system/status"),
        ("GET", "/api/stocks/RELIANCE/history?limit=100"),
        ("GET", "/api/stocks/INFY/history?limit=100"),
        ("GET", "/api/stocks/TCS/history?limit=100"),
        ("GET", "/api/stocks/RELIANCE/prediction"),
        ("GET", "/api/stocks/INFY/prediction"),
        ("GET", "/api/stocks/TCS/prediction"),
        ("GET", "/api/assets/RELIANCE/technical-analysis"),
    ]

    print("=" * 60)
    print("STOCKSENSE AI — API PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"{'Endpoint':<45} | {'Cold (ms)':<10} | {'Warm (ms)':<10}")
    print("-" * 71)

    results = {}
    for method, path in endpoints:
        # Cold request
        t0 = time.perf_counter()
        res_cold = client.request(method, path)
        t1 = time.perf_counter()
        cold_ms = (t1 - t0) * 1000.0

        # Warm request
        t2 = time.perf_counter()
        res_warm = client.request(method, path)
        t3 = time.perf_counter()
        warm_ms = (t3 - t2) * 1000.0

        results[path] = {
            "cold_ms": round(cold_ms, 2),
            "warm_ms": round(warm_ms, 2),
            "status_code": res_warm.status_code
        }

        print(f"{path:<45} | {cold_ms:<10.2f} | {warm_ms:<10.2f}")

    print("=" * 60)
    return results

if __name__ == "__main__":
    run_benchmarks()
