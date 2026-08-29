# WORLD PULSE v6

**MINIMUM TEXT. MAXIMUM MEANING.**  
**FACTS FIRST. CONTEXT SECOND.**

WORLD PULSE is an automated international news publication system designed to transform verified global news into concise, neutral and contextualized newspaper-style editions.

---

## Current Launch Configuration

| Parameter | Configuration |
|---|---|
| Publication language | English |
| Audience timezone | `America/New_York` |
| Daily editions | 3 |
| Edition times | 07:00 / 13:00 / 20:00 |
| Telegram channel | `@WorldPulseDaily` |
| Telegram format | Audio Edition → Text Edition |
| Operation model | Fully autonomous after production launch |

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

WORLD PULSE uses 14 established editorial directions:

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

WORLD PULSE follows two primary principles:

> **MINIMUM TEXT. MAXIMUM MEANING.**

> **FACTS FIRST. CONTEXT SECOND.**

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
- Editorial Significance.

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
- Editorial Significance.

The Front Page is not a mechanical list of every story.

---

## Newspaper Edition

WORLD PULSE is designed as a digital newspaper-style publication.

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

`@WorldPulseDaily`

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

After production launch, WORLD PULSE must operate without:

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
WORLD-PULSE-EN-2026-08-30-0700
```

The final technical implementation may define the exact format.

Audio, text, visuals and delivery records belonging to the same edition must use the same Edition ID.

---

## Persistent Event Memory

WORLD PULSE requires persistent event memory.

The target operational memory is approximately 30 days for recent events.

The system must be able to recognize:

- previously published events;
- continuing stories;
- new developments;
- duplicate reports;
- previously covered subjects.

Event memory must survive process restarts.

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
- production orchestrator.

Latest recorded full regression:

```text
226 passed
```

Real Telegram delivery:

```text
STATUS: SENT
CHANNEL: telegram
MESSAGE_ID: 29
REAL TELEGRAM TEST: SUCCESS
```

Idempotency test:

```text
FIRST: SENT
FIRST MESSAGE_ID: 30
SECOND: SKIPPED
LOG: SENT
IDEMPOTENCY TEST: SUCCESS
```

---

## Production Work Remaining

The major remaining production stages are:

1. Persistent SQLite delivery state.
2. Stable Edition ID implementation.
3. Persistent event memory.
4. Production Source Registry.
5. Source Reputation implementation.
6. Source Independence implementation.
7. Complete editorial priority engine.
8. Production Edition Builder.
9. Front Page Engine.
10. Full dynamic Layout Engine.
11. Production Visual Engine.
12. Full Audio Edition generation.
13. Audio Quality Control.
14. Audio + Text publication package.
15. Autonomous edition runner.
16. Production scheduler.
17. Hosted production deployment.
18. Monitoring and alerting.
19. Failure recovery.
20. Controlled retry system.
21. Complete end-to-end Quality Control.
22. Full production rehearsal.
23. Autonomous launch.

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
- editorial decision validity.

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
- validating it;
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
- all three daily schedules.

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

WORLD PULSE is considered production-complete only when:

- the complete pipeline runs successfully;
- news is collected and verified;
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

> **FACTS FIRST. CONTEXT SECOND.**
