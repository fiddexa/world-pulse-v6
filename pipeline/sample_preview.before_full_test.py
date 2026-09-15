from __future__ import annotations

from pathlib import Path

from pipeline.edition_preview import build_edition_preview


OUTPUT = Path("data/previews/sample-edition-0001")


def event(
    title: str,
    summary: str,
    why_it_matters: str,
    category: str,
) -> dict:
    return {
        "title": title,
        "summary": summary,
        "why_it_matters": why_it_matters,
        "category": category,
        "sources": [
            "Sample Editorial Source",
        ],
    }


def main() -> None:

    edition = {
        "edition_id": "sample-edition-0001",
        "edition_year": 2026,
        "edition_number": 1,
        "edition_label": "EDITION 0001",
        "publication_date": "02 September 2026",

        "top_story": event(
            "World leaders meet as major geopolitical tensions reshape global priorities",
            (
                "Governments are responding to a rapidly changing international "
                "environment as diplomacy, security and economic interests become "
                "increasingly interconnected."
            ),
            (
                "The decisions made during this period could influence diplomatic "
                "relations, markets and international security well beyond the "
                "immediate news cycle."
            ),
            "WORLD",
        ),

        "main_stories": [
            event(
                "Global markets watch central banks and new economic signals",
                (
                    "Investors are assessing new economic data while markets "
                    "continue to react to changing expectations around monetary "
                    "policy and growth."
                ),
                (
                    "Interest-rate expectations can affect currencies, investment "
                    "flows and the cost of capital across major economies."
                ),
                "ECONOMY",
            ),
            event(
                "Technology companies accelerate investment in artificial intelligence",
                (
                    "Major technology companies continue expanding artificial "
                    "intelligence infrastructure, products and research programs."
                ),
                (
                    "The pace of investment is shaping competition across technology "
                    "and could influence productivity and future digital services."
                ),
                "TECHNOLOGY",
            ),
            event(
                "Energy markets remain focused on supply, demand and transport routes",
                (
                    "Energy traders are watching production levels, consumption "
                    "patterns and developments affecting major transportation routes."
                ),
                (
                    "Energy prices influence inflation, industrial costs and the "
                    "economic outlook for both producers and consumers."
                ),
                "BUSINESS",
            ),
        ],

        "additional_events": [
            event(
                "Diplomats intensify talks on major international priorities",
                (
                    "Officials are holding a new round of consultations as governments "
                    "seek practical areas for cooperation and risk reduction."
                ),
                (
                    "Diplomatic engagement can reduce uncertainty and create channels "
                    "for resolving wider international disputes."
                ),
                "WORLD",
            ),
            event(
                "Businesses prepare for a more closely connected global economy",
                (
                    "Companies are adjusting supply chains and investment plans as "
                    "international trade conditions continue to evolve."
                ),
                (
                    "Changes in global trade can affect prices, production decisions "
                    "and opportunities for businesses in multiple regions."
                ),
                "BUSINESS",
            ),
        ],

        "briefs": [
            event(
                "Scientists report new progress in climate research",
                "Researchers publish new findings that improve understanding of long-term climate patterns.",
                "Better scientific data can improve planning and policy decisions.",
                "SCIENCE",
            ),
            event(
                "Health authorities monitor emerging public-health developments",
                "Health agencies continue tracking developments and coordinating international responses.",
                "Early information can help governments and communities prepare.",
                "HEALTH",
            ),
            event(
                "International sport enters another major competition phase",
                "Teams and athletes prepare for a new series of high-profile international events.",
                "Major sporting events have significant cultural and economic impact.",
                "SPORTS",
            ),
            event(
                "Cities expand investment in digital public services",
                "Governments are testing new digital tools designed to improve access to public services.",
                "Digital infrastructure is becoming increasingly important to everyday life.",
                "WORLD",
            ),
        ],
    }

    result = build_edition_preview(
        edition,
        OUTPUT,
    )

    print("PREVIEW CREATED")
    print()
    print(f"Edition: {result['edition_label']}")
    print(f"Status:  {result['approval_status']}")
    print()
    print(f"Preview: {result['preview_root']}")
    print(f"Manifest: {result['manifest_path']}")
    print()
    print("FULL EDITION:")

    for path in result["full_edition"]["files"]:
        print(f"  {path}")

    print()
    print("MOBILE EDITION:")
    print(f"  {result['mobile_edition']['file']}")
    print()
    print("PUBLISH: NOT EXECUTED")


if __name__ == "__main__":
    main()
