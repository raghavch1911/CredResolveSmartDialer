# CredResolve SmartDialer

A safety-first outbound dialing prototype built with **FastAPI, Python, SQLite, React, and Vite**. The system demonstrates progressive call allocation, predictive pacing, agent management, provider simulation, and safeguards against duplicate or unsafe call allocation.

## Features

- **Progressive Dialer:** Allocates one available agent and one queued borrower per call.
- **Predictive Pacing Engine:** Estimates how many calls to request based on the expected answer rate and current agent availability.
- **Safety Controller:** Checks agent capacity and borrower availability before approving call requests.
- **Agent Management:** Register agents and track their availability and dialing states.
- **Borrower Management:** Register borrowers and maintain the call queue.
- **Mock Telecom Providers:** Simulate providers with different latency and reliability characteristics.
- **Provider Event Processing:** Deduplicates provider events and handles terminal and out-of-order events.
- **Circuit Breaker:** Temporarily blocks new requests after repeated provider failures.
- **Interactive Dashboard:** Monitor agents, borrowers, call activity, dialing controls, and provider health.
- **Automated Tests:** Test state transitions, allocation, duplicate events, concurrency, pacing, and circuit-breaker behavior.
- **Simulation and Load Testing:** Run basic dialing scenarios and HTTP health-endpoint tests.

## Technology Stack

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Database | SQLite |
| Database access | Python `sqlite3` |
| Frontend | React, Vite, JavaScript |
| UI icons | Lucide React |
| API documentation | Swagger UI / OpenAPI |
| Testing | Pytest |
| HTTP testing | HTTPX |
| Provider integration | Mock telecom providers |

## Project Structure

```text
CredResolveSmartDialer/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── api/
│   ├── core/
│   ├── models/
│   │   └── states.py
│   ├── providers/
│   │   ├── base.py
│   │   ├── mock_a.py
│   │   └── mock_b.py
│   └── services/
│       ├── dialer.py
│       ├── pacing.py
│       ├── safety.py
│       ├── call_service.py
│       ├── circuit_breaker.py
│       ├── events.py
│       ├── recovery.py
│       └── registry.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
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
├── smartdialer.db
└── README.md
```

The database file is generated locally when the application initializes. Do not commit real borrower information or sensitive data.

## Prerequisites

- Python 3.11 or later
- Node.js and npm
- Git (optional, for version control)

Docker and a separately installed database server are not required for the local prototype.

## Installation and Setup

### 1. Clone or open the project

Open CMD in the project directory:

```cmd
cd /d D:\CredResolveSmartDialer
```

### 2. Set up the Python environment

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### 3. Start the backend

From the project root, run:

```cmd
python -m uvicorn app.main:app --reload
```

The backend will be available at:

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Keep this terminal running.

### 4. Start the React frontend

Open a second CMD terminal:

```cmd
cd /d D:\CredResolveSmartDialer\frontend
npm install
npm install lucide-react
npm run dev
```

Open the frontend URL displayed by Vite, usually:

http://localhost:5173

The frontend communicates with the local FastAPI backend. Both servers must be running for the dashboard to display live API data.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Backend health check |
| POST | `/agents` | Register an agent |
| GET | `/agents` | List agents |
| POST | `/borrowers` | Register a borrower |
| GET | `/borrowers` | List borrowers |
| POST | `/dial/allocate` | Allocate a progressive call |
| POST | `/calls/initiate` | Initiate a mock outbound call |
| GET | `/calls` | List call records |
| POST | `/safety/evaluate` | Evaluate a requested dialing batch |
| POST | `/dial/predictive` | Run a predictive dialing cycle |
| POST | `/provider/events` | Process a provider event |
| GET | `/providers/health` | Inspect circuit-breaker state |
| POST | `/agents/{agent_id}/available` | Make an eligible agent available |

See Swagger UI for request parameters, schemas, and response examples.

## How It Works

### Progressive Dialing

1. Find an available agent.
2. Find a queued borrower.
3. Reserve both within a database transaction.
4. Create a call record with a unique idempotency key.
5. Initiate the call through the selected mock provider.
6. Update the call and agent state based on the outcome.

Conditional updates and SQLite write transactions protect local resource allocation from competing requests.

### Predictive Pacing

The rule-based pacing engine estimates a requested batch using the answer-rate estimate, available agents, active calls, and configured batch limit.

The Safety Controller independently evaluates the requested number of calls against available agents, queued borrowers, and provider health. Individual call allocations must still succeed before a call can be initiated.

### Provider Failure Handling

The prototype includes two mock providers, a circuit breaker, event deduplication, and a recovery helper for stale reservations.

A timeout does not necessarily mean a provider failed to initiate a call. Ambiguous outcomes require reconciliation before releasing reserved resources or retrying the call.

## Testing

Activate the virtual environment and run:

```cmd
python -m pytest tests -v
```

The automated tests cover:

- Agent and call state transitions
- Progressive allocation
- Competing allocation requests
- Duplicate provider events
- Out-of-order terminal events
- Predictive pacing
- Circuit-breaker behavior

The current baseline test suite passed nine tests during development. Run the tests again against your final code to confirm the current result.

## Simulation

Run the scenario simulator from the project root:

```cmd
python scripts\simulate.py
```

The script compares example scenarios with different answer rates, talk times, provider latency values, and failure rates.

These results are illustrative, not validated production dialing forecasts.

## Load Test

Start the backend first, then run:

```cmd
python scripts\load_test.py
```

The script sends concurrent HTTP requests to the health endpoint and reports successful requests, failures, elapsed time, throughput, and response latency.

This is a basic HTTP endpoint test, not a benchmark of concurrent call allocation or production telecom throughput.

## Architecture

The principal flow is:

```text
Campaign / API
      |
      +--> Progressive Dialer
      |
      +--> Predictive Pacing Engine
                    |
                    v
             Safety Controller
                    |
                    v
              Call Allocator
                    |
             +------+------+
             |             |
         Mock A          Mock B
             |             |
             +------+------+
                    |
             Provider Events
                    |
                    v
               SQLite DB
```

The Safety Controller is intended to remain a mandatory gate between predictive recommendations and call initiation. See `docs/architecture.md` for the architecture diagram and design decisions.

## Design Decisions and Limitations

- **FastAPI:** Provides lightweight API development and interactive documentation.
- **SQLite:** Simplifies local installation and persistent storage.
- **React and Vite:** Provide a responsive dashboard for demonstrating the backend.
- **Mock providers:** Allow call initiation and provider failures to be tested without a live telecom account.
- **Rule-based pacing:** Keeps the predictive logic understandable and easy to inspect.

This is an engineering prototype, not a production-ready dialer. Before production use, further work is required on distributed worker coordination, provider-side idempotency, durable event processing, timeout reconciliation, coordinated circuit-breaker state, and robust recovery.

SQLite is appropriate for this local demonstration but is not the intended shared transactional database for a high-concurrency, multi-worker production deployment. PostgreSQL with appropriate transaction isolation and locking would be a candidate for that environment.

## Future Improvements

- PostgreSQL-based concurrent allocation
- Durable provider event processing
- Automated worker-crash recovery
- More realistic predictive simulation and agent-utilization metrics
- Provider latency and failure monitoring
- Allocation-focused load and stress testing
- Authentication, authorization, and audit logging
- Production telecom integration

## License

This project was developed as a technical assignment prototype for evaluation. Add an explicit open-source license only if you intend to distribute it under those terms.
