# Bulk Certificate Generator

A FastAPI backend assignment implementation for generating certificates in bulk.

## Requirements covered

The assignment asks the backend to accept a certificate generation request, validate recipients, generate certificates from one predefined template, track status/progress, retrieve generated certificates, support bulk processing, isolate individual failures, include tests, and document setup/use. This project implements all of those requirements.

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- SQLite (relational database; easy local setup)
- ReportLab (PDF generation)
- Pytest
- FastAPI BackgroundTasks

## Project structure

```text
bulk_certificate_generator/
├── app/
│   ├── __init__.py
│   ├── certificate_generator.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   └── templates/
├── generated/
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Open:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

## Submit a bulk generation request

```http
POST /api/v1/jobs
Content-Type: application/json
```

Example:

```json
{
  "event_name": "AI Workshop 2026",
  "issuer_name": "Tech Academy",
  "recipients": [
    {
      "name": "Alice Sharma",
      "email": "alice@example.com",
      "course_name": "Artificial Intelligence"
    },
    {
      "name": "Bob Patel",
      "email": "bob@example.com",
      "course_name": "Machine Learning"
    }
  ]
}
```

The API returns HTTP 202:

```json
{
  "job_id": 1,
  "status": "pending",
  "total_count": 2
}
```

## Check job status

```http
GET /api/v1/jobs/1
```

Example response:

```json
{
  "job_id": 1,
  "event_name": "AI Workshop 2026",
  "issuer_name": "Tech Academy",
  "status": "completed",
  "total_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "progress_percent": 100.0,
  "certificates": [
    {
      "id": 1,
      "recipient_name": "Alice Sharma",
      "recipient_email": "alice@example.com",
      "course_name": "Artificial Intelligence",
      "certificate_status": "completed",
      "file_path": "...",
      "error_message": null
    }
  ],
  "error_message": null
}
```

## Download a generated certificate

```http
GET /api/v1/certificates/{certificate_id}/download
```

The endpoint returns the generated PDF.

## Validation

Pydantic validates:

- recipient name
- recipient email
- course name
- event name
- issuer name
- at least one recipient
- maximum 5000 recipients per request

Invalid input returns HTTP 422 and no job is created.

## Failure handling

Each recipient has its own database record. During processing, certificate generation happens independently for every recipient.

If one PDF fails:

- that certificate is marked `failed`
- its error is saved
- other certificates continue generating
- the job finishes as `completed_with_errors`

This prevents one bad certificate from stopping the entire bulk operation.

## Why background processing?

The API returns quickly with HTTP 202 instead of making the client wait for every PDF to finish.

FastAPI `BackgroundTasks` is sufficient for this assignment and keeps the project simple. For production workloads involving very large batches or multiple application instances, this service could be replaced by a durable queue such as Celery/RQ with Redis or RabbitMQ.

## Database design

### generation_jobs

Stores one record per bulk request:

- job ID
- event
- issuer
- total recipients
- successful count
- failed count
- status
- timestamps

### certificates

Stores one record per recipient:

- recipient information
- job ID
- generation status
- output file path
- error message

The relationship makes progress tracking and individual certificate retrieval straightforward.

## Run tests

```bash
pytest -q
```

The test suite covers:

1. Creating a generation job
2. Input validation
3. Certificate generation
4. Job status/progress
5. Individual certificate failure isolation
6. Retrieving generated certificates

## Interview explanation

### Request flow

```text
Client
  |
  | POST /api/v1/jobs
  v
FastAPI + Pydantic validation
  |
  v
Create Job + Certificate rows
  |
  v
Return 202 + job_id
  |
  v
Background processor
  |
  +--> Certificate 1 --> PDF
  +--> Certificate 2 --> PDF
  +--> Certificate N --> PDF
  |
  v
Update per-certificate status
  |
  v
Update aggregate job progress/status
```

### Important design decision

The system separates job-level state from certificate-level state. This is important because a bulk job can partially succeed.

For example:

```text
total = 100
success = 97
failed = 3
status = completed_with_errors
progress = 100%
```

That gives the client enough information to identify exactly what happened.

## Production improvements

If this were deployed at significant scale, I would add:

- PostgreSQL instead of SQLite
- Redis/RabbitMQ + Celery for durable background jobs
- object storage such as S3 for generated PDFs
- authentication and authorization
- rate limiting
- structured logging
- retry policy for transient failures
- database migrations with Alembic
- ZIP download for an entire completed batch
- cleanup/retention policy for old certificates
- Docker and CI/CD
