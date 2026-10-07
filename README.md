# Bulk Certificate Generator

A FastAPI-based backend service for generating certificates in bulk from a predefined certificate template. The system accepts multiple recipients in a single request, validates their data, generates individual PDF certificates, tracks generation progress, handles individual failures without stopping the complete job, and provides APIs to check job status and download generated certificates.

## Features

- Bulk certificate generation through a single API request
- FastAPI REST API
- SQLite relational database with SQLAlchemy ORM
- Input validation using Pydantic
- Predefined certificate template
- Individual PDF certificate generation
- Background job processing
- Job status and progress tracking
- Success and failure counts
- Individual certificate failure isolation
- Generated certificate download endpoint
- Automated API tests using pytest
- Swagger/OpenAPI documentation

## Tech Stack

- **Python 3**
- **FastAPI**
- **SQLAlchemy**
- **SQLite**
- **Pydantic**
- **ReportLab**
- **Pytest**
- **Uvicorn**

## Project Structure

```text
bulk_certificate_generator/
│
├── app/
│   ├── __init__.py
│   ├── certificate_generator.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── services.py
│   │
│   └── templates/
│
├── tests/
│   ├── conftest.py
│   └── test_api.py
│
├── generated/
│
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── sample_request.json
└── README.md
```

## Database Design

The application uses **SQLite as a relational database** with SQLAlchemy as the ORM.

There are two main tables:

### GenerationJob

Stores information about a bulk certificate generation request.

Important fields:

- `id`
- `event_name`
- `issuer_name`
- `total_count`
- `success_count`
- `failure_count`
- `status`
- `created_at`
- `updated_at`
- `error_message`

### Certificate

Stores information about each recipient certificate.

Important fields:

- `id`
- `job_id`
- `recipient_name`
- `recipient_email`
- `course_name`
- `certificate_status`
- `file_path`
- `error_message`
- `created_at`

The relationship is:

```text
GenerationJob
      │
      │ 1-to-many
      ▼
Certificate
```

Each certificate is associated with a generation job through the `job_id` foreign key.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/bulk-certificate-generator.git
cd bulk-certificate-generator
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

## API Endpoints

### 1. Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### 2. Create Bulk Generation Job

```http
POST /api/v1/jobs
```

This endpoint accepts multiple recipients in a single request.

Example request:

```json
{
  "event_name": "AI & Machine Learning Workshop 2026",
  "issuer_name": "Parul University",
  "recipients": [
    {
      "name": "Meet Darji",
      "email": "meet@example.com",
      "course_name": "Artificial Intelligence and Machine Learning"
    },
    {
      "name": "Rahul Patel",
      "email": "rahul@example.com",
      "course_name": "Python for Machine Learning"
    }
  ]
}
```

Example response:

```json
{
  "job_id": 1,
  "status": "pending",
  "total_count": 2
}
```

The endpoint returns `202 Accepted` because certificate generation is processed in the background.

### 3. Check Job Status

```http
GET /api/v1/jobs/{job_id}
```

Example response:

```json
{
  "job_id": 1,
  "event_name": "AI & Machine Learning Workshop 2026",
  "issuer_name": "Parul University",
  "status": "completed",
  "total_count": 2,
  "success_count": 2,
  "failure_count": 0,
  "progress_percent": 100.0,
  "certificates": []
}
```

The status can indicate:

```text
pending
processing
completed
completed_with_errors
failed
```

### 4. Download Certificate

```http
GET /api/v1/certificates/{certificate_id}/download
```

This endpoint returns the generated certificate as a PDF file.

## Certificate Generation Workflow

The application follows this workflow:

```text
Client
  │
  │ POST /api/v1/jobs
  ▼
FastAPI
  │
  ├── Validate request
  │
  ├── Create GenerationJob
  │
  ├── Create Certificate records
  │
  └── Start background processing
          │
          ▼
    Certificate Generator
          │
          ├── Generate Certificate 1
          ├── Generate Certificate 2
          ├── Generate Certificate 3
          └── ...
                  │
                  ▼
             PDF files
                  │
                  ▼
             Database status
```

## Failure Handling

Certificate generation is handled individually.

If one certificate fails:

```text
Recipient 1 → Success
Recipient 2 → Failed
Recipient 3 → Success
Recipient 4 → Success
```

The remaining certificates continue to generate.

The job is marked:

```text
completed_with_errors
```

The database stores the failure information for the affected certificate.

This prevents one invalid or failed certificate from stopping the complete bulk generation job.

## Input Validation

Recipient data is validated before processing.

Validation includes:

- Recipient name
- Email address
- Course name
- Required fields
- Recipient list size

For example, an invalid email:

```json
{
  "email": "not-an-email"
}
```

results in a validation error response:

```text
HTTP 422 Unprocessable Entity
```

## Testing

The project includes automated tests using pytest.

Run:

```bash
pytest -q
```

Current test coverage includes:

1. Creating a generation job
2. Input validation
3. Certificate generation
4. Job status and progress
5. Certificate PDF retrieval
6. Individual certificate failure isolation

Expected result:

```text
5 passed
```

## Design Decisions

### FastAPI

FastAPI was selected because it provides:

- Simple REST API development
- Automatic OpenAPI documentation
- Pydantic request validation
- Good support for background tasks
- Easy testing with FastAPI's `TestClient`

### SQLite

SQLite was selected as the relational database because it is lightweight and requires no separate database server for this assignment.

The application can later be migrated to PostgreSQL or another relational database with minimal changes because database access is handled through SQLAlchemy.

### Background Processing

Certificate generation is performed as a background task so that the API can immediately return a job ID instead of making the client wait for every PDF to be generated.

The client can then query:

```http
GET /api/v1/jobs/{job_id}
```

to monitor progress.

### Failure Isolation

Each certificate is generated inside its own error-handling block. Therefore, failure of one certificate does not terminate the remaining generation process.

## Sample Request File

A sample request is included in:

```text
sample_request.json
```

It can be used to test the bulk certificate generation endpoint.

## Docker

The project also includes:

```text
Dockerfile
docker-compose.yml
```

To build and run using Docker:

```bash
docker compose up --build
```

## Generated Files

Generated PDF certificates are stored in:

```text
generated/
```

The database stores the generated file path for each successfully generated certificate.

## API Documentation

After starting the application, interactive Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

ReDoc documentation is available at:

```text
http://127.0.0.1:8000/redoc
```

## Future Improvements

Possible production-level improvements include:

- Redis/Celery or another dedicated task queue for large workloads
- PostgreSQL for production deployment
- Cloud object storage for generated certificates
- Authentication and authorization
- Rate limiting
- Structured logging
- Job cancellation
- Certificate expiry and cleanup
- Email delivery of generated certificates
- Deployment using Docker and a cloud platform

## Author

**Meet Darji**

B.Tech Computer Science & Engineering — Artificial Intelligence / Machine Learning

GitHub: `https://github.com/YOUR_USERNAME`
