"""
Metadata utilities for Open-EZ PDE artifacts.

Standardizes provenance data stored alongside STEP/STL/G-code outputs.
"""

from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from config import config


REQUIRED_FIELDS = (
    "artifact",
    "artifact_type",
    "generated_at",
    "revision",
    "config_hash",
    "contributor",
    "component",
    "provenance",
)


def _serialize_config() -> str:
    """Serialize the configuration deterministically for hashing."""
    config_dict = asdict(config)
    return json.dumps(config_dict, default=str, sort_keys=True)


def compute_config_hash() -> str:
    """Return a stable hash of the current configuration."""
    payload = _serialize_config().encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_git_revision() -> str:
    """Return the current git revision or a placeholder when unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        revision = result.stdout.strip()
        return revision or "unknown"
    except Exception:
        return "unknown"


@dataclass
class ArtifactMetadata:
    """Schema for artifact provenance tracked in output/ directories."""

    artifact: str
    artifact_type: str
    generated_at: str
    revision: str
    config_hash: str
    contributor: str
    component: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact": self.artifact,
            "artifact_type": self.artifact_type,
            "generated_at": self.generated_at,
            "revision": self.revision,
            "config_hash": self.config_hash,
            "contributor": self.contributor,
            "component": self.component,
            "provenance": self.provenance,
        }


def write_artifact_metadata(
    artifact_path: Path,
    component: Any,
    artifact_type: str,
    contributor: Optional[str] = None,
    revision: Optional[str] = None,
    config_hash: Optional[str] = None,
) -> Path:
    """Persist metadata next to an exported artifact.

    Args:
        artifact_path: Path to the artifact being exported.
        component: Component that produced the artifact (must expose get_metadata()).
        artifact_type: STEP, STL, DXF, GCODE, etc.
        contributor: Optional contributor identifier (env var PDE_CONTRIBUTOR used if unset).
        revision: Git revision to pin; detected automatically if omitted.
        config_hash: Hash of the active configuration; auto-computed if omitted.
    """

    contributor_name = contributor or os.environ.get("PDE_CONTRIBUTOR", "unknown")
    metadata = ArtifactMetadata(
        artifact=artifact_path.name,
        artifact_type=artifact_type,
        generated_at=datetime.utcnow().isoformat() + "Z",
        revision=revision or get_git_revision(),
        config_hash=config_hash or compute_config_hash(),
        contributor=contributor_name,
        component=component.get_metadata(),
        provenance={
            "toolchain": "Open-EZ PDE",
            "automated": True,
        },
    )

    metadata_path = artifact_path.parent / f"{artifact_path.stem}.metadata.json"
    metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2))
    return metadata_path
