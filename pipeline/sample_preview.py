from __future__ import annotations

from pathlib import Path
import sys

# Allow the documented `python pipeline/sample_preview.py` invocation from the
# repository root as well as `python -m pipeline.sample_preview`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.edition_preview import build_edition_preview


OUTPUT = Path("data/previews/sample-edition-0001")


def event(
    title: str,
    summary: str,
    category: str,
) -> dict:
    return {
        "title": title,
        "summary": summary,
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

        # ============================================================
        # FRONT PAGE
        # ============================================================

        "top_story": event(
            "World leaders meet as major geopolitical tensions reshape global priorities",
            (
                "Governments are responding to a rapidly changing international "
                "environment as diplomacy, security and economic interests become "
                "increasingly interconnected."
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
                "ECONOMY",
            ),

            event(
                "Technology companies accelerate investment in artificial intelligence",
                (
                    "Major technology companies continue expanding artificial "
                    "intelligence infrastructure, products and research programs."
                ),
                "TECHNOLOGY",
            ),

            event(
                "Energy markets remain focused on supply, demand and transport routes",
                (
                    "Energy traders are watching production levels, consumption "
                    "patterns and developments affecting major transportation routes."
                ),
                "BUSINESS",
            ),
        ],

        # ============================================================
        # ADDITIONAL FRONT-PAGE MATERIAL
        # ============================================================

        "additional_events": [

            event(
                "Diplomats intensify talks on major international priorities",
                (
                    "Officials are holding a new round of consultations as governments "
                    "seek practical areas for cooperation and risk reduction."
                ),
                "WORLD",
            ),

            event(
                "Businesses prepare for a more closely connected global economy",
                (
                    "Companies are adjusting supply chains and investment plans as "
                    "international trade conditions continue to evolve."
                ),
                "BUSINESS",
            ),

            event(
                "Scientists report new progress in climate research",
                (
                    "Researchers publish new findings that improve understanding "
                    "of long-term climate patterns."
                ),
                "SCIENCE",
            ),

            event(
                "Health authorities monitor emerging public-health developments",
                (
                    "Health agencies continue tracking developments and coordinating "
                    "international responses."
                ),
                "HEALTH",
            ),

            event(
                "International sport enters another major competition phase",
                (
                    "Teams and athletes prepare for a new series of high-profile "
                    "international events."
                ),
                "SPORTS",
            ),

            event(
                "Cities expand investment in digital public services",
                (
                    "Governments are testing new digital tools designed to improve "
                    "access to public services."
                ),
                "WORLD",
            ),

            event(
                "Global trade routes adapt to changing transportation conditions",
                (
                    "Shipping companies and exporters are reviewing routes, schedules "
                    "and logistics plans as international trade patterns change."
                ),
                "BUSINESS",
            ),

            event(
                "Manufacturers increase focus on resilient supply networks",
                (
                    "Industrial companies are reviewing suppliers and production "
                    "strategies to reduce disruption risks."
                ),
                "ECONOMY",
            ),

            event(
                "New research expands understanding of ocean conditions",
                (
                    "Researchers are collecting additional observations to improve "
                    "scientific understanding of changing marine environments."
                ),
                "SCIENCE",
            ),

            event(
                "Governments strengthen cooperation on digital security",
                (
                    "Officials are discussing measures designed to improve resilience "
                    "across increasingly connected digital infrastructure."
                ),
                "TECHNOLOGY",
            ),

            event(
                "Hospitals expand use of digital tools in patient services",
                (
                    "Healthcare organizations are introducing additional digital "
                    "systems to support administration and patient access."
                ),
                "HEALTH",
            ),

            event(
                "International sporting organizations prepare for major events",
                (
                    "Organizers and participating teams are completing preparations "
                    "for upcoming international competitions."
                ),
                "SPORTS",
            ),
        ],

        # ============================================================
        # BRIEF NEWS
        # ============================================================

        "briefs": [

            event(
                "Global diplomatic contacts continue across several regions",
                (
                    "Officials maintain regular consultations as governments "
                    "seek dialogue on international issues."
                ),
                "WORLD",
            ),

            event(
                "Currency markets respond to fresh economic indicators",
                (
                    "Major currencies move as investors assess new economic data "
                    "and policy expectations."
                ),
                "ECONOMY",
            ),

            event(
                "Technology sector tracks new developments in computing",
                (
                    "Companies and researchers continue work on new computing "
                    "systems and digital infrastructure."
                ),
                "TECHNOLOGY",
            ),

            event(
                "Energy producers monitor changing demand patterns",
                (
                    "Producers and traders continue to assess consumption and "
                    "supply conditions across major markets."
                ),
                "BUSINESS",
            ),

            event(
                "Researchers publish new findings from international studies",
                (
                    "Scientists from several institutions release additional "
                    "research and observational data."
                ),
                "SCIENCE",
            ),

            event(
                "Health agencies exchange information on public-health trends",
                (
                    "Authorities continue sharing information and coordinating "
                    "monitoring activities."
                ),
                "HEALTH",
            ),

            event(
                "Athletes prepare for another round of international competition",
                (
                    "Teams and athletes continue preparations for upcoming "
                    "sporting events."
                ),
                "SPORTS",
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
