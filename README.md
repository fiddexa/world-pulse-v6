# AROUND THE MAIN v6

**MINIMUM TEXT. MAXIMUM CLARITY.**  
**VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**

AROUND THE MAIN is an automated international news publication system designed to transform verified global information into concise, neutral and clearly sourced newspaper-style editions.

AROUND THE MAIN is **not a headline aggregator**. International sources provide the information used by the system; the final product is a structured news edition built from verified information, source attribution and editorial selection.

---

## Current Launch Configuration

| Parameter | Configuration |
|---|---|
| Publication language | English |
| Audience timezone | `America/New_York` |
| Daily editions | 3 |
| Edition times | 07:00 / 13:00 / 20:00 |
| Telegram channel | `@aroundthemain` |
| Telegram format | Audio Edition → Text Edition |
| Operation model | Fully autonomous after production launch |

---

## Editorial Snapshot Model

The three daily editions are **three independent editorial decisions**, not three automatic re-publications of the same news feed.

```text
07:00 → NEW INFORMATION SNAPSHOT → AROUND THE MAIN 07:00
13:00 → NEW INFORMATION SNAPSHOT → AROUND THE MAIN 13:00
20:00 → NEW INFORMATION SNAPSHOT → AROUND THE MAIN 20:00
```

Before each edition, AROUND THE MAIN must collect and process the information available from its configured international sources and determine what is most important for the world audience at that moment.

The central editorial question is:

> **What do we know by the time of this edition, and which of the known events are most important to the global audience right now?**

### The system does not use a rigid "last N hours" rule

Publication time from a source is only one signal. AROUND THE MAIN must not automatically use rules such as:

- include everything published within 6 hours;
- exclude everything older than 24 hours;
- include everything published before a fixed hour.

Freshness is an input to editorial evaluation, not the editorial decision itself.

### Four different time concepts

Where possible, the system should distinguish:

- `event_time` — when the event happened;
- `published_at` — when a source published a report;
- `first_seen_at` — when AROUND THE MAIN first received the information;
- `last_updated_at` — when significant new information became available;
- `editorial_time` — the time used for the edition's editorial snapshot.

These timestamps must not be treated as interchangeable.

### Late information example

If an earthquake occurs at 05:30 but the first relevant source report becomes available to AROUND THE MAIN at 07:20:

```text
07:00 snapshot → information not yet available → cannot be selected
13:00 snapshot → information is available → may be selected
```

Selection at 13:00 still depends on verification, significance, current relevance and competition with other events.

### Re-evaluation across editions

The same event may be considered again in a later edition. Previous publication does not automatically suppress future editorial evaluation.

A continuing event may become more or less important depending on:

- new facts;
- new confirmations;
- changing casualty or damage information;
- new official statements;
- international reaction;
- escalation or de-escalation;
- other meaningful developments.

Event Memory provides historical context and duplicate awareness; it must not become a blanket ban on reconsidering a previously seen event.

### Own editorial product

AROUND THE MAIN uses source material as input and independently forms:

- the headline;
- the summary;
- the editorial priority;
- the section assignment;
- the structure of the edition.

The system should combine and compare multiple reports about the same event rather than treating every source headline as a separate final story.

```text
INFORMATION FROM OUR SOURCES
            ↓
COLLECTION
            ↓
NORMALIZATION / FACT EXTRACTION
            ↓
EVENT CLUSTERING
            ↓
CROSS-SOURCE VERIFICATION
            ↓
CURRENT EVENT ANALYSIS
            ↓
EDITORIAL SNAPSHOT
            ↓
RANKING / EDITORIAL SELECTION
            ↓
AROUND THE MAIN HEADLINE + SUMMARY
            ↓
AROUND THE MAIN EDITION
```

**Each edition = new information collection + new analysis + new editorial decision.**

The previous edition is historical context, not the template for the next edition.

---

## Core Pipeline

```text
News Collection
      ↓
Normalization
      ↓
Fact Extraction
      ↓
Clustering
      ↓
Verification
      ↓
Intelligence / Context
      ↓
Editorial Snapshot
      ↓
Ranking
      ↓
Editorial Selection
      ↓
Edition Builder
      ↓
Visual Engine
      ↓
Audio Edition
      ↓
Quality Control
      ↓
Delivery Policy
      ↓
Persistent Delivery State
      ↓
Telegram
```

---

## Editorial Directions

AROUND THE MAIN uses 14 established editorial directions:

1. World
2. Politics
3. Economy
4. Finance
5. Business
6. Technology
7. Science
8. Energy
9. Markets
10. Security
11. Climate
12. Society
13. Health
14. Culture

Sections are included dynamically according to the importance and availability of relevant news.

The system must never artificially fill an edition.

---

## Editorial Principles

AROUND THE MAIN follows two primary principles:

> **MINIMUM TEXT. MAXIMUM MEANING.**

> **VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**

The publication is designed to be:

- factual;
- neutral;
- concise;
- internationally oriented;
- contextual;
- source-conscious;
- editorially selective.

The system must never invent facts, quotations, figures, motives, forecasts or unsupported explanations.

---

## News Intelligence

The pipeline transforms multiple reports into verified events.

```text
Many Articles
      ↓
Event Clustering
      ↓
One Verified Event
```

Each event may be evaluated using:

- Source Reputation;
- Source Independence;
- Verification;
- Freshness;
- Global Impact;
- Momentum;
- International Reach;
- Editorial Significance;
- Current relevance to the edition snapshot.

A single event may be relevant to multiple editorial directions but should not be published multiple times simply because it belongs to multiple sections.

---

## Front Page

The Front Page is dynamic.

It prioritizes the most important stories of each edition according to factors such as:

- Global Impact;
- Freshness;
- Momentum;
- Source Confidence;
- International Reach;
- Editorial Significance;
- relevance at the current Editorial Snapshot.

The Front Page is not a mechanical list of every story.

---

## Newspaper Edition

AROUND THE MAIN is designed as a digital newspaper-style publication.

An edition may contain:

- multiple pages;
- section headings;
- article blocks;
- photographs;
- maps;
- charts;
- timelines;
- infographics;
- contextual information.

The number of pages is dynamic.

There is no fixed page count.

The system must prioritize editorial value, readability and hierarchy rather than artificial page filling.

---

## Visual System

Visual material must have editorial value.

Possible visual formats include:

- real photographs;
- maps;
- charts;
- diagrams;
- timelines;
- data visualizations;
- AI-generated illustrations where appropriate.

AI-generated visuals must never be presented as documentary photographs or real evidence of an event.

---

## Audio Edition

A complete audio version of the edition is a mandatory part of the final publication.

The Audio Edition is not merely a short headline summary.

It should represent the complete published edition in coherent spoken form while preserving the editorial structure and meaning.

---

## Telegram Publication

Current production channel:

`@aroundthemain`

The Telegram production path has been implemented and tested.

Real Telegram delivery has been successfully verified.

Idempotency has also been successfully verified.

Example:

```text
FIRST: SENT
SECOND: SKIPPED
```

### Mandatory Publication Order

The Telegram publication order is:

```text
🔊 AUDIO EDITION
        ↓
📰 TEXT / PRINTED EDITION
```

The Audio Edition must appear above the printed/text version.

Audio and text must belong to the same edition.

---

## Telegram Configuration

Telegram credentials are provided only through environment variables:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Secrets must never be:

- committed to Git;
- stored in source code;
- printed in logs;
- included in test fixtures;
- exposed in screenshots.

---

## Autonomous Publication

After production launch, AROUND THE MAIN must operate without:

- an open browser;
- an active ChatGPT session;
- an active Codespace;
- the user's computer;
- manual publication commands.

The production scheduler must independently trigger the daily editions.

The English-language schedule is:

```text
America/New_York

07:00
13:00
20:00
```

The schedule must correctly handle EST/EDT daylight-saving transitions.

Codespace is a development environment and must not be treated as the permanent production scheduler.

---

## Edition ID

Every production edition must have a stable Edition ID.

The Edition ID must identify, at minimum:

- publication date;
- scheduled edition time;
- language;
- target channel;
- edition instance.

Conceptual example:

```text
AROUND-THE-MAIN-EN-2026-08-30-0700
```

The final technical implementation may define the exact format.

Audio, text, visuals and delivery records belonging to the same edition must use the same Edition ID.

---

## Persistent Event Memory

AROUND THE MAIN requires persistent event memory.

The target operational memory is approximately 30 days for recent events.

The system must be able to recognize:

- previously published events;
- continuing stories;
- new developments;
- duplicate reports;
- previously covered subjects.

Event memory must survive process restarts.

Event Memory must not prevent a previously seen event from being evaluated again for a later Editorial Snapshot.

---

## Delivery Architecture

The delivery system is separated into layers:

```text
Delivery Policy
      ↓
Delivery Log
      ↓
Delivery Executor
      ↓
Publisher Interface
      ↓
Channel Publisher
      ↓
Transport
```

The publisher must not make editorial decisions.

The transport must not modify editorial content.

---

## Idempotency

Idempotency is mandatory for production.

The same edition/event must not be successfully delivered twice to the same channel.

Conceptually:

```text
Same Edition/Event
       +
Same Channel
       ↓
Already SENT
       ↓
SKIPPED
```

Failed deliveries may be retried.

Successful deliveries must not be duplicated after:

- process restart;
- scheduler duplication;
- runner restart;
- temporary network problems.

Production delivery state must therefore be persistent.

---

## Current Development Status

The following components have been implemented and tested:

- normalization;
- fact extraction;
- clustering;
- verification;
- intelligence;
- ranking;
- editorial decision;
- content building;
- publication building;
- delivery policy;
- delivery log;
- delivery executor;
- publisher interface;
- Telegram configuration;
- Telegram publisher;
- Telegram HTTP transport;
- Telegram publisher factory;
- Telegram production runner;
- production orchestrator;
- edition slot resolution;
- persistent Edition Memory;
- persistent Event Memory;
- edition-level Telegram delivery;
- production edition delivery;
- Editorial Snapshot timing passed through production execution.

Latest recorded full regression:

```text
393 passed
```

Real Telegram delivery has been verified successfully with the production bot and channel configuration.

---

## Production Work Remaining

The major remaining production stages are:

1. Production Source Registry expansion.
2. Source Reputation implementation.
3. Source Independence implementation.
4. Editorial Snapshot eligibility based on information availability.
5. `first_seen_at` / `last_updated_at` event-state tracking where source data permits it.
6. Final editorial relevance and priority calibration for real-world news.
7. Production Edition Builder hardening.
8. Front Page Engine.
9. Full dynamic Layout Engine.
10. Production Visual Engine.
11. Full Audio Edition generation.
12. Audio Quality Control.
13. Complete Audio + Text publication package.
14. Hosted production deployment.
15. Monitoring and alerting.
16. Failure recovery.
17. Controlled retry system.
18. Complete end-to-end Quality Control.
19. Full production rehearsal.
20. Autonomous launch.

---

## Production Scheduler

The final scheduler must operate independently of the development environment.

Required English-language schedule:

```text
Timezone: America/New_York

07:00
13:00
20:00
```

The scheduler must:

- trigger the correct edition;
- establish the correct Editorial Snapshot Time;
- prevent accidental duplicate execution;
- support retries;
- survive process restarts;
- use the configured audience timezone;
- operate without the user's computer.

---

## Failure Recovery

The production system must handle:

- source/API failures;
- network failures;
- Telegram failures;
- audio generation failures;
- visual generation failures;
- malformed data;
- process restarts;
- scheduler duplication;
- partial delivery.

Failures must be visible in production logs.

The system must never silently report successful publication when publication failed.

---

## Quality Control

Before publication, the complete edition must pass Quality Control.

QC must cover, where applicable:

### Editorial

- factual accuracy;
- source quality;
- verification;
- duplicate detection;
- editorial decision validity;
- correct Editorial Snapshot eligibility.

### Content

- correct headlines;
- correct summaries;
- correct sources;
- correct section assignment.

### Layout

- valid page structure;
- readability;
- no broken blocks;
- correct hierarchy.

### Visual

- correct event association;
- appropriate visual type;
- no misleading documentary presentation.

### Audio

- correct edition;
- correct language;
- complete audio;
- valid file;
- acceptable quality.

### Delivery

- correct Edition ID;
- correct channel;
- idempotency readiness;
- publication package consistency.

---

## Monitoring

Production monitoring must eventually provide visibility into:

- edition start;
- edition completion;
- Editorial Snapshot Time;
- article collection;
- event count;
- selected stories;
- QC result;
- audio generation;
- delivery;
- Telegram message IDs;
- failures;
- retries.

Secrets must never appear in logs.

---

## Production Safety

Development and production must remain clearly separated.

The following operations must not automatically publish real Telegram messages:

- unit tests;
- syntax checks;
- mock publisher tests;
- local experiments;
- ordinary development scripts.

Real publication must use an explicit production path.

---

## Development Roadmap

### Phase 1 — Persistent State

- SQLite delivery database;
- persistent delivery records;
- Edition ID;
- persistent event memory.

### Phase 2 — Editorial Intelligence

- Source Registry;
- Source Reputation;
- Source Independence;
- Editorial Snapshot eligibility;
- `first_seen_at` / `last_updated_at` tracking;
- improved editorial priority.

### Phase 3 — Edition Construction

- Edition Builder;
- Front Page Engine;
- dynamic Layout Engine.

### Phase 4 — Visual System

- visual decision logic;
- maps;
- charts;
- timelines;
- illustrations;
- AI visual safeguards.

### Phase 5 — Audio

- complete edition audio generation;
- audio formatting;
- audio Quality Control;
- Telegram audio delivery.

### Phase 6 — Publication Package

Integrate:

```text
Edition ID
+
Editorial Snapshot
+
Text
+
Pages
+
Visuals
+
Audio
+
Quality Control
+
Delivery Metadata
```

### Phase 7 — Autonomous Runner

Create a production-safe command capable of:

- building one edition;
- collecting current source information;
- validating the Editorial Snapshot;
- generating the publication package;
- delivering it;
- recording persistent state.

### Phase 8 — Scheduler

Implement:

```text
America/New_York

07:00
13:00
20:00
```

The scheduler must be hosted independently of Codespace and the user's computer.

### Phase 9 — Production Hardening

Implement:

- monitoring;
- alerts;
- failure recovery;
- retries;
- persistent logging;
- operational safeguards.

### Phase 10 — Final Rehearsal

Run a complete end-to-end production rehearsal:

```text
Collection
↓
Editorial Snapshot
↓
Verification
↓
Editorial
↓
Edition
↓
Visuals
↓
Audio
↓
Quality Control
↓
Telegram Audio
↓
Telegram Text
↓
Persistent Delivery State
```

The rehearsal must also verify:

- restart safety;
- duplicate scheduler safety;
- timezone behavior;
- all three daily schedules;
- information cutoff behavior;
- late-arriving information behavior;
- independent editorial selection for each edition.

### Phase 11 — Autonomous Launch

Autonomous publication is activated only after the final production rehearsal succeeds.

---

## Master Technical Specification

The complete and controlling technical specification is:

[WORLD_PULSE_FINAL_TZ_v1.1.md](WORLD_PULSE_FINAL_TZ_v1.1.md)

The master specification contains the complete architectural, editorial, publication, delivery and production requirements.

Important production decisions must be reflected in the master specification rather than existing only in chat history.

---

## Production Completion

AROUND THE MAIN is considered production-complete only when:

- the complete pipeline runs successfully;
- news is collected and verified;
- each edition is built from a fresh Editorial Snapshot;
- information eligibility is evaluated against the edition snapshot;
- editorial selection succeeds;
- the edition is built;
- visuals are valid;
- the complete Audio Edition is generated;
- audio QC passes;
- the text/printed edition is generated;
- Audio is published before Text;
- persistent delivery state is recorded;
- duplicate delivery is prevented;
- failed deliveries can be safely retried;
- the scheduler operates independently of the user's computer;
- the English channel operates at 07:00, 13:00 and 20:00 `America/New_York`;
- monitoring is operational;
- failure recovery is operational;
- the complete end-to-end rehearsal succeeds.

Only after these requirements are satisfied may autonomous production be activated.

---

## Version

Current master specification:

```text
WORLD_PULSE_FINAL_TZ_v1.1.md
```

The original v1.0 specification remains the historical source document.

Future approved architectural or product decisions must be reflected in the master specification and documented in the project changelog.

---

## Project Principle

> **MINIMUM TEXT. MAXIMUM MEANING.**

> **VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**

## Mobile Edition Layout

Mobile Edition is a paginated presentation of one Edition.

### Page 01

Page 01 uses the unified branded header image:

assets/mobile-header.png

The separate logo.png is not rendered in the mobile header.

Page 01 contains:
- branded header;
- edition number;
- publication date;
- edition name;
- PAGE 01;
- edition content;
- DAILY BRIEF footer.

### Pages 02+

Pages 02 and later do not repeat the branded header image.

They use a compact top line with:
- edition name on the left;
- PAGE XX on the right;
- horizontal divider below.

The content follows below the compact header.

### Edition Names

The supported editions are:

- Morning Briefing
- Midday Update
- Evening Round-up

The appropriate edition name is displayed according to the active Edition.

### Page Numbers

Page numbers are generated dynamically:

PAGE 01
PAGE 02
PAGE 03
...

Each rendered page receives its own page_number.

### Footer

Every Mobile Edition page uses the same DAILY BRIEF footer.

The footer contains:
- DAILY BRIEF;
- The most important stories, delivered in brief.;
- GLOBAL NEWS • AROUND THE MAIN;
- Telegram @aroundthemain;
- X @aroundthemain;
- STAY INFORMED. STAY AHEAD.

### Visual System

All pages of one edition use the same visual system:

- newspaper-style cream/paper background;
- black typography;
- red accent;
- consistent dividers and section bars;
- consistent footer;
- consistent typography and spacing.

The first page provides the full brand presentation. Subsequent pages use a clean compact layout while remaining visually connected to Page 01.

ONE EDITION → MULTIPLE PAGES → ONE CONSISTENT VISUAL SYSTEM
