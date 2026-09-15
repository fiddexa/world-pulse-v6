from __future__ import annotations

import json

from pipeline.edition_approval import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
    get_edition_approval_status,
)
from pipeline.edition_preview import (
    approve_edition_preview,
    build_edition_preview,
    reject_edition_preview,
)


def test_preview_starts_pending(tmp_path):
    edition = {
        "edition_id": "approval-test-0001",
        "edition_year": 2026,
        "edition_number": 1,
        "edition_label": "EDITION 0001",
        "top_story": {
            "title": "Test story",
            "summary": "Test summary",
            "category": "WORLD",
            "sources": ["Test Source"],
        },
        "main_stories": [],
        "briefs": [],
    }

    result = build_edition_preview(
        edition,
        tmp_path / "preview",
    )

    assert result["approval_status"] == APPROVAL_PENDING
    assert result["manifest_path"]

    manifest = json.loads(
        (tmp_path / "preview" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["edition_id"] == edition["edition_id"]
    assert manifest["approval_status"] == APPROVAL_PENDING


def test_preview_can_be_approved(tmp_path):
    edition = {
        "edition_id": "approval-test-0002",
        "edition_year": 2026,
        "edition_number": 2,
        "edition_label": "EDITION 0002",
        "top_story": {
            "title": "Test story",
            "summary": "Test summary",
            "category": "WORLD",
            "sources": ["Test Source"],
        },
        "main_stories": [],
        "briefs": [],
    }

    root = tmp_path / "preview"

    build_edition_preview(
        edition,
        root,
    )

    manifest = approve_edition_preview(root)

    assert manifest["edition_id"] == edition["edition_id"]
    assert manifest["approval_status"] == APPROVAL_APPROVED

    assert (
        get_edition_approval_status(
            edition["edition_id"],
            root / "manifest.json",
        )
        == APPROVAL_APPROVED
    )


def test_preview_can_be_rejected(tmp_path):
    edition = {
        "edition_id": "approval-test-0003",
        "edition_year": 2026,
        "edition_number": 3,
        "edition_label": "EDITION 0003",
        "top_story": {
            "title": "Test story",
            "summary": "Test summary",
            "category": "WORLD",
            "sources": ["Test Source"],
        },
        "main_stories": [],
        "briefs": [],
    }

    root = tmp_path / "preview"

    build_edition_preview(
        edition,
        root,
    )

    manifest = reject_edition_preview(root)

    assert manifest["approval_status"] == APPROVAL_REJECTED

    assert (
        get_edition_approval_status(
            edition["edition_id"],
            root / "manifest.json",
        )
        == APPROVAL_REJECTED
    )


def test_missing_manifest_is_not_approved(tmp_path):
    assert (
        get_edition_approval_status(
            "approval-test-missing",
            tmp_path / "manifest.json",
        )
        is None
    )


def test_wrong_edition_id_is_not_approved(tmp_path):
    manifest_path = tmp_path / "manifest.json"

    manifest_path.write_text(
        json.dumps(
            {
                "edition_id": "different-edition",
                "approval_status": APPROVAL_APPROVED,
            }
        ),
        encoding="utf-8",
    )

    assert (
        get_edition_approval_status(
            "expected-edition",
            manifest_path,
        )
        is None
    )
