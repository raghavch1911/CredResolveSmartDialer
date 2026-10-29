# CredResolve SmartDialer

A safety-first outbound dialing prototype built with Python, FastAPI, SQLite, and Pytest.

## Features

- Progressive call allocation
- Rule-based predictive pacing
- Safety Controller
- Agent and borrower state management
- Two mock telecom providers
- Provider-event deduplication
- Out-of-order event handling
- Circuit breaker for provider failures
- Automated tests
- Basic simulation and HTTP load test

## Requirements

- Python 3.11+
- Windows, macOS, or Linux

## Setup on Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run the API

```cmd
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.

## Run tests

```cmd
python -m pytest tests -v
```

## Run the simulation

```cmd
python scripts\simulate.py
```

## Run the HTTP load test

Start the API first, then run:

```cmd
python scripts\load_test.py
```

## Main endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/agents` | Register an agent |
| GET | `/agents` | List agents |
| POST | `/borrowers` | Register a borrower |
| GET | `/borrowers` | List borrowers |
| POST | `/dial/allocate` | Allocate a progressive call |
| POST | `/dial/predictive` | Request predictive dialing |
| POST | `/calls/initiate` | Initiate a mock call |
| GET | `/calls` | List call records |
| POST | `/provider/events` | Process a provider event |
| GET | `/providers/health` | Inspect circuit-breaker state |

## Limitations

This is an educational prototype, not a production dialer. SQLite write serialization supports the local concurrency demonstration but is not a replacement for a production multi-worker architecture. Provider integrations are mocked, and provider timeouts require reconciliation. The simulation is illustrative rather than a validated telecom performance model.

See `docs/architecture.md` for the architecture and design decisions.