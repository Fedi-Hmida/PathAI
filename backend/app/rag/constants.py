from pathlib import Path
from typing import Literal

DEFAULT_RESOURCE_TOP_K = 3
MAX_RESOURCE_TOP_K = 10
MIN_RESOURCE_MATCH_SCORE = 0.08
FOUNDATIONAL_FALLBACK_SCORE = 0.18

RetrievalSource = Literal["catalog_match", "token_overlap", "foundational_fallback"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def canonical_rag_root() -> Path:
    return project_root() / "rag"


def resource_schema_path() -> Path:
    return canonical_rag_root() / "schemas" / "resource.schema.json"


def resource_staging_path() -> Path:
    return canonical_rag_root() / "resources" / "staging"


def resource_approved_path() -> Path:
    return canonical_rag_root() / "resources" / "approved"
