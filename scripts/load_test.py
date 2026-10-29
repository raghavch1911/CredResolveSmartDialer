
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx


BASE_URL = "http://127.0.0.1:8000"


def request_health(_):
    started = time.perf_counter()

    try:
        response = httpx.get(
            f"{BASE_URL}/health",
            timeout=5,
        )
        elapsed = time.perf_counter() - started

        return response.status_code, elapsed
    except httpx.HTTPError:
        return 0, time.perf_counter() - started


def main():
    total_requests = 200
    workers = 20
    latencies = []
    failures = 0

    started = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(request_health, i)
            for i in range(total_requests)
        ]

        for future in as_completed(futures):
            status, elapsed = future.result()
            latencies.append(elapsed)

            if status != 200:
                failures += 1

    elapsed_total = time.perf_counter() - started
    successful = total_requests - failures

    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {successful}")
    print(f"Failed requests: {failures}")
    print(f"Duration: {elapsed_total:.2f}s")
    print(f"Throughput: {successful / elapsed_total:.2f} requests/s")

    if latencies:
        print(f"Average latency: {sum(latencies) / len(latencies) * 1000:.2f} ms")
        print(f"Max latency: {max(latencies) * 1000:.2f} ms")


if __name__ == "__main__":
    main()
