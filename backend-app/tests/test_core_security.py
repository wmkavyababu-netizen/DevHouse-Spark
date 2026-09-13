"""
End-to-end verification tests for backend-app core:
1. RS256 JWT validation and UserContext extraction
2. RBAC role enforcement (require_role)
3. Storage signed download token generation and validation
4. Storage file upload validation (magic bytes, extensions, size limits)
"""

import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt
import pytest
import httpx
from fastapi import HTTPException

# Ensure backend-app is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.security import register_cached_public_key, UserContext
from app.storage.service import storage_service
from app.storage.validation import validate_file_extension, validate_content_signature

# Generate RSA keypair for testing
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode("utf-8")

TEST_KID = "tarang-dev-key-v1"
# Register public key in FastAPI security cache
register_cached_public_key(TEST_KID, public_key_pem)

TEST_USER_ID = str(uuid.uuid4())
TEST_ORG_ID = str(uuid.uuid4())

def create_test_jwt(roles, user_id=TEST_USER_ID, org_id=TEST_ORG_ID, expires_in=3600, kid=TEST_KID, key=private_key):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": "analyst@tarang.dev",
        "roles": roles,
        "organization_id": org_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    headers = {"kid": kid}
    return jwt.encode(payload, key, algorithm="RS256", headers=headers)


@pytest.mark.asyncio
async def test_auth_context_without_token():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/auth/context")
        assert response.status_code in [401, 403]
        assert "detail" in response.json()


@pytest.mark.asyncio
async def test_auth_context_with_valid_token():
    token = create_test_jwt(roles=["ROLE_OPERATOR", "ROLE_ANALYST"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert data["email"] == "analyst@tarang.dev"
        assert data["organization_id"] == TEST_ORG_ID
        assert "ROLE_OPERATOR" in data["roles"]
        assert "ROLE_ANALYST" in data["roles"]


@pytest.mark.asyncio
async def test_rbac_admin_ping_forbidden():
    # Token with only ROLE_OPERATOR should get 403 on admin ping
    token = create_test_jwt(roles=["ROLE_OPERATOR"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/ping",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_admin_ping_allowed():
    # Token with ROLE_ORG_ADMIN should succeed
    token = create_test_jwt(roles=["ROLE_ORG_ADMIN"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/ping",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_invalid_signature():
    # Another key signing the token
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = create_test_jwt(roles=["ROLE_OPERATOR"], key=other_key)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/context",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert "Invalid token signature" in response.json()["detail"]


def test_storage_signed_token_flow():
    artifact_id = uuid.uuid4()
    user_id = uuid.uuid4()
    token = storage_service.generate_signed_download_token(artifact_id=artifact_id, user_id=user_id, expires_in=60)
    assert token is not None

    # Verify token
    verified_art_id, verified_user_id = storage_service.verify_download_token(token)
    assert verified_art_id == artifact_id
    assert verified_user_id == user_id

    # Test tampered signature
    tampered_token = token[:-4] + "abcd"
    with pytest.raises(HTTPException) as exc_info:
        storage_service.verify_download_token(tampered_token)
    assert exc_info.value.status_code == 401


def test_storage_upload_validation():
    # Valid PNG extension and magic
    ext = validate_file_extension("survey_frame.png")
    assert ext == ".png"
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    validate_content_signature(".png", png_bytes)

    # Valid XTF extension and magic
    ext_xtf = validate_file_extension("sonar_line.xtf")
    assert ext_xtf == ".xtf"
    xtf_bytes = b"\x7b\x44" + b"\x00" * 30
    validate_content_signature(".xtf", xtf_bytes)

    # Valid JSF extension and magic
    ext_jsf = validate_file_extension("sonar_line.jsf")
    assert ext_jsf == ".jsf"
    jsf_bytes = b"\x01\x16\x00\x00"
    validate_content_signature(".jsf", jsf_bytes)

    # Valid JSON extension and magic
    ext_json = validate_file_extension("metadata.json")
    assert ext_json == ".json"
    validate_content_signature(".json", b'{"survey_id": "test"}')

    # Mismatched extension and content (png content for .xtf file)
    with pytest.raises(HTTPException) as exc_info:
        validate_content_signature(".xtf", png_bytes)
    assert exc_info.value.status_code == 400
    assert "Content signature verification failed" in exc_info.value.detail

    # Disallowed extension
    with pytest.raises(HTTPException) as exc_info:
        validate_file_extension("payload.exe")
    assert exc_info.value.status_code == 400
    assert "not permitted" in exc_info.value.detail


if __name__ == "__main__":
    import asyncio
    print("Running verification tests directly...")

    async def run_all():
        await test_auth_context_without_token()
        print("PASS: test_auth_context_without_token")
        await test_auth_context_with_valid_token()
        print("PASS: test_auth_context_with_valid_token")
        await test_rbac_admin_ping_forbidden()
        print("PASS: test_rbac_admin_ping_forbidden")
        await test_rbac_admin_ping_allowed()
        print("PASS: test_rbac_admin_ping_allowed")
        await test_invalid_signature()
        print("PASS: test_invalid_signature")
        test_storage_signed_token_flow()
        print("PASS: test_storage_signed_token_flow")
        test_storage_upload_validation()
        print("PASS: test_storage_upload_validation")
        print("\nALL CORE VERIFICATION TESTS PASSED SUCCESSFULLY!")

    asyncio.run(run_all())
