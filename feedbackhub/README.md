# FeedbackHub

A web-enabled customer feedback **data collection** system: a REST API plus a small web form.
Submissions are validated, stored in SQLite, tagged with a sentiment label, and summarised
through an analytics endpoint so decisions can be based on data.

## Features
- REST API with input validation, pagination, filtering and consistent JSON errors
- Web form at `/` that posts to the API and shows live summary stats
- Lexicon-based sentiment analysis with negation handling (`app/sentiment.py`)
- Analytics summary: totals, average rating, breakdown by sentiment, channel and rating
- CSV export with protection against spreadsheet formula injection
- Parameterised SQL everywhere (no SQL injection), XSS-safe UI rendering
- API specification in `docs/openapi.yaml`
- Unit and API tests (`unittest`), Docker image, GitHub Actions CI

## Tech stack
Python 3, Flask, SQLite, unittest, Docker, GitHub Actions

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py                    # http://127.0.0.1:5000
```

## Run tests
```bash
python -m unittest discover -v
```

## Run with Docker
```bash
docker build -t feedbackhub .
docker run -p 8000:8000 -v feedbackhub-data:/data feedbackhub
```

## API overview
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/feedback` | Submit feedback (201 + Location header) |
| GET | `/api/feedback?page=&per_page=&channel=&sentiment=` | Paginated list |
| GET | `/api/feedback/{id}` | Fetch one item |
| DELETE | `/api/feedback/{id}` | Delete one item |
| GET | `/api/feedback/export` | CSV export (same filters) |
| GET | `/api/analytics/summary` | Aggregated statistics |

Example:
```bash
curl -X POST http://127.0.0.1:5000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha","email":"asha@example.com","channel":"mobile","rating":5,"message":"Great app, really easy to use"}'
```

## Project layout
```
app/            application code (factory, routes, db, validators, sentiment, template)
tests/          unit and API tests
docs/           OpenAPI specification
.github/        CI workflow
```

## Possible next steps
Authentication for admin endpoints, PostgreSQL, rate limiting, ML-based sentiment model.
