"""Object storage for raw artifacts (S3 or local DATA_DIR fallback)."""

from app.integrations.s3.storage import ArtifactStorage, get_artifact_storage

__all__ = ["ArtifactStorage", "get_artifact_storage"]
