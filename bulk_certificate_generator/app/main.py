from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Certificate, GenerationJob
from .schemas import (
    GenerationRequest,
    JobCreatedResponse,
    JobStatusResponse,
)
from .services import process_job


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
    description=(
        "Backend API for bulk certificate generation "
        "with job tracking and PDF certificate downloads."
    ),
)


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGIN = "https://bulk-certificate-generator-gold.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Explicit CORS preflight handler
# ============================================================

@app.options("/api/v1/jobs")
def options_jobs():
    return Response(
        content="OK",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "600",
        },
    )


# ============================================================
# Root
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# Create generation job
# ============================================================

@app.post(
    "/api/v1/jobs",
    status_code=202,
    response_model=JobCreatedResponse,
)
def create_job(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = GenerationJob(event_name=request.event_name, issuer_name=request.issuer_name, total_count=len(request.recipients), status="pending", success_count=0, failure_count=0)

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        process_job,
        job.id,
        request.recipients,
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "total_count": job.total_count,
    }


# ============================================================
# Get job status
# ============================================================

@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    certificates = db.query(Certificate).filter(Certificate.job_id == job_id).all()
    processed = job.success_count + job.failure_count
    progress_percent = round((processed / job.total_count) * 100, 2) if job.total_count else 0

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "issuer_name": job.issuer_name,
        "status": job.status.value if hasattr(job.status, "value") else job.status,
        "total_count": job.total_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "progress_percent": progress_percent,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "certificates": certificates,
    }

# ============================================================
# Download certificate
# ============================================================

@app.get("/api/v1/certificates/{certificate_id}/download")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
):
    certificate = (
        db.query(Certificate)
        .filter(Certificate.id == certificate_id)
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    file_path = certificate.file_path

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{certificate.recipient_name}.pdf",
    )




