from sqlalchemy.orm import Session

from .certificate_generator import (
    generate_certificate,
    safe_filename,
)
from .config import GENERATED_DIR
from .database import SessionLocal
from .models import (
    Certificate,
    CertificateStatus,
    GenerationJob,
    JobStatus,
)


def process_job(
    job_id: int,
    session_factory=SessionLocal,
) -> None:
    """
    Process all certificates belonging to a generation job.

    Each certificate is processed independently so that
    one failure does not stop the remaining certificates.
    """

    db: Session = session_factory()

    try:
        # Find the job
        job = db.get(
            GenerationJob,
            job_id,
        )

        if not job:
            return

        # Mark job as processing
        job.status = JobStatus.PROCESSING
        db.commit()

        # Get all certificates belonging to this job
        certificates = (
            db.query(Certificate)
            .filter(
                Certificate.job_id == job_id
            )
            .order_by(Certificate.id)
            .all()
        )

        # Process every certificate independently
        for certificate in certificates:

            try:
                # Generate unique filename
                filename = (
                    f"job_{job.id}_certificate_"
                    f"{certificate.id}_"
                    f"{safe_filename(certificate.recipient_name)}"
                    f".pdf"
                )

                output_path = (
                    GENERATED_DIR / filename
                )

                # Generate PDF
                generate_certificate(
                    output_path=output_path,
                    recipient_name=(
                        certificate.recipient_name
                    ),
                    course_name=(
                        certificate.course_name
                    ),
                    event_name=job.event_name,
                    issuer_name=job.issuer_name,
                )

                # Mark certificate successful
                certificate.file_path = str(
                    output_path
                )

                certificate.certificate_status = (
                    CertificateStatus.COMPLETED
                )

                certificate.error_message = None

                job.success_count += 1

            except Exception as exc:

                # Mark only this certificate as failed
                certificate.certificate_status = (
                    CertificateStatus.FAILED
                )

                certificate.error_message = str(
                    exc
                )

                job.failure_count += 1

            # Save after every certificate
            db.commit()

        # Determine final job status
        if job.failure_count > 0:
            job.status = (
                JobStatus.COMPLETED_WITH_ERRORS
            )
        else:
            job.status = JobStatus.COMPLETED

        db.commit()

    except Exception as exc:

        # Handle unexpected job-level errors
        job = db.get(
            GenerationJob,
            job_id,
        )

        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            db.commit()

    finally:
        db.close()