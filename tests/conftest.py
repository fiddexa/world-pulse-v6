from __future__ import annotations

import json
from pathlib import Path

from pipeline.edition_preview import approve_edition_preview


def create_approved_manifest(tmp_path: Path, edition_id: str) -> Path:
    preview_root = tmp_path / "previews" / edition_id
    preview_root.mkdir(parents=True, exist_ok=True)

    manifest_path = preview_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "edition_id": edition_id,
                "approval_status": "PENDING",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    approve_edition_preview(preview_root)
    return manifest_path
