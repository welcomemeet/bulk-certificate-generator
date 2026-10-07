from app.services import process_job


def sample_payload():
    return {
        "event_name": "AI Workshop 2026",
        "issuer_name": "Tech Academy",
        "recipients": [
            {
                "name": "Alice Sharma",
                "email": "alice@example.com",
                "course_name": "Artificial Intelligence",
            },
            {
                "name": "Bob Patel",
                "email": "bob@example.com",
                "course_name": "Machine Learning",
            },
        ],
    }


def test_create_generation_job(client):
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(),
    )

    assert response.status_code == 202

    data = response.json()

    assert data["job_id"] > 0
    assert data["status"] == "pending"
    assert data["total_count"] == 2


def test_input_validation(client):
    payload = sample_payload()

    payload["recipients"][0]["email"] = "not-an-email"

    response = client.post(
        "/api/v1/jobs",
        json=payload,
    )

    assert response.status_code == 422


def test_certificate_generation_and_status(
    client,
    test_session_factory,
):
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(),
    )

    assert response.status_code == 202

    job_id = response.json()["job_id"]

    # Process the background job manually during testing.
    process_job(
        job_id,
        session_factory=test_session_factory,
    )

    response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["total_count"] == 2
    assert data["success_count"] == 2
    assert data["failure_count"] == 0
    assert data["progress_percent"] == 100.0

    for certificate in data["certificates"]:
        assert certificate["certificate_status"] == "completed"
        assert certificate["file_path"] is not None


def test_retrieve_generated_certificate(
    client,
    test_session_factory,
):
    response = client.post(
        "/api/v1/jobs",
        json=sample_payload(),
    )

    assert response.status_code == 202

    job_id = response.json()["job_id"]

    process_job(
        job_id,
        session_factory=test_session_factory,
    )

    response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"

    certificate_id = data["certificates"][0]["id"]

    download_response = client.get(
        f"/api/v1/certificates/{certificate_id}/download"
    )

    assert download_response.status_code == 200

    assert (
        download_response.headers["content-type"]
        == "application/pdf"
    )

    assert download_response.content.startswith(b"%PDF")


def test_individual_certificate_failure_isolated(
    client,
    monkeypatch,
    test_session_factory,
):
    payload = sample_payload()

    response = client.post(
        "/api/v1/jobs",
        json=payload,
    )

    assert response.status_code == 202

    job_id = response.json()["job_id"]

    import app.services as services

    original_generate_certificate = (
        services.generate_certificate
    )

    calls = {"count": 0}

    def fail_first_certificate(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            raise RuntimeError(
                "Simulated certificate generation failure"
            )

        return original_generate_certificate(
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        services,
        "generate_certificate",
        fail_first_certificate,
    )

    process_job(
        job_id,
        session_factory=test_session_factory,
    )

    response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed_with_errors"
    assert data["total_count"] == 2
    assert data["success_count"] == 1
    assert data["failure_count"] == 1
    assert data["progress_percent"] == 100.0

    certificates = data["certificates"]

    assert certificates[0]["certificate_status"] == "failed"

    assert (
        certificates[0]["error_message"]
        == "Simulated certificate generation failure"
    )

    assert (
        certificates[1]["certificate_status"]
        == "completed"
    )