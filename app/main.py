
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
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


# ---------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------
# Allows the React + Vite frontend running on port 5173
# to communicate with the FastAPI backend running on port 8000.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://bulk-certificate-generator-gold.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# CREATE BULK CERTIFICATE GENERATION JOB
# ---------------------------------------------------------

@app.post(
    "/api/v1/jobs",
    response_model=JobCreatedResponse,
    status_code=202,
)
def create_generation_job(
    payload: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a bulk certificate generation job.

    The request contains:
    - Event name
    - Issuer name
    - Multiple recipients

    A job is created immediately and certificate generation
    is processed in the background.
    """

    # Create generation job
    job = GenerationJob(
        event_name=payload.event_name,
        issuer_name=payload.issuer_name,
        total_count=len(payload.recipients),
    )

    db.add(job)
    db.flush()

    # Create certificate records for each recipient
    for recipient in payload.recipients:
        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            course_name=recipient.course_name,
        )

        db.add(certificate)

    db.commit()
    db.refresh(job)

    # Start certificate generation in the background
    background_tasks.add_task(
        process_job,
        job.id,
    )

    return JobCreatedResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
    )


# ---------------------------------------------------------
# GET JOB STATUS / PROGRESS
# ---------------------------------------------------------

@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=JobStatusResponse,
)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Return the current status and progress of a generation job.
    """

    job = db.get(
        GenerationJob,
        job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Generation job not found",
        )

    # Calculate progress
    if job.total_count > 0:
        completed_count = (
            job.success_count
            + job.failure_count
        )

        progress = (
            completed_count
            / job.total_count
        ) * 100

    else:
        progress = 100

    return JobStatusResponse(
        job_id=job.id,
        event_name=job.event_name,
        issuer_name=job.issuer_name,
        status=job.status,
        total_count=job.total_count,
        success_count=job.success_count,
        failure_count=job.failure_count,
        progress_percent=round(
            progress,
            2,
        ),
        created_at=job.created_at,
        updated_at=job.updated_at,
        certificates=job.certificates,
        error_message=job.error_message,
    )


# ---------------------------------------------------------
# DOWNLOAD GENERATED CERTIFICATE
# ---------------------------------------------------------

@app.get(
    "/api/v1/certificates/{certificate_id}/download"
)
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a successfully generated certificate as a PDF.
    """

    certificate = db.get(
        Certificate,
        certificate_id,
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    # Certificate must be successfully generated
    if (
        certificate.certificate_status.value
        != "completed"
        or not certificate.file_path
    ):
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available for download",
        )

    # Check whether the PDF file exists
    import os

    if not os.path.isfile(
        certificate.file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Generated file not found",
        )

    return FileResponse(
        certificate.file_path,
        media_type="application/pdf",
        filename=os.path.basename(
            certificate.file_path
        ),
    )
