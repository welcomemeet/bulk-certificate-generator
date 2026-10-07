from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
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


# ---------------------------------------------------------
# Create database tables
# ---------------------------------------------------------
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------
app = FastAPI(
    title="Bulk Certificate Generator",
    version="1.0.0",
    description="Backend API for bulk certificate generation.",
)


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# Create Certificate Generation Job
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
    - List of recipients

    The certificates are generated in the background.
    """

    # Create generation job
    job = GenerationJob(
        event_name=payload.event_name,
        issuer_name=payload.issuer_name,
        total_count=len(payload.recipients),
    )

    db.add(job)

    # Flush so that job.id is generated
    db.flush()

    # Create certificate records for every recipient
    for recipient in payload.recipients:

        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            course_name=recipient.course_name,
        )

        db.add(certificate)

    # Save everything to database
    db.commit()

    # Refresh job from database
    db.refresh(job)

    # Start certificate generation in background
    background_tasks.add_task(
        process_job,
        job.id,
    )

    # Return job information
    return JobCreatedResponse(
        job_id=job.id,
        status=job.status,
        total_count=job.total_count,
    )


# ---------------------------------------------------------
# Get Job Status
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
    Get the current status and progress of a certificate job.
    """

    # Find job
    job = db.get(
        GenerationJob,
        job_id,
    )

    # Job doesn't exist
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

    # Return job status
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
# Download Generated Certificate
# ---------------------------------------------------------
@app.get(
    "/api/v1/certificates/{certificate_id}/download"
)
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a generated certificate PDF.
    """

    # Find certificate
    certificate = db.get(
        Certificate,
        certificate_id,
    )

    # Certificate doesn't exist
    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found",
        )

    # Certificate is not ready
    if (
        certificate.certificate_status.value
        != "completed"
        or not certificate.file_path
    ):
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available for download",
        )

    # Check file
    import os

    if not os.path.isfile(
        certificate.file_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Generated file not found",
        )

    # Return PDF file
    return FileResponse(
        certificate.file_path,
        media_type="application/pdf",
        filename=os.path.basename(
            certificate.file_path
        ),
    )