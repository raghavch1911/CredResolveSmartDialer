# CredResolve SmartDialer

A safety-first outbound dialing prototype built with **Python, FastAPI, SQLite, and React**. The project demonstrates progressive call allocation, rule-based predictive pacing, agent availability management, provider-failure handling, and safe processing of provider events.

## Features

- **Progressive dialing:** Allocates queued borrowers to available agents.
- **Predictive pacing:** Uses available agents, active calls, answer rate, ringing calls, and batch limits to recommend dialing volume.
- **Safety Controller:** Limits requested dialing based on available agents, queued borrowers, and provider health.
- **State management:** Tracks agent and call lifecycle states.
- **Mock telecom providers:** Includes two simulated providers with different latency and failure characteristics.
- **Provider-event deduplication:** Uses unique event IDs to prevent duplicate event processing.
- **Out-of-order event handling:** Applies state-transition rules and protects terminal call states.
- **Circuit breaker:** Helps prevent repeated requests to a failing provider.
- **Failure recovery:** Includes utilities to identify stale calls and reconcile eligible failed reservations.
- **Interactive dashboard:** React-based interface for viewing agents, borrowers, calls, provider health, and dialing controls.
- **Automated tests:** Covers state transitions, allocation, event handling, pacing, circuit-breaker behavior, and concurrent allocation.
- **Simulation and load testing:** Includes scripts for illustrative dialing scenarios and HTTP endpoint testing.

## Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Database | SQLite |
| Frontend | React, Vite |
| API validation | Pydantic |
| Testing | Pytest, HTTPX |
| Provider integration | Mock Provider A and Mock Provider B |

## Project Structure

```text
CredResolveSmartDialer/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   │   └── states.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── mock_a.py
│   │   └── mock_b.py
│   └── services/
│       ├── registry.py
│       ├── dialer.py
│       ├── safety.py
│       ├── pacing.py
│       ├── call_service.py
│       ├── events.py
│       ├── circuit_breaker.py
│       └── recovery.py
├── frontend/
│   ├── src/
│   ├── package.json
│   └── index.html
├── tests/
│   ├── test_smartdialer.py
│   ├── test_pacing.py
│   └── test_circuit_breaker.py
├── scripts/
│   ├── simulate.py
│   └── load_test.py
├── docs/
│   └── architecture.md
├── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.11 or later
- Node.js and npm
- Windows, macOS, or Linux
- Git (optional, for cloning the repository)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/raghavch1911/CredResolveSmartDialer.git
cd CredResolveSmartDialer
```

### 2. Set up the backend

**Windows — CMD**

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Start the backend API

From the project root, with the virtual environment activated:

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger documentation: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

Keep this terminal running.

### 4. Set up and start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL displayed in the terminal, normally:

`http://localhost:5173`

The frontend communicates with the FastAPI backend. Start the backend before using the dashboard.

## Running Tests

From the project root, activate the virtual environment and run:

```bash
python -m pytest tests -v
```

The test suite covers core state transitions, progressive allocation, event handling, concurrent allocation, predictive pacing, and circuit-breaker behavior.

## Running the Simulation

From the project root:

```bash
python scripts/simulate.py
```

The script runs illustrative dialing scenarios with different answer rates, provider latencies, and failure rates.

**Note:** Simulation results are illustrative and should not be interpreted as validated production dialing or telecom performance metrics.

## Running the HTTP Load Test

First, start the backend API. Open another terminal at the project root, activate the virtual environment, and run:

```bash
python scripts/load_test.py
```

The script sends concurrent HTTP requests and reports request success, failures, elapsed time, throughput, and latency.

Load-test results depend on the local machine, server configuration, and current environment. They should not be treated as production capacity benchmarks.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API welcome response |
| `GET` | `/health` | Health check |
| `POST` | `/agents` | Register an agent |
| `GET` | `/agents` | List agents |
| `POST` | `/borrowers` | Register a borrower |
| `GET` | `/borrowers` | List borrowers |
| `POST` | `/dial/allocate` | Allocate a progressive call |
| `POST` | `/dial/predictive` | Request predictive dialing |
| `POST` | `/calls/initiate` | Initiate a mock call |
| `GET` | `/calls` | List call records |
| `POST` | `/safety/evaluate` | Evaluate a dialing request against safety limits |
| `POST` | `/provider/events` | Process a provider event |
| `POST` | `/agents/{agent_id}/available` | Mark an agent available |
| `GET` | `/providers/health` | Inspect provider circuit-breaker status |

For request schemas and example payloads, open the Swagger documentation at `http://127.0.0.1:8000/docs`.

## Architecture Overview

The project separates API handling, dialing decisions, safety checks, provider integration, and event processing.

1. **FastAPI layer:** Exposes endpoints for registration, allocation, dialing, events, and health checks.
2. **Progressive Dialer:** Allocates queued borrowers to available agents.
3. **Predictive Pacing Engine:** Calculates a recommended dialing batch from current operating conditions.
4. **Safety Controller:** Applies preflight limits before dialing requests are processed.
5. **Call Service:** Coordinates allocation, provider requests, and call status updates.
6. **Mock Providers:** Simulate provider responses and selected failure scenarios.
7. **Provider Event Handler:** Deduplicates provider events and validates state transitions.
8. **SQLite:** Persists agents, borrowers, calls, and processed provider-event IDs.
9. **Circuit Breaker and Recovery Utilities:** Support provider-failure containment and stale-call reconciliation.

See [`docs/architecture.md`](docs/architecture.md) for the architecture diagram and design decisions.

## Design Considerations

- **Transactional allocation:** SQLite write transactions serialize allocation operations to reduce the risk of assigning the same agent or borrower to multiple calls.
- **Idempotency:** Unique identifiers are used to detect repeated allocation requests or provider events where implemented.
- **State transitions:** Agent and call states are constrained by explicit transition rules.
- **Safety-first pacing:** Dialing recommendations are limited by available agents and queued borrowers.
- **Failure containment:** Circuit-breaker logic helps handle repeated provider failures.
- **Reconciliation:** Stale-call detection and reservation reconciliation utilities provide a foundation for recovery workflows.

## Limitations and Future Improvements

This is an educational prototype, not a production-ready outbound dialing platform.

- Telecom providers are mocked; no real calls are placed.
- SQLite is suitable for a local prototype but is not a substitute for a production database and distributed concurrency architecture.
- Provider timeout recovery requires reconciliation; a complete automated reconciliation worker is not included.
- Circuit-breaker state is maintained in memory and is not shared across multiple backend processes.
- Predictive pacing uses simplified rules rather than a trained forecasting model.
- The simulation is illustrative and does not model all real-world telecom behavior or validate production performance.
- Production deployment would require stronger observability, authentication, authorization, deployment configuration, and more comprehensive failure-recovery testing.

Potential future improvements include PostgreSQL, Redis-backed coordination, background reconciliation workers, provider webhooks, stronger integration tests, and production-grade metrics.

## License

No license has been specified. Add a license file if you intend to distribute the project under a particular open-source license.

---

**Repository:** https://github.com/raghavch1911/CredResolveSmartDialer/
