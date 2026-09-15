import json

from PIL import Image, ImageDraw

from pipeline.edition_pages import EditionPage, PAGE_WORLD, build_edition_pages
from pipeline.edition_preview import build_edition_preview
from pipeline.newspaper_renderer import (
    CONTENT_WIDTH,
    HEIGHT,
    Image as RendererImage,
    SECTION_GEOMETRY,
    WHITE,
    measure_news_block,
    plan_section_pages,
)


def _event(number, *, image_path=None):
    event = {
        "title": f"Measured story {number} follows a developing international event",
        "summary": "Officials provided additional details as the situation continued to develop.",
        "category": "WORLD",
        "sources": ["Test Source"],
    }
    if image_path:
        event["image_path"] = str(image_path)
    return event


def _draw():
    return ImageDraw.Draw(RendererImage.new("RGB", (1500, HEIGHT), WHITE))


def test_measure_news_block_uses_width_and_real_image_only(tmp_path):
    event = _event(1)
    narrow = measure_news_block(_draw(), event, 280)
    wide = measure_news_block(_draw(), event, CONTENT_WIDTH, lead=True)

    image_path = tmp_path / "actual-image.png"
    Image.new("RGB", (40, 40), "white").save(image_path)
    with_image = measure_news_block(
        _draw(), _event(2, image_path=image_path), CONTENT_WIDTH, lead=True
    )

    assert narrow > 0
    assert wide > 0
    assert with_image > wide


def test_page_plan_is_measured_and_never_overflows_content_area():
    page = EditionPage(
        page_number=2,
        page_type=PAGE_WORLD,
        title="WORLD",
        events=[_event(number) for number in range(1, 49)],
    )

    plans = plan_section_pages(page)
    blocks = [block for plan in plans for block in plan.blocks]

    assert len(plans) > 1
    assert [block.number for block in blocks] == list(range(1, 49))
    assert all(
        SECTION_GEOMETRY.content_top <= block.y
        and block.y + block.height <= SECTION_GEOMETRY.content_bottom
        for block in blocks
    )


def test_section_plan_uses_three_masonry_columns_and_a_two_column_lead():
    page = EditionPage(
        page_number=2,
        page_type=PAGE_WORLD,
        title="WORLD",
        events=[_event(number) for number in range(1, 13)],
    )

    plan = plan_section_pages(page)[0]
    lead, *compact = plan.blocks

    assert lead.lead
    assert len({block.x for block in compact}) == 3
    assert lead.width > compact[0].width


def test_mixed_page_has_a_short_global_news_heading():
    edition = {
        "top_story": _event("front"),
        "additional_events": [
            {**_event(1), "category": "WORLD"},
            {**_event(2), "category": "BUSINESS"},
        ],
    }

    page = build_edition_pages(edition)[1]

    assert page.page_type == "MIXED"
    assert page.title == "GLOBAL NEWS"


def test_preview_manifest_matches_the_actual_page_pngs(tmp_path):
    edition = {
        "edition_id": "test-preview",
        "edition_label": "EDITION 0001",
        "top_story": _event("front"),
        "additional_events": [_event(number) for number in range(1, 8)],
    }
    root = tmp_path / "preview"
    full = root / "full"
    full.mkdir(parents=True)
    stale = full / "page-99.png"
    stale.write_bytes(b"old preview")

    result = build_edition_preview(edition, root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    actual = sorted(str(path) for path in full.glob("page-*.png"))

    assert not stale.exists()
    assert manifest["full_edition"] == result["full_edition"]
    assert sorted(manifest["full_edition"]["files"]) == actual
    assert manifest["full_edition"]["page_count"] == len(actual)
