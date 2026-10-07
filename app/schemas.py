from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import CertificateStatus, JobStatus


class RecipientInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    course_name: str = Field(min_length=2, max_length=300)

    @field_validator("name", "course_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class GenerationRequest(BaseModel):
    event_name: str = Field(min_length=2, max_length=200)
    issuer_name: str = Field(min_length=2, max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1, max_length=5000)

    @field_validator("event_name", "issuer_name")
    @classmethod
    def strip_header_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class JobCreatedResponse(BaseModel):
    job_id: int
    status: JobStatus
    total_count: int


class CertificateResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_name: str
    recipient_email: EmailStr
    course_name: str
    certificate_status: CertificateStatus
    file_path: str | None
    error_message: str | None


class JobStatusResponse(BaseModel):
    job_id: int
    event_name: str
    issuer_name: str
    status: JobStatus
    total_count: int
    success_count: int
    failure_count: int
    progress_percent: float
    created_at: datetime
    updated_at: datetime
    certificates: list[CertificateResult]
    error_message: str | None = None
