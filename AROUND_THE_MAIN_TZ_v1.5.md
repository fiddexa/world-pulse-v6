# AROUND THE MAIN — TECHNICAL SPECIFICATION v1.5

**Project:** WORLD PULSE v6
**Public brand:** AROUND THE MAIN
**Primary Telegram:** `@aroundthemain`
**Status:** Current working production specification

> v1.5 is the current production specification and defines the release-to-release Mobile + Audio collection model, adaptive release volume, global source coverage, source attribution, rights awareness, dynamic page density, publication safety, and the mandatory production publication order TEXT → AUDIO.

---

## 1. CORE CONCEPT

AROUND THE MAIN is an automated international news publication that forms multiple editorial editions during the day.

Core principle:

```text
ONE SET OF INFORMATION
        ↓
ONE EDITION
        ↓
MULTIPLE PRESENTATIONS
```

The system must produce an independent editorial product rather than mechanically republishing source headlines.

### Production Publication Order

For every approved production edition, Telegram publication follows this mandatory sequence:



The Audio Edition must never be generated or published before the text publication step has been successfully completed or confirmed as already completed.

The text delivery state is the gate for the Audio stage.

Canonical Audio Telegram caption:



---

## 2. ARCHITECTURE

```text
GLOBAL NEWS SOURCES
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
GEOGRAPHIC COVERAGE ANALYSIS
        ↓
EDITORIAL SCORING
        ↓
EDITORIAL SELECTION
        ↓
ONE EDITION MODEL
      ↙     ↓      ↘
   FULL   MOBILE   AUDIO
      \      ↓      /
       TELEGRAM PUBLISHER
             ↓
       @aroundthemain
```

Responsibilities remain separated:

- **DATA:** what happened;
- **EDITORIAL LOGIC:** what should be published;
- **EDITION:** which snapshot was formed;
- **RENDERER:** how it looks;
- **PUBLISHER:** where it is delivered.

---

## 3. DAILY EDITIONS

Current schedule:

```text
America/New_York

07:00 — MORNING BRIEFING
13:00 — MIDDAY UPDATE
20:00 — EVENING ROUND-UP
```

Each edition receives its own Edition ID.

Each edition is a new editorial snapshot, not an automatic continuation of the previous edition.

---

### Release-to-release editorial window

Mobile + Audio selection is release-driven rather than quantity-driven.

Canonical slots:
- 07:00
- 13:00
- 20:00

Canonical release windows:
- 07:00: previous day 20:00 → current day 07:00
- 13:00: current day 07:00 → current day 13:00
- 20:00: current day 13:00 → current day 20:00

The system prioritizes information newly available since the previous release. The release window is a priority boundary, not an absolute exclusion boundary: older information may remain eligible when materially important or when it represents a significant development.

## 4. EDITORIAL SNAPSHOT

The system evaluates information available by the edition's editorial snapshot time.

Do not use a rigid rule such as "last 6 hours" or "last 24 hours" as the sole selection mechanism.

Where available, distinguish:

- `event_time` — when the event happened;
- `published_at` — when a source published the report;
- `first_seen_at` — when the system first received the information;
- `last_updated_at` — when meaningful new information became available;
- `editorial_time` — the snapshot time of the edition.

A late report may therefore appear in a later edition if it was not available for the earlier snapshot.

Continuing events may be reconsidered in later editions when meaningful developments occur.

---

## 5. SOURCE NETWORK

The production system must use a broad international source network.

### Target

```text
≈ 25–40 active production sources
```

The exact number is dynamic. Quality and regional diversity are more important than an arbitrary source count.

The network should include a mixture of:

1. major international news organizations;
2. regional and national media;
3. specialist sources where appropriate;
4. primary institutional sources;
5. official government and public-agency sources.

Examples of institutional sources include UN, WHO, World Bank, IMF, IEA, OPEC, central banks and government/public agencies.

International and regional coverage should collectively seek meaningful representation from:

- North America;
- Latin America and the Caribbean;
- Europe;
- Africa;
- Middle East;
- Central Asia;
- South Asia;
- East Asia;
- Southeast Asia;
- Oceania.

The registry must not claim a source as active until its production feed/API is actually configured and functioning.

A failed source connector must not cause successful sources to be discarded.

---

## 6. SOURCE INDEPENDENCE

Source count is not the same as independent confirmation.

Multiple websites may reproduce one wire report. The system should distinguish, where technically possible:

- independent reporting;
- primary/official statement;
- direct reporting;
- syndicated content;
- republished content;
- aggregated content;
- unknown derivation.

Cross-source verification should reward genuinely independent confirmation rather than duplicate copies of the same report.

---

## 7. NEWS COLLECTION VOLUME

The system must distinguish candidate collection from final publication.

### Candidate pool

Normal production target:

```text
80–150+ candidate articles per edition run
```

The result may be lower or higher according to actual source availability and source health.

### Final edition

Default target:

```text
12–16 published stories
Target ≈ 14
```

High-density editions may contain:

```text
16–20 stories
```

Practical lower threshold:

```text
≈ 10 stories
```

The system must never create weak or repetitive stories solely to reach a numerical target.

If the news cycle genuinely provides fewer publishable stories, editorial quality takes precedence.

---

### Adaptive release volume

There is no fixed number of stories per release.

The number of Mobile + Audio stories is determined by the actual qualifying information available for that release window.

The system must never:
- force-fill a release to a target count;
- discard a qualifying important story solely because a target count was reached;
- treat 30 stories, 25 stories, or any other numeric value as a canonical requirement.

## 8. GLOBAL COVERAGE

A central production objective is:

> **MAXIMUM MEANINGFUL COVERAGE OF THE WORLD IN EVERY EDITION.**

Geographic diversity is an editorial objective, not a hard quota.

Normal target:

```text
8–12+ countries where the news cycle supports it
6–8+ world regions where relevant
```

The selection engine should consider:

- country;
- region;
- continent;
- cross-border impact;
- international relevance;
- event significance;
- source confidence;
- freshness;
- momentum.

Avoid unnecessary concentration on one country, region or conflict when other important international developments are available.

Exceptional global events may legitimately occupy several positions.

The system must never add a weak story from an underrepresented country simply to satisfy a geographic quota.

---

## 9. DEDUPLICATION AND EVENT CLUSTERING

Many source articles about one event should normally become one editorial event.

```text
20 REPORTS
    ↓
EVENT CLUSTER
    ↓
VERIFIED FACT SET
    ↓
ONE EDITORIAL STORY
```

The system must detect duplicate and near-duplicate reporting and avoid publishing the same event repeatedly in one edition.

A later meaningful development can create a new editorial treatment in a later edition.

---

## 10. EDITORIAL SELECTION

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

Ranking should consider:

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

The editorial engine must select a balanced edition, not simply the highest-scoring articles in isolation.

---

### Release-window selection hierarchy

For Mobile + Audio, selection priority is:

1. New information since the previous release.
2. Materially new developments of previously known stories.
3. Editorial importance.
4. Freshness.
5. International relevance and impact.
6. Soft geographic and thematic diversity.

Diversity rules must not become hard exclusion rules for otherwise qualifying important events.

## 11. EDITORIAL PRODUCT

AROUND THE MAIN independently forms:

- headline;
- summary;
- Why It Matters;
- editorial priority;
- section;
- page placement;
- final edition structure.

The final text should be original editorial writing based on verified facts.

The system must not invent:

- facts;
- quotations;
- figures;
- motives;
- forecasts;
- unsupported causal explanations.

---

## 12. CATEGORIES

Current newspaper directions:

1. World
2. Geopolitics / Politics
3. Business / Economy
4. Energy
5. Technology
6. Science & Health
7. Climate
8. Trade & Logistics
9. Society
10. Culture
11. Sports

Categories are dynamic according to available and important news.

Do not artificially create categories or stories to fill a page.

---

## 13. EDITION MODEL

The edition is the single source of truth for all presentation layers.

Minimum structure:

```python
edition = {
    "edition_id": "...",
    "publication_date": "...",
    "edition_time": "...",
    "top_story": ...,
    "main_stories": [...],
    "briefs": [...],
    "sections": {...},
}
```

Full, Mobile and Audio must use the same editorial selection, date, time, Edition ID and source metadata.

---

## 14. FULL EDITION

Full Edition is the digital newspaper presentation.

It may contain:

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

Page count is dynamic.

The layout must prioritize information density, hierarchy and readability.

---

## 15. MOBILE EDITION

Mobile Edition is a separate presentation layer of the same Edition Model.

It is designed for smartphone reading, vertical scrolling and Telegram.

Every news card should contain:

1. Image;
2. Headline;
3. Summary;
4. Why It Matters;
5. Sources.

A story must never be split between pages.

### Dynamic page planning

Pages must be populated according to actual story count and card heights.

The renderer must:

- minimize large empty regions;
- fit as many appropriate stories as practical on each page;
- preserve story integrity;
- adapt card height to content;
- preserve image proportions;
- keep visual hierarchy;
- retain the established first-page branded header;
- retain the established compact headers on later pages;
- keep the footer consistent.

The goal is:

> **HIGH INFORMATION DENSITY WITHOUT VISUAL CROWDING.**

---

## 16. MOBILE PAGE STRUCTURE

### PAGE 01

- branded header image: `assets/mobile-header.png`;
- edition label;
- publication date;
- edition name;
- PAGE 01;
- news content;
- Daily Brief/footer area.

### PAGES 02+

- compact edition/header row;
- PAGE XX;
- divider;
- news content;
- same footer system.

Page number is dynamic and must not be stored in a global variable.

---

## 17. VISUAL SYSTEM

Use the established newspaper visual language:

- cream/paper background;
- black primary text;
- red accent;
- strict newspaper aesthetic;
- high information density;
- minimum decoration;
- maximum useful news space.

Visual material must have editorial value.

### AI-Generated Editorial Visual Standard

AI-generated editorial visuals are the default visual format for selected news stories.

For each selected story, the system should generate one dedicated visual from the common Edition/Event Model using verified headline, summary, Why It Matters, extracted facts, entities, locations and section/topic.

One event must produce one reusable image asset:

ONE EVENT -> ONE IMAGE ASSET -> FULL + MOBILE + TELEGRAM

The `AROUND THE MAIN` brand mark must be applied programmatically by the renderer, not generated as text inside the AI image.

AI-generated visuals must represent the subject accurately, must not invent material facts, and must never be presented as authentic documentary photographs or evidence of an event.

Generation metadata should be retained where available. Failed generation must not result in an unrelated image being silently attached.


---

## 18. SOURCE ATTRIBUTION

Each published story must identify the meaningful sources actually used.

Example:

```text
SOURCE
Reuters • BBC • Government of Japan
```

or:

```text
SOURCE
UN News • WHO
```

Attribution must be truthful and must not be added merely to create an appearance of verification.

Source names and trademarks remain the property of their respective owners. A source citation does not imply endorsement, sponsorship, affiliation or partnership.

---

## 19. RIGHTS-AWARE CONTENT POLICY

AROUND THE MAIN must be designed to reduce copyright and other rights risks.

### Text policy

Third-party articles are information inputs. The final AROUND THE MAIN story should be independently written and substantially transformed into the publication's own concise editorial presentation.

Do not systematically reproduce:

- full source articles;
- long verbatim passages;
- source-specific article structures;
- copyrighted material merely because a source is credited.

Attribution is **not a substitute for permission or a license**.

### Images

Image rights must be treated separately from text attribution.

Only use images that are:

- properly licensed;
- authorized for the intended use;
- public domain;
- legally reusable under an applicable exception or permission;
- otherwise cleared by the project.

The presence of an image on a news website does not itself establish reuse rights.

If rights are uncertain, do not publish the image. Use a cleared image, public-domain visual, licensed asset, chart/map generated from lawful data, or an appropriately labeled AI-generated illustration where suitable.

### Provenance

For each published image, store available provenance/rights metadata such as:

- source/provider;
- original URL where appropriate;
- license or usage basis;
- acquisition timestamp;
- rights status;
- attribution requirements.

---

## 20. EDITORIAL NOTICE

A short notice may appear at the end of the publication, before the final footer, or in the website's Editorial & Content Policy:

> **Editorial Notice:** AROUND THE MAIN independently selects, verifies and summarizes information from multiple sources. Source attribution is provided for reference and transparency. Third-party names, trademarks, photographs and other protected materials remain the property of their respective owners. Attribution does not imply endorsement, affiliation or a license to reproduce third-party content.

The notice is a transparency measure, **not a legal shield**. It does not replace licensing, rights clearance, legal review or compliance with applicable law.

The production system should support a full public Editorial & Content Policy before commercial/public launch.

---

## 21. CORRECTIONS AND RIGHTS REQUESTS

A production-ready system should provide a visible process for:

- factual corrections;
- source attribution corrections;
- image rights concerns;
- rights-holder requests;
- takedown requests;
- editorial complaints.

Requests and corrections should be traceable to Edition ID and story metadata where possible.

---

## 22. TELEGRAM

Production destination:

```text
@aroundthemain
```

Old production identifier:

```text
@WorldPulseDaily
```

The old channel must not be used as the production destination.

Mandatory order:

```text
🎧 AUDIO EDITION
        ↓
📰 TEXT / PRINTED EDITION
```

Audio and text must belong to the same Edition ID.

---

## 23. TELEGRAM SECURITY

Credentials must be supplied through environment variables only:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Never commit, hard-code, print or expose credentials in:

- source code;
- README;
- TЗ;
- tests;
- logs;
- screenshots.

---

## 24. EDITION ID

Every edition receives a deterministic stable identifier containing, at minimum:

- publication date;
- edition time;
- language.

Conceptual format:

```text
AROUND-THE-MAIN-EN-2026-08-30-0700
```

All presentation and delivery artifacts belonging to the same edition use the same Edition ID.

---

## 25. EVENT MEMORY

Persistent Event Memory is required.

Target recent-memory horizon:

```text
≈ 30 days
```

It should recognize:

- previously published events;
- continuing stories;
- new developments;
- duplicate reports;
- prior coverage.

Memory must not become a blanket ban on later editorial reconsideration.

---

### Release continuity

Event Memory stores event observation and edition usage history.

For release continuity:
- unchanged events already used in an earlier edition are excluded from repeat Mobile + Audio publication;
- materially changed developments may be selected when event identity/fingerprint changes;
- edition history represents events actually used by an edition;
- Event Memory does not determine editorial ranking and does not replace verification.

## 26. ARCHIVE

Each edition must be reproducible.

Persist, where available:

- Edition ID;
- publication date;
- edition time;
- editorial snapshot time;
- selected stories;
- source metadata;
- image provenance/rights metadata;
- rendered output;
- audio output;
- QC result;
- publication status;
- delivery identifiers.

---

## 27. QUALITY CONTROL

Before publication, QC must check:

### Editorial

- factual accuracy;
- source quality;
- source independence where claimed;
- event clustering;
- duplicate detection;
- global geographic coverage;
- editorial relevance;
- publishability.

### Content

- original headline;
- accurate summary;
- Why It Matters;
- correct source attribution;
- correct section.

### Layout

- no broken blocks;
- no unintended large empty regions;
- readable typography;
- correct page numbers;
- correct edition/date;
- correct image proportions.

### Rights

- image provenance recorded where applicable;
- rights/usage status known;
- unresolved rights not silently published.

### Delivery

- correct Edition ID;
- correct Telegram destination;
- correct publication order;
- consistent package metadata;
- idempotency readiness.

---

## 28. IDEMPOTENCY

Production delivery is idempotent.

```text
SAME EDITION
+
SAME CHANNEL
        ↓
ALREADY SENT
        ↓
SKIPPED
```

Failed deliveries may be retried. Successful deliveries must not be duplicated after process restart, scheduler duplication or runner restart.

---

## 29. AUTONOMOUS PRODUCTION

After launch, ordinary production must operate without:

- an open browser;
- an active ChatGPT session;
- an active Codespace;
- the user's computer;
- manual publication commands.

Codespace is a development environment, not the permanent production scheduler.

---

## 30. TESTING

Test independently:

- source collection;
- normalization;
- clustering;
- verification;
- editorial selection;
- global coverage balancing;
- Edition Model;
- Full renderer;
- Mobile renderer;
- Audio;
- Telegram publication;
- idempotency;
- failure recovery;
- rights metadata and publication blocking.

Unit tests, local previews and mock publisher tests must never automatically publish real Telegram messages.

---

## 31. PRODUCTION READINESS GATES

Autonomous public launch requires, at minimum:

1. broad active source registry;
2. working source-health monitoring;
3. candidate collection at the intended production scale;
4. geographic coverage measurement;
5. independent event clustering and verification;
6. final story-volume control;
7. dynamic page-density control;
8. rights-aware image handling;
9. source attribution;
10. corrections/rights-request procedure;
11. complete Full/Mobile/Audio package consistency;
12. Telegram idempotency;
13. hosted scheduler;
14. monitoring and alerting;
15. failure recovery and controlled retries;
16. complete end-to-end rehearsal.

---

## 32. IMPLEMENTATION PRIORITY

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

Do not optimize decorative layout before the source, editorial and page-planning layers are stable.

---

## 33. CANONICAL RULE

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

The publication goal is:

> **A dense, accurate, internationally representative snapshot of the world — three times a day.**

---

## 34. STATUS

**Version:** v1.5
**Status:** Current working production specification
**Primary Telegram:** `@aroundthemain`
**Architecture:** ONE EDITION → MULTIPLE PRESENTATIONS

## CURRENT PRODUCTION STATUS — SEPTEMBER 2026
### Release-to-release news collection

The current editorial collection model is release-to-release for Mobile + Audio.

The three daily releases use the previous release as the primary information boundary:
20:00 → 07:00, 07:00 → 13:00, 13:00 → 20:00.

Story count is fully adaptive and determined by the actual amount of new, important and fresh information.


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


---

# CURRENT VERIFIED IMPLEMENTATION — SEPTEMBER 2026

This section records the currently approved production decisions and
verified behavior for AROUND THE MAIN.

## Editorial release model

Editions are built release-to-release:

- 07:00 edition uses the previous 20:00 release as its comparison/reference boundary.
- 13:00 edition uses the previous 07:00 release.
- 20:00 edition uses the previous 13:00 release.

The release window is a priority boundary, not a hard cutoff. Older
materially important developments may remain eligible.

Story count is adaptive. There is no fixed target, minimum, or maximum
number of Mobile/Audio stories.

EventMemory has an approximately 30-day history horizon. This is a memory
storage horizon, not a story-count rule.

Only events actually included in the final ordered edition are recorded
as published edition history.

## Mobile and Audio

Mobile and Audio use the same canonical selected event sequence:
`mobile_audio["events"]`.

The renderer must never concatenate `top_story`, `main_stories`,
`briefs`, and `events` as separate story pools. The canonical `events`
list is authoritative.

Mobile and Audio therefore use the same stories in the same order.

The edition number remains spoken in Audio, because it identifies the
release number.

## Mobile pagination

Mobile pagination is content-driven.

- Stories are never split between pages.
- Card height is calculated from the same typography used during final drawing.
- Page count is adaptive.
- There is no fixed number of stories per page.

## Mobile SOURCE layout

The SOURCE block is part of the normal text flow.

The required order is:

1. headline;
2. summary;
3. small gap;
4. `SOURCE`;
5. source name;
6. bottom padding;
7. card bottom border.

SOURCE must never be anchored independently to the bottom of the card in
a way that can overlap the summary.

Card height must reserve the complete space required by summary + SOURCE.

## Mobile date

Every Mobile page displays the edition date.

When an explicit edition date is unavailable, the renderer derives the date
from the production `edition_id` format:

`AROUND-THE-MAIN-EN-YYYY-MM-DD-HHMM`

The display format is `DD MON YYYY`, for example `11 SEP 2026`.

## Last-page branding

The final Mobile page may use otherwise unused vertical space after the
last story.

The goal is visual balance, not mandatory placement of branding.

The information block is identical whether or not a banner is present.

The information block is:

- italic;
- non-bold;
- smaller than normal story text;
- compact line spacing;
- never truncated.

The last-page decision logic is:

- if there is enough space for banner + complete INFO, render both;
- otherwise, if the complete INFO block fits, render INFO only;
- if the complete INFO block does not fit, render nothing.

The banner uses six adaptive sizes and the largest size that physically
fits together with the complete INFO block is selected.

The banner must never overlap the footer.

## International relevance gate

For Mobile/Audio, official UK and Canadian government sources are subject
to an international-relevance gate.

A government-source story is retained only when the headline/summary
contains direct evidence of international relevance.

Aggregated actor/affected-area metadata alone is not sufficient evidence,
because clustered events can contain background references that do not
make a story itself international.

Domestic government stories are therefore excluded from Mobile/Audio.

## Publishing architecture

The intended production flow is:

collection → editorial selection → Mobile → Audio → Telegram → X.

External credentials for publishing are stored as GitHub Actions Secrets,
not inside the Codespace or source files.

X publication is configured and fully tested before the development
Codespace is deleted.

Once code, workflows, secrets, and automatic publication have been
successfully tested, the Codespace may be stopped or deleted.

The GitHub repository and GitHub Actions remain the production system;
the Codespace is only a development environment.

## Current verified checkpoints

`8740cb9` — Mobile last-page branding and source-layout checkpoint.

`8dc1752` — Mobile SOURCE flow, edition date fallback, and adaptive
last-page branding verified visually.

These checkpoints are part of the recovery history and must not be
replaced by ad-hoc rewrites.

---

### Version v1.5

Version `v1.5` incorporates the approved production publication-order change.

The mandatory production sequence is:

APPROVED
   ↓
BUILD EDITION
   ↓
PUBLISH TEXT TO TELEGRAM
   ↓
TEXT DELIVERY CONFIRMED
   ↓
GENERATE AUDIO EDITION
   ↓
PUBLISH AUDIO TO TELEGRAM

The Audio Edition must never be generated or published before the
text publication step has been successfully completed or confirmed
as already completed.

For a normal first publication:

TEXT = SENT
   ↓
AUDIO = GENERATED
   ↓
AUDIO = SENT

For a repeated or restarted production run:

TEXT = SKIPPED
   ↓
TEXT ALREADY PUBLISHED
   ↓
AUDIO MAY CONTINUE

Text and Audio must belong to the same `Edition ID` and edition number.

Canonical Audio Telegram caption:

AROUND THE MAIN — EDITION 0114
Audio Edition

Audio delivery idempotency remains a separate production-hardening
requirement and must be verified before autonomous production launch.
