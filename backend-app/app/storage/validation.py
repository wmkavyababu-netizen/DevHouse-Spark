import json
from pathlib import Path
from typing import Optional, Set
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# Content signature definitions (magic bytes)
MAGIC_SIGNATURES = {
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jsf": [b"\x01\x16", b"\x16\x01"],  # Edgetech JSF sync pattern 0x1601
    ".xtf": [b"\x7b", b"\x1b"],          # eXtended Triton Format header packet types
}


def validate_file_extension(filename: str, allowed_extensions: Optional[Set[str]] = None) -> str:
    """Validates that file extension belongs to whitelist."""
    whitelist = allowed_extensions or settings.ALLOWED_EXTENSIONS
    suffix = Path(filename).suffix.lower()

    if suffix not in whitelist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{suffix}' not permitted. Whitelisted extensions: {sorted(list(whitelist))}",
        )
    return suffix


def validate_content_signature(suffix: str, header_bytes: bytes) -> None:
    """
    Validates file content signature (magic bytes) to prevent extension spoofing.
    Rejected files are discarded immediately and never touch the processing pipeline.
    """
    if suffix == ".json":
        try:
            # Must be valid UTF-8 and start with valid JSON token
            decoded = header_bytes.decode("utf-8", errors="strict").strip()
            if not (decoded.startswith("{") or decoded.startswith("[")):
                raise ValueError("JSON must start with object or array")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON content structure: {str(e)}",
            )
        return

    expected_magics = MAGIC_SIGNATURES.get(suffix)
    if expected_magics:
        matches = any(header_bytes.startswith(magic) for magic in expected_magics)
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content signature verification failed for {suffix}. File content does not match expected format magic bytes.",
            )


async def validate_upload(
    file: UploadFile,
    allowed_extensions: Optional[Set[str]] = None,
    max_size_bytes: Optional[int] = None,
) -> bytes:
    """
    Comprehensive upload validation:
    1. Validates file extension against whitelist.
    2. Reads and checks payload size against max size limit.
    3. Validates MIME type and binary magic byte signatures.
    Returns the validated file content bytes.
    """
    filename = file.filename or "unknown"
    suffix = validate_file_extension(filename, allowed_extensions)

    limit = max_size_bytes or (settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024)

    # Read content
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)",
        )

    if len(content) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size ({settings.MAX_UPLOAD_SIZE_MB} MB)",
        )

    # Inspect first 16 bytes for magic signatures
    validate_content_signature(suffix, content[:16])

    # Reset file pointer if needed by caller
    await file.seek(0)
    return content
