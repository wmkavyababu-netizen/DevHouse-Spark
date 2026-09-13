import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.sonar import StorageArtifact


class StorageService:
    """
    Manages physical storage of raw SSS binaries, frame tiles, model weights, and reports.
    Enforces strict folder hierarchies and generates signed, temporary download tokens.
    Never returns raw filesystem paths to API clients.
    """

    def __init__(self, root_path: Optional[str] = None):
        self.root = Path(root_path or settings.STORAGE_ROOT).resolve()

    def get_survey_raw_path(self, survey_id: UUID, filename: str) -> Path:
        dest_dir = self.root / "surveys" / str(survey_id) / "raw"
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / filename

    def get_survey_extracted_path(self, survey_id: UUID, filename: str) -> Path:
        dest_dir = self.root / "surveys" / str(survey_id) / "extracted"
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / filename

    def get_survey_processed_path(self, survey_id: UUID, processing_job_id: UUID, filename: str) -> Path:
        dest_dir = self.root / "surveys" / str(survey_id) / "processed" / str(processing_job_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / filename

    def get_model_path(self, version: str, filename: str) -> Path:
        dest_dir = self.root / "models" / version
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / filename

    def get_report_path(self, filename: str) -> Path:
        dest_dir = self.root / "reports"
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir / filename

    async def save_artifact(
        self,
        db: AsyncSession,
        dest_path: Path,
        content: bytes,
        artifact_type: str,
        filename: str,
        mime_type: str,
        metadata_json: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> StorageArtifact:
        """
        Writes content bytes to dest_path, computes SHA-256 and size,
        and registers a row in the storage_artifacts database table.
        """
        # Ensure parent directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with open(dest_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        checksum = hashlib.sha256(content).hexdigest()

        # Compute relative storage URI
        try:
            rel_path = dest_path.relative_to(self.root).as_posix()
        except ValueError:
            rel_path = dest_path.as_posix()

        storage_uri = f"storage://{rel_path}"

        artifact = StorageArtifact(
            artifact_type=artifact_type,
            storage_uri=storage_uri,
            filename=filename,
            mime_type=mime_type,
            file_size_bytes=file_size,
            checksum_sha256=checksum,
            metadata_json=metadata_json or metadata or {},
        )
        db.add(artifact)
        await db.commit()
        await db.refresh(artifact)
        return artifact

    def resolve_physical_path(self, storage_uri: str) -> Path:
        """
        Resolves a storage:// URI to a secure, verified physical path under STORAGE_ROOT.
        Guards against directory traversal.
        """
        if not storage_uri.startswith("storage://"):
            raise ValueError(f"Invalid storage URI scheme: {storage_uri}")

        rel_part = storage_uri[len("storage://"):]
        resolved_path = (self.root / rel_part).resolve()

        if not str(resolved_path).startswith(str(self.root)):
            raise PermissionError("Access violation: Directory traversal attempt detected")

        if not resolved_path.exists():
            raise FileNotFoundError(f"Storage artifact file not found on disk: {storage_uri}")

        return resolved_path

    def generate_signed_download_token(
        self, artifact_id: UUID, user_id: UUID, expires_in: Optional[int] = None
    ) -> str:
        """
        Generates an HMAC-signed download reference token.
        FastAPI clients use this token to retrieve artifacts without ever seeing disk paths.
        """
        ttl = expires_in or settings.DOWNLOAD_TOKEN_EXPIRE_SECONDS
        payload = {
            "aid": str(artifact_id),
            "uid": str(user_id),
            "exp": int(time.time()) + ttl,
        }
        json_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(json_bytes).decode("utf-8").rstrip("=")

        sig = hmac.new(
            settings.DOWNLOAD_TOKEN_SECRET.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return f"{b64_payload}.{sig}"

    def verify_download_token(self, token: str) -> Tuple[UUID, UUID]:
        """
        Verifies signed token integrity and expiry. Returns (artifact_id, user_id).
        """
        parts = token.split(".")
        if len(parts) != 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed download token")

        b64_payload, signature = parts

        expected_sig = hmac.new(
            settings.DOWNLOAD_TOKEN_SECRET.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid download token signature")

        try:
            # Re-pad base64
            padded = b64_payload + "=" * (-len(b64_payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token encoding")

        if time.time() > data.get("exp", 0):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Download token has expired")

        try:
            return UUID(data["aid"]), UUID(data["uid"])
        except (KeyError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token identifiers")


storage_service = StorageService()
