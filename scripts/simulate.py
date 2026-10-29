
import math
import random


def simulate(
    name,
    agents,
    answer_rate,
    avg_talk_seconds,
    provider_latency_ms,
    provider_failure_rate,
    duration_seconds=60,
):
    random.seed(42)

    available = agents
    connected = 0
    calls_initiated = 0
    calls_connected = 0
    abandoned = 0
    talk_time_remaining = []

    for _ in range(duration_seconds):
        # Finish calls whose simulated talk time has elapsed.
        talk_time_remaining = [
            remaining - 1
            for remaining in talk_time_remaining
            if remaining > 1
        ]

        connected = len(talk_time_remaining)
        available = agents - connected

        # Estimate calls that could answer during this time step.
        batch = min(10, available)
        latency_seconds = max(0, provider_latency_ms / 1000)

        for _ in range(batch):
            if random.random() < provider_failure_rate:
                continue

            calls_initiated += 1

            if random.random() < answer_rate:
                if available > 0:
                    calls_connected += 1
                    available -= 1
                    talk_time_remaining.append(
                        max(1, math.ceil(avg_talk_seconds))
                    )
                else:
                    abandoned += 1

    utilization = (
        calls_connected / max(1, calls_initiated)
    ) * 100

    return {
        "scenario": name,
        "agents": agents,
        "answer_rate": answer_rate,
        "avg_talk_seconds": avg_talk_seconds,
        "provider_latency_ms": provider_latency_ms,
        "provider_failure_rate": provider_failure_rate,
        "calls_initiated": calls_initiated,
        "calls_connected": calls_connected,
        "abandoned": abandoned,
        "connection_rate_percent": round(utilization, 2),
    }


if __name__ == "__main__":
    scenarios = [
        ("A", 10, 0.20, 120, 100, 0.02),
        ("B", 10, 0.50, 90, 200, 0.05),
        ("C", 10, 0.70, 180, 500, 0.10),
        ("D", 10, 0.35, 120, 1000, 0.25),
    ]

    for scenario in scenarios:
        result = simulate(*scenario)
        print(result)
