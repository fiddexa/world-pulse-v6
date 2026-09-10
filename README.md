# AROUND THE MAIN v6

**MINIMUM TEXT. MAXIMUM CLARITY.**  
**VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**

AROUND THE MAIN is an automated international news publication system. It transforms information from a broad international source network into concise, neutral, contextualized and clearly attributed newspaper-style editions.

**AROUND THE MAIN is not a headline-copying aggregator.** Sources provide reporting, facts, data and context; the final product is independently selected, verified, structured and written.

> **Current specification: `AROUND_THE_MAIN_TZ_v1.3.md`**

---

## 1. Current Configuration

| Parameter | Value |
|---|---|
| Brand | AROUND THE MAIN |
| Technical project | WORLD PULSE v6 |
| Language | English |
| Timezone | `America/New_York` |
| Daily editions | 3 |
| Schedule | 07:00 / 13:00 / 20:00 |
| Telegram | `@aroundthemain` |
| Telegram order | Audio → Text / Printed |
| Architecture | ONE EDITION → MULTIPLE PRESENTATIONS |

---

## 2. Core Pipeline

```text
GLOBAL SOURCE NETWORK
        ↓
COLLECT
        ↓
NORMALIZE
        ↓
FACT EXTRACTION
        ↓
DEDUPLICATION
        ↓
EVENT CLUSTERING
        ↓
CROSS-SOURCE VERIFICATION
        ↓
GEOGRAPHIC COVERAGE
        ↓
EDITORIAL SCORING
        ↓
EDITORIAL SELECTION
        ↓
ONE EDITION MODEL
      ↙     ↓      ↘
   FULL   MOBILE   AUDIO
        ↓
TELEGRAM @aroundthemain
```

The data, editorial logic, edition model, renderer and publisher remain separate responsibilities.

---

## 3. One Edition

Each scheduled run creates one editorial snapshot and one Edition ID.

```text
ONE EDITION
 ├── 📰 FULL EDITION
 ├── 📱 MOBILE EDITION
 └── 🎧 AUDIO EDITION
```

All presentations use the same:

- Edition ID;
- publication date;
- edition time;
- selected stories;
- editorial priorities;
- source metadata.

The Edition Model contains, at minimum:

```python
{
    "edition_id": "...",
    "publication_date": "...",
    "edition_time": "...",
    "top_story": ...,
    "main_stories": [...],
    "briefs": [...],
    "sections": {...},
}
```

---

## 4. Editorial Snapshot

The three editions are three independent editorial decisions, not automatic re-publications of one feed.

```text
07:00 → NEW INFORMATION SNAPSHOT → EDITION
13:00 → NEW INFORMATION SNAPSHOT → EDITION
20:00 → NEW INFORMATION SNAPSHOT → EDITION
```

The system evaluates information actually available at the snapshot time. A rigid "last N hours" rule must not determine selection by itself.

Where available, distinguish:

- `event_time`;
- `published_at`;
- `first_seen_at`;
- `last_updated_at`;
- `editorial_time`.

Continuing events may be reconsidered when meaningful developments occur.

---

## 5. Global News Coverage

The primary editorial objective is:

> **MAXIMUM MEANINGFUL COVERAGE OF THE WORLD IN EVERY EDITION.**

A normal edition should target, where the news cycle supports it:

- **8–12+ countries**;
- **6–8+ world regions**.

Relevant regions include North America, Latin America/Caribbean, Europe, Africa, Middle East, Central Asia, South Asia, East Asia, Southeast Asia and Oceania.

Geographic diversity is **not a hard quota**. Important global events may occupy multiple positions. Weak stories must never be added merely to satisfy geography.

The selection engine should balance:

- country;
- region;
- continent;
- cross-border impact;
- international reach;
- global significance;
- freshness;
- momentum;
- verification confidence.

The edition should not be dominated by one country or conflict when other important international developments are available.

---

## 6. News Volume

The system separates candidate collection volume from final publication volume.

### Candidate pool

Normal target:

```text
80–150+ candidate articles per edition run
```

Actual collection may vary with source availability and health.

### Final publication

Default target:

```text
12–16 stories
Target ≈ 14
```

High-density edition:

```text
16–20 stories
```

Practical lower threshold:

```text
≈ 10 stories
```

The system must never create weak, repetitive or low-value stories simply to reach a target.

Page count is dynamic and follows actual editorial volume.

---

## 7. Source Network

Target production network:

```text
≈ 25–40 active sources
```

The exact number is dynamic; quality, reliability, independence and geographic diversity matter more than the number itself.

The source registry should combine:

- major international news organizations;
- regional/national media;
- specialist sources where useful;
- primary institutions;
- governments and public agencies.

Institutional examples include UN, WHO, World Bank, IMF, IEA, OPEC, central banks and public agencies.

The registry must not claim a source as active until its production RSS/Atom/API connector is actually configured and functioning.

One failed connector must not discard successful results from other sources.

### Source independence

Several sites repeating one wire report are not necessarily independent confirmations. Where possible, classify sources as:

- independent reporting;
- primary/official statement;
- direct reporting;
- syndicated;
- republished;
- aggregated;
- unknown derivation.

---

## 8. Editorial Selection

Editorial hierarchy:

```text
LEAD_STORY
↓
TOP_STORY
↓
SECTION_STORY
↓
MAIN_STORY
↓
BRIEF
```

Ranking considers, where available:

- importance;
- score;
- category;
- freshness;
- source reputation;
- source independence;
- verification;
- global impact;
- international reach;
- momentum;
- current relevance;
- publishability.

The final selection must be balanced rather than simply taking the highest individual scores.

---

## 9. Editorial Product

AROUND THE MAIN independently forms:

- headline;
- summary;
- Why It Matters;
- editorial priority;
- section;
- page placement;
- final edition structure.

Source reporting is used as information input. The system must not systematically reproduce full articles, long verbatim passages or source-specific article structures.

The system must never invent facts, quotations, figures, motives, forecasts or unsupported explanations.

---

## 10. Source Attribution

Every published story should identify the meaningful sources actually used.

Example:

```text
SOURCE
Reuters • BBC • Government of Japan
```

Attribution must be truthful and must not be added merely to create an appearance of verification.

Source names and trademarks remain the property of their respective owners. Mentioning a source does not imply endorsement, sponsorship, affiliation or partnership.

---

## 11. Rights-Aware Content Standard

**Attribution is not a license to copy.**

Text and image rights are separate.

### Text

Third-party reporting is an information input. AROUND THE MAIN should produce original headlines and summaries based on verified facts and multiple reports where available.

### Images

Only publish images whose use is authorized, licensed, public-domain, legally reusable under an applicable exception/permission, or otherwise cleared by the project.

An image appearing on a news website does **not** by itself establish permission to reuse it.

If image rights are uncertain:

```text
DO NOT PUBLISH THE IMAGE
        ↓
USE A CLEARED VISUAL
```

Store available image provenance/rights metadata, including provider, original URL where appropriate, license/usage basis, acquisition time and rights status.

### AI-generated visual standard

AROUND THE MAIN uses AI-generated editorial visuals as the default visual format for selected news stories.

Each selected story should receive one dedicated visual based on its verified headline, summary, facts, entities and location.

The same image asset must be reused by Full, Mobile and Telegram.

The `AROUND THE MAIN` brand mark is added programmatically by the renderer for consistent spelling, size and placement.

AI visuals are editorial illustrations and must never be presented as authentic documentary photographs or evidence of an event.


---

## 12. Publication Editorial Notice

A short notice may appear at the end of the publication, before the final footer:

> **Editorial Notice:** AROUND THE MAIN independently selects, verifies and summarizes information from multiple sources. Source attribution is provided for reference and transparency. Third-party names, trademarks, photographs and other protected materials remain the property of their respective owners. Attribution does not imply endorsement, affiliation or a license to reproduce third-party content.

This notice is a transparency measure, **not a legal shield**. It does not replace licensing, rights clearance, legal review or compliance with applicable law.

A full **Editorial & Content Policy** should be maintained on the project website before public/commercial launch.

---

## 13. Corrections / Rights Requests

The production system should support a visible process for:

- factual corrections;
- source attribution corrections;
- image-rights concerns;
- rights-holder requests;
- takedown requests;
- editorial complaints.

Corrections and requests should be traceable to Edition ID and story metadata where possible.

---

## 14. Mobile Edition

Mobile Edition is a separate renderer of the same Edition Model.

Every story card should contain:

1. Image;
2. Headline;
3. Summary;
4. Why It Matters;
5. Sources.

A story must never be split between pages.

### Dynamic page density

The number of pages and placement of cards must depend on actual story count and calculated card height.

The renderer must:

- minimize large unused areas;
- fit as many appropriate stories as practical;
- preserve story integrity;
- adapt card height to content;
- preserve image proportions;
- maintain editorial hierarchy;
- keep Page 01 branded;
- keep later pages compact and consistent;
- keep the footer consistent.

The target is:

> **HIGH INFORMATION DENSITY WITHOUT VISUAL CROWDING.**

---

## 15. Full Edition

Full Edition is the digital newspaper presentation and may contain:

- lead story;
- main stories;
- briefs;
- photographs;
- maps;
- charts;
- timelines;
- infographics;
- section headings;
- date;
- edition number;
- page number;
- footer.

Page count is dynamic. Layout must prioritize editorial value, hierarchy and readability rather than artificial page filling.

---

## 16. Visual System

Established visual language:

- cream/paper background;
- black primary text;
- red accent;
- strict international newspaper aesthetic;
- high information density;
- minimum decoration;
- maximum useful news space.

---

## 17. Audio Edition

Audio is a presentation of the same edition, not a separate editorial selection.

Telegram publication order:

```text
🎧 AUDIO EDITION
        ↓
📰 TEXT / PRINTED EDITION
```

Audio and text must use the same Edition ID.

---

## 18. Telegram

Production channel:

```text
@aroundthemain
```

`@WorldPulseDaily` is not a production destination.

Credentials are provided only through environment variables:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Never commit or expose credentials in source code, README, tests, logs or screenshots.

Production delivery must be idempotent: an already successfully delivered edition/channel combination is skipped rather than duplicated.

---

## 19. Event Memory

Persistent Event Memory is required, with a target recent-memory horizon of approximately 30 days.

It helps identify:

- previously published events;
- continuing stories;
- new developments;
- duplicate reports;
- previous coverage.

It must not become a blanket ban on later editorial reconsideration.

---

## 20. Archive / Reproducibility

Each edition should be reproducible. Persist, where available:

- Edition ID;
- publication date/time;
- Editorial Snapshot time;
- selected stories;
- source metadata;
- image rights/provenance metadata;
- rendered outputs;
- audio output;
- QC result;
- publication status;
- delivery identifiers.

---

## 21. Quality Control

Before publication verify:

### Editorial
- factual accuracy;
- source quality;
- source independence where claimed;
- event clustering;
- duplicate detection;
- geographic coverage;
- relevance and publishability.

### Content
- original headline;
- accurate summary;
- Why It Matters;
- correct attribution;
- correct section.

### Layout
- no broken blocks;
- no unintended large empty areas;
- readable typography;
- correct page numbering;
- correct edition/date;
- correct image proportions.

### Rights
- image provenance recorded;
- usage status known;
- unresolved rights do not silently pass publication.

### Delivery
- correct Edition ID;
- correct channel;
- correct order;
- consistent package metadata;
- idempotency readiness.

---

## 22. Autonomous Production

After launch, production must operate without an open browser, active ChatGPT session, active Codespace, user's computer or manual publication commands.

Codespace is a development environment, not the permanent scheduler.

Required schedule:

```text
America/New_York
07:00
13:00
20:00
```

EST/EDT daylight-saving transitions must be handled correctly.

---

## 23. Production Readiness Gates

Autonomous public launch requires:

1. broad active source registry;
2. source health monitoring;
3. candidate collection at intended scale;
4. geographic coverage metrics;
5. independent event clustering/verification;
6. final story-volume control;
7. dynamic page-density control;
8. rights-aware image handling;
9. source attribution;
10. corrections/rights-request procedure;
11. consistent Full/Mobile/Audio package;
12. Telegram idempotency;
13. hosted scheduler;
14. monitoring and alerting;
15. failure recovery and controlled retries;
16. end-to-end rehearsal.

---

## 24. Implementation Priority

```text
1. SOURCE NETWORK EXPANSION
2. GLOBAL COVERAGE ENGINE
3. EDITORIAL VOLUME / SELECTION
4. DYNAMIC PAGE PLANNING
5. RIGHTS-AWARE CONTENT + IMAGE PROVENANCE
6. FULL / MOBILE / AUDIO HARDENING
7. END-TO-END QC
8. HOSTED AUTONOMOUS PRODUCTION
```

Do not optimize decorative layout before source, editorial and page-planning layers are stable.

---

## 25. Canonical Rule

```text
ONE EDITION
      ↓
ONE EDITORIAL SELECTION
      ↓
FULL + MOBILE + AUDIO
      ↓
ONE EDITION ID
      ↓
TELEGRAM @aroundthemain
```

**Production goal:** a dense, accurate and internationally representative snapshot of the world — three times a day.

---

## 26. Current Development Focus

The current implementation work is focused on:

- expanding the production source registry;
- maximizing meaningful country/region coverage;
- producing a sufficiently rich candidate pool;
- selecting approximately 12–16 strong stories per normal edition;
- dynamically filling mobile pages to avoid large empty areas;
- preserving story integrity between pages;
- implementing rights-aware source/image handling;
- maintaining the existing Telegram/audio/full/mobile architecture.

The repository must not claim global coverage until the source registry actually provides broad functioning coverage.

---

## 27. Canonical Files

- `AROUND_THE_MAIN_TZ_v1.3.md` — current controlling technical specification;
- `AROUND_THE_MAIN_TZ_v1.2.txt` — previous working specification retained for history;
- `README.md` — project overview and operational rules.

**Version:** v1.3  
**Architecture:** ONE EDITION → MULTIPLE PRESENTATIONS  
**Telegram:** `@aroundthemain`

## CURRENT PRODUCTION STATUS — SEPTEMBER 2026

### Production presentation standard

AROUND THE MAIN currently uses a text-first news presentation.

Production news stories contain:

- category;
- headline;
- concise summary;
- source attribution.

Editorial photographs and AI-generated story images are disabled in the production execution path.

The AI visual module may remain in the repository as an experimental component, but it is not a production dependency and must never delay, block or fail an edition.

### Presentation architecture

ONE EDITION produces:

FULL + MOBILE + AUDIO

All three presentations use the same Edition Model, Edition ID, editorial selection and source metadata.

### Full Edition visual standard

All Full Edition news pages use the same text-first newspaper language:

CATEGORY
HEADLINE
SUMMARY
SOURCE

The existing masthead/header and footer remain part of the publication design.

Page 01 follows the same text-first news-feed principle as the later Full Edition pages. The existing market information area remains part of Page 01.

### Mobile visual standard

Mobile uses the same Edition Model and is optimized for smartphone reading and Telegram.

Current production Mobile news cards are text-first:

HEADLINE
SUMMARY
WHY IT MATTERS where available
SOURCES

Stories must never be split between pages.

### Audio

Audio remains an official presentation of the same Edition Model.

Audio and text belong to the same Edition ID.

Telegram production order remains:

AUDIO
↓
TEXT / PRINTED

### Last-page branding

The final Full Edition page may contain an additional AROUND THE MAIN branding and information-rights block when sufficient empty space remains.

Current adaptive threshold:

< 25% free space  -> no block
25–40%            -> COMPACT
40–55%            -> STANDARD
> 55%             -> LARGE

The block uses:

assets/around_the_main_last_page_3x1.png

The asset is a transparent 3:1 PNG.

The block may contain:

AROUND THE MAIN
More than news. A wider perspective.
INFORMATION & RIGHTS POLICY

The block must never displace, compress, remove or reorder published stories.

The existing header and footer remain unchanged.

### Information & Rights Policy

The publication may use the following transparency language:

INFORMATION & RIGHTS POLICY

We gather information from publicly available and reputable news sources, then independently edit and summarize it for clarity, context and informational purposes. We respect intellectual property rights and do not claim ownership of third-party materials.

Trademarks, logos, photographs and other protected materials remain the property of their respective owners and are used with attribution where applicable. No affiliation, endorsement or transfer of rights is implied.

AROUND THE MAIN is an independent editorial project. Content is provided for informational purposes and does not constitute professional, financial, legal or other advice.

This notice is a transparency measure and is not a substitute for licensing, permission, rights clearance, legal review or compliance with applicable law.

### Current production priorities

Operational stability and timely publication have priority over decorative visual generation.

The system must continue to prioritize:

source collection;
event clustering;
verification;
editorial selection;
geographic diversity;
dynamic page planning;
text-first Full/Mobile presentation;
Audio generation;
Telegram delivery;
quality control.

The production goal remains:

ACCURATE + INTERNATIONAL + FAST + STABLE

Three editions per day.
