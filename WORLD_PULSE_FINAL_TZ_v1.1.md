# AROUND THE MAIN v6 — FINAL TECHNICAL SPECIFICATION v1.1

**Status:** Master Technical Specification
**Project:** AROUND THE MAIN v6
**Current publication language:** English
**Primary audience timezone:** `America/New_York`
**Daily editions:** 07:00, 13:00, 20:00
**Primary Telegram channel:** `@aroundthemain`

---

## 1. PROJECT PURPOSE

AROUND THE MAIN is an automated international news publication system designed to transform verified global news into concise, neutral, contextualized newspaper-style editions.

Core editorial principle:

> **MINIMUM TEXT. MAXIMUM MEANING.**

Secondary principle:

> **VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**

The system must ultimately operate autonomously after final production deployment.

The user must not be required to manually collect news, prepare editions, open a browser, start a Codespace, run scripts, or manually publish each edition.

---

# 2. CURRENT PUBLICATION MODEL

The first production channel is an English-language international news channel.

### Current configuration

- Language: **English**
- Audience timezone: **America/New_York**
- Telegram channel: **@aroundthemain**
- Editions per day: **3**

### Daily publication times

```text
07:00
13:00
20:00
```

All times are interpreted in:


```
America/New_York
```

The schedule must automatically account for EST/EDT daylight-saving changes.

The timezone is determined by the target audience/channel, not by the physical location of the operator.

Future language channels may use different audience timezones and schedules.

---

# 3. AUTONOMOUS OPERATION

After production launch, AROUND THE MAIN must operate without:

-  an open browser;
-  an open ChatGPT session;
-  an active Codespace;
-  the user's computer being powered on;
-  manual execution of the pipeline.

The production scheduler must independently trigger all three daily editions.

The production system must be hosted in an environment capable of running scheduled jobs independently of the development environment.

Codespaces are development environments and must not be treated as the permanent production scheduler.

---

# 4. END-TO-END ARCHITECTURE

The intended production architecture is:


```
                    PRODUCTION SCHEDULER
                            ↓
                    NEWS COLLECTION
                            ↓
                     NORMALIZATION
                            ↓
                    FACT EXTRACTION
                            ↓
                       CLUSTERING
                            ↓
                      VERIFICATION
                            ↓
                 INTELLIGENCE / CONTEXT
                            ↓
                        RANKING
                            ↓
                  EDITORIAL SELECTION
                            ↓
                     CONTENT BUILDER
                            ↓
                     EDITION BUILDER
                            ↓
              FRONT PAGE / LAYOUT ENGINE
                            ↓
                     VISUAL ENGINE
                            ↓
                     AUDIO EDITION
                            ↓
                  PUBLICATION PACKAGE
                            ↓
                     QUALITY CONTROL
                            ↓
                    DELIVERY POLICY
                            ↓
                 PERSISTENT DELIVERY LOG
                            ↓
                  DELIVERY EXECUTOR
                            ↓
                    PUBLISHER INTERFACE
                            ↓
                  CHANNEL PUBLISHER
                            ↓
                       TRANSPORT
                            ↓
                      TELEGRAM
```

Each layer must have a clear responsibility.

External publication must occur only through the explicit production delivery path.

---

# 5. DAILY EDITION MODEL

An edition is a distinct production object.

Each edition must have a stable:


```
Edition ID
```

The Edition ID must identify, at minimum:

-  publication date;
-  scheduled edition time;
-  language;
-  target channel;
-  edition instance.

Example conceptual format:


```
AROUND-THE-MAIN-EN-2026-08-30-0700
```

The exact implementation format may be finalized during the Edition ID phase.

Each selected event must also have a stable identity/fingerprint.

---

# 6. EDITION SCHEDULE

The English-language channel has exactly three planned publication opportunities per day:


```
America/New_York

07:00
13:00
20:00
```

The system should prepare the edition before the scheduled publication time.

News collection and processing may begin sufficiently early to allow:

-  verification;
-  ranking;
-  editorial selection;
-  writing;
-  layout;
-  visuals;
-  audio generation;
-  quality control;
-  delivery preparation.

The publication operation itself occurs at the scheduled time.

---

# 7. EDITORIAL PRINCIPLES

AROUND THE MAIN must be:

-  factual;
-  neutral;
-  internationally oriented;
-  concise;
-  contextual;
-  source-conscious;
-  editorially selective.

The system must not artificially increase the number of stories to make an edition appear fuller.

If there are fewer major developments, the edition may be shorter.

Quality is more important than quantity.

---

# 8. EDITORIAL DIRECTIONS

The established editorial directions are:

1.  World
2.  Politics
3.  Economy
4.  Finance
5.  Business
6.  Technology
7.  Science
8.  Energy
9.  Markets
10.  Security
11.  Climate
12.  Society
13.  Health
14.  Culture

The system may include only the directions justified by the news available for that edition.

No section should be filled artificially.

A single event may have relevance to multiple directions, but the same event must not be published multiple times merely because it belongs to multiple categories.

---

# 9. NEWS COLLECTION

The collection layer must gather current information from appropriate sources.

The collection system should support:

-  international news agencies;
-  reputable newspapers;
-  official government sources;
-  official institutional sources;
-  specialist sources;
-  regional sources where appropriate.

Collection is a discovery and evidence-gathering stage.

Collected material must not automatically become publishable content.

---

# 10. SOURCE HIERARCHY

Sources are evaluated according to reliability and independence.

Conceptual source levels:

### Tier 1

Primary or official sources and highest-confidence direct reporting.

Examples include:

-  government agencies;
-  international organizations;
-  official statements;
-  direct institutional sources;
-  verified first-hand reporting.

### Tier 2

Highly reputable international news organizations.

### Tier 3

Reputable regional and specialist sources.

### Tier 4

Discovery or lower-confidence sources.

Tier 4 information must not automatically become publishable fact.

---

# 11. SOURCE REPUTATION

The system should maintain a Source Registry.

The Source Registry should eventually contain information such as:

-  source name;
-  domain;
-  country/region;
-  category;
-  reputation score;
-  source tier;
-  language;
-  reliability history;
-  correction history where available.

Source reputation must support, but not replace, editorial verification.

---

# 12. SOURCE INDEPENDENCE

Multiple articles are not necessarily multiple independent confirmations.

If several publications repeat the same original report, they should not automatically be counted as independent sources.

The system should identify shared underlying reporting where possible.

---

# 13. FACT EXTRACTION

The system must distinguish verified facts from interpretation.

Each event should be represented through structured information including, where available:

-  headline;
-  what happened;
-  date/time;
-  location;
-  involved entities;
-  confirmed figures;
-  source references;
-  affected areas;
-  verification state.

Unsupported details must not be invented.

---

# 14. VERIFICATION

The verification layer must evaluate whether an event has sufficient evidence for publication.

Verification states may include:


```
VERIFIED
PARTIALLY_VERIFIED
SINGLE_SOURCE
UNVERIFIED
REJECTED
```

The exact final state model may evolve, but publication must remain conservative.

Important claims should receive stronger verification than minor details.

---

# 15. EVENT CLUSTERING

Multiple articles concerning the same underlying event must be clustered.

The system should attempt to recognize:

-  duplicate reports;
-  follow-up reports;
-  updates;
-  translated versions;
-  syndicated content;
-  different angles on the same event.

The goal is:


```
many articles
      ↓
one event
```

rather than:


```
many articles
      ↓
many duplicate stories
```

---

# 16. EVENT MEMORY

AROUND THE MAIN requires persistent event memory.

The target operational memory is approximately 30 days for recent events.

Event memory must allow the system to recognize:

-  previously published events;
-  continuing stories;
-  new developments;
-  duplicate reports;
-  previously covered subjects.

Event memory must survive process restarts.

In-memory-only memory is not sufficient for final production.

---

# 17. GLOBAL IMPACT

Each event may receive a:


```
Global Impact Score: 0–100
```

The score should support editorial ranking.

Possible factors include:

-  number of countries affected;
-  economic significance;
-  geopolitical significance;
-  humanitarian significance;
-  security significance;
-  technological significance;
-  energy impact;
-  international reach;
-  potential consequences.

The Global Impact Score must support editorial judgment rather than replace it.

---

# 18. EDITORIAL PRIORITY

Editorial ranking should consider factors such as:

-  Global Impact;
-  Freshness;
-  Momentum;
-  Source Confidence;
-  International Reach;
-  Editorial Significance;
-  relevance to the current edition.

The highest-scoring event is not automatically required to become the Front Page story.

Final selection remains subject to editorial rules.

---

# 19. CONTENT STRUCTURE

AROUND THE MAIN is a news-first international publication.

Public news content must prioritize:

- verified facts;
- concise summaries;
- reliable source attribution;
- verification status;
- international significance;
- freshness;
- editorial relevance.

### WHAT HAPPENED

A concise factual statement describing the event.

### SUMMARY

A concise factual summary based on verified information.

### SOURCES AND VERIFICATION

Every published story must retain source attribution and an appropriate verification status.

Public editions must NOT include automatically generated:

- editorial opinion;
- political interpretation;
- unsupported predictions;
- statements telling the reader what conclusion to adopt;
- assumptions presented as facts.

The system must never invent:

- motives;
- casualty figures;
- quotations;
- future outcomes;
- political intentions;
- economic forecasts;
- technical explanations;

unless supported by reliable evidence.

If the available information is insufficiently verified, the story should be held for editorial review rather than filled with assumptions or generated interpretation.

---

# 20. FRONT PAGE

The Front Page is dynamic.

It should contain the most important stories of the edition rather than mechanically reproducing every section.

Front Page ranking should consider:

-  Global Impact;
-  Freshness;
-  Momentum;
-  Source Confidence;
-  International Reach;
-  Editorial Significance.

The Front Page may contain:

-  lead story;
-  secondary stories;
-  major visual;
-  concise context;
-  relevant data.

---

# 21. NEWSPAPER FORMAT

The publication is designed as a digital newspaper-style edition.

The edition may contain:

-  multiple pages;
-  section headings;
-  article blocks;
-  images;
-  maps;
-  charts;
-  timelines;
-  infographics.

The number of pages is dynamic.

There is no requirement to fill a fixed page count.

---

# 22. LAYOUT ENGINE

The Layout Engine must determine how content is distributed across pages.

It should consider:

-  story importance;
-  story length;
-  visual requirements;
-  available space;
-  section hierarchy;
-  page balance;
-  readability.

Rules:

-  no artificial page filling;
-  no unnecessary whitespace where avoidable;
-  no overcrowding;
-  clear hierarchy;
-  consistent visual identity.

---

# 23. VISUAL ENGINE

Visuals must provide editorial value.

Possible visual types:

-  real photographs;
-  maps;
-  charts;
-  diagrams;
-  timelines;
-  data visualizations;
-  AI-generated illustrations where appropriate.

Visuals must never be used to fabricate evidence.

AI-generated images must never be presented as documentary photographs or real event evidence.

---

# 24. AUDIO EDITION

The complete edition must have an audio version.

Audio is a mandatory component of a production edition.

The audio edition is not merely a short headline summary.

It should represent the complete published edition in coherent spoken form.

The audio should preserve the editorial structure and meaning of the written edition.

---

# 25. TELEGRAM AUDIO-FIRST PUBLICATION

For the Telegram channel, the publication order is mandatory:


```
🔊 AUDIO EDITION
        ↓
📰 PRINTED / TEXT VERSION
```

The audio message must appear above the printed/text version.

The printed version follows as the newspaper-style edition.

This ordering is part of the product specification.

---

# 26. AUDIO QUALITY CONTROL

Before publication, the audio must be checked for:

-  successful generation;
-  file availability;
-  completeness;
-  correct edition;
-  correct language;
-  acceptable duration;
-  absence of obvious generation errors.

A failed audio generation must not be silently presented as successful publication.

If audio is mandatory for an edition, the system must have a defined failure policy before production launch.

---

# 27. PUBLICATION PACKAGE

A final edition must contain, at minimum:


```
Edition ID
Language
Audience timezone
Scheduled publication time
Selected events
Editorial content
Page structure
Visual metadata
Audio file
Publication metadata
Quality-control result
Delivery state
```

The publication package must represent one coherent edition.

Audio and printed content must correspond to the same Edition ID.

---

# 28. DELIVERY ARCHITECTURE

The delivery architecture is separated into layers:


```
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

Each layer must have a limited responsibility.

The publisher must not make editorial decisions.

The transport must not modify content.

The delivery log must not determine editorial importance.

---

# 29. DELIVERY POLICY

Delivery Policy determines whether a channel is allowed to receive a particular event or edition.

It should account for:

-  editorial decision;
-  channel;
-  publication readiness;
-  duplicate protection;
-  required publication content.

Blocked content must not be sent.

---

# 30. DELIVERY LOG

The current implementation contains an in-memory DeliveryLog.

The current DeliveryLog uses stable event fingerprints and channel-specific state.

Current statuses include:


```
READY
SENT
FAILED
```

For production, the delivery state must become persistent.

SQLite is the preferred initial persistent implementation.

---

# 31. IDEMPOTENCY

Idempotency is mandatory.

The system must prevent duplicate publication of the same event/edition to the same channel.

Conceptually:


```
same identity + same channel
              ↓
        already SENT
              ↓
           SKIPPED
```

A failed attempt may be retried.

A successful attempt must not be duplicated merely because:

-  the process restarted;
-  the scheduler fired twice;
-  the network response was ambiguous;
-  the runner was restarted.

---

# 32. PERSISTENT DELIVERY STATE

Production delivery state must survive process restarts.

At minimum it should retain:

-  edition ID;
-  event fingerprint;
-  channel;
-  status;
-  message ID where available;
-  created timestamp;
-  updated timestamp;
-  error information;
-  retry information where applicable.

The final schema may be expanded during implementation.

---

# 33. TELEGRAM CONFIGURATION

Telegram credentials must never be stored in source code.

The required environment variables are:


```
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

Secrets must never be:

-  committed to Git;
-  printed in logs;
-  included in test fixtures;
-  included in screenshots;
-  embedded in source files.

---

# 34. TELEGRAM CHANNEL

The current production target is:


```
aroundthemain
@aroundthemain
```

Telegram API access has already been successfully verified.

The destination has been verified as a Telegram channel.

---

# 35. TELEGRAM IMPLEMENTATION STATUS

The following components have already been implemented:


```
telegram_config.py
telegram_publisher.py
telegram_transport.py
telegram_factory.py
telegram_runner.py
```

The Telegram Bot API has been tested against the real bot.

Real delivery was successfully verified.

Example recorded result:


```
STATUS: SENT
CHANNEL: telegram
MESSAGE_ID: 29
REAL TELEGRAM TEST: SUCCESS
```

Idempotency was also verified:


```
FIRST: SENT
FIRST MESSAGE_ID: 30
SECOND: SKIPPED
LOG: SENT
IDEMPOTENCY TEST: SUCCESS
```

---

# 36. PRODUCTION ORCHESTRATOR

The production orchestrator coordinates the delivery process.

Its responsibility is to process multiple events and route them through the delivery architecture.

The orchestrator must not bypass:

-  delivery policy;
-  delivery log;
-  delivery executor;
-  publisher abstraction.

---

# 37. TELEGRAM RUNNER

The Telegram runner is the production-facing Telegram execution layer.

It must:

-  receive a prepared publication;
-  use the configured Telegram publisher;
-  perform safe delivery;
-  return delivery results;
-  cooperate with idempotency;
-  avoid exposing secrets.

The runner must not be the scheduler itself.

---

# 38. SCHEDULER

The production scheduler must independently launch edition production.

The English channel requires:


```
America/New_York
07:00
13:00
20:00
```

The scheduler must be independent of:

-  browser state;
-  ChatGPT;
-  Codespace;
-  user's local machine.

A hosted production scheduler or equivalent persistent server-side scheduler is required.

---

# 39. SCHEDULE EXECUTION MODEL

The intended flow is:


```
Scheduled time approaches
        ↓
Edition job starts
        ↓
Collect current news
        ↓
Process / verify / rank
        ↓
Build edition
        ↓
Generate visuals
        ↓
Generate audio
        ↓
Quality Control
        ↓
Create publication package
        ↓
Delivery
        ↓
Audio → Telegram
        ↓
Text → Telegram
        ↓
Record persistent delivery state
```

The final architecture may prepare the edition substantially before the exact publication time.

---

# 40. FAILURE HANDLING

The production system must handle:

-  source failures;
-  API timeouts;
-  network failures;
-  Telegram failures;
-  audio generation failures;
-  visual generation failures;
-  malformed data;
-  process restarts;
-  scheduler duplication;
-  partial delivery.

Failures must be visible in logs.

The system must not silently report successful publication when publication failed.

---

# 41. RETRIES

Retries must be controlled.

A failed delivery may be retried.

A successful delivery must not be repeated.

Retry logic must cooperate with persistent idempotency.

The system must distinguish:


```
FAILED
```

from:


```
SENT
```

and must never treat an uncertain state as permission to blindly duplicate a publication.

---

# 42. QUALITY CONTROL

Before production publication, the complete edition must pass QC.

QC must include, where applicable:

### Editorial

-  factual accuracy;
-  verification;
-  source quality;
-  duplicate detection;
-  editorial decision validity.

### Content

-  complete headlines;
-  correct summaries;
-  correct sources;
-  correct section assignment.

### Layout

-  valid page structure;
-  no broken blocks;
-  acceptable readability.

### Visual

-  correct visual assignment;
-  no misleading documentary presentation;
-  correct event association.

### Audio

-  correct edition;
-  complete audio;
-  correct language;
-  valid file.

### Delivery

-  correct channel;
-  correct Edition ID;
-  idempotency readiness.

---

# 43. PRODUCTION SAFETY

Development and production must remain clearly separated.

The following operations must not automatically publish real Telegram messages:

-  unit tests;
-  syntax checks;
-  normal development scripts;
-  mock publisher tests;
-  local experimentation.

Real external publication must require an explicit production path.

---

# 44. MONITORING

Production monitoring must eventually show:

-  edition start;
-  edition completion;
-  collection count;
-  event count;
-  selected story count;
-  QC result;
-  audio result;
-  publication result;
-  Telegram message IDs;
-  failures;
-  retries.

Secrets must never appear in logs.

---

# 45. ALERTING

The final production system should provide operational alerts for critical failures, including:

-  edition generation failure;
-  QC failure;
-  audio failure;
-  Telegram delivery failure;
-  scheduler failure;
-  persistent storage failure.

The exact alert channel may be selected during production deployment.

---

# 46. CURRENT IMPLEMENTATION STATUS

The following components are implemented and tested:

-  normalization;
-  fact extraction;
-  clustering;
-  verification;
-  intelligence;
-  ranking;
-  editorial decision;
-  content building;
-  publication building;
-  delivery policy;
-  in-memory delivery log;
-  delivery executor;
-  publisher interface;
-  Telegram configuration;
-  Telegram publisher;
-  Telegram HTTP transport;
-  Telegram factory;
-  Telegram runner;
-  production orchestrator.

The system has reached a tested Telegram delivery stage.

Latest recorded full regression result:


```
226 passed
```

---

# 47. TESTING POLICY

The complete regression suite must be run after significant architectural changes.

Current successful test command:


```
python -m pytest -q
```

The latest recorded successful result was:


```
226 passed
```

Individual component tests should continue to be maintained.

No feature is considered production-ready merely because its individual test passes.

End-to-end testing is required.

---

# 48. REMAINING PRODUCTION WORK

The following items are not yet considered complete:

1.  Persistent SQLite delivery storage.
2.  Stable Edition ID implementation.
3.  Persistent event memory.
4.  Production Source Registry.
5.  Source Reputation implementation.
6.  Source Independence implementation.
7.  Complete production editorial priority engine.
8.  Production Edition Builder.
9.  Front Page Engine.
10.  Full dynamic Layout Engine.
11.  Production Visual Engine.
12.  Full Audio Edition generation.
13.  Audio quality-control integration.
14.  Audio/text publication package integration.
15.  Autonomous edition runner.
16.  Production scheduler.
17.  Hosted production deployment.
18.  Monitoring.
19.  Alerting.
20.  Failure recovery.
21.  Controlled retry system.
22.  Complete end-to-end QC.
23.  Full production rehearsal.
24.  Activation of autonomous daily editions.

---

# 49. DEVELOPMENT ROADMAP

## Phase 1 — Persistent State

Implement:

-  SQLite delivery database;
-  persistent delivery records;
-  Edition ID;
-  persistent event memory.

---

## Phase 2 — Editorial Intelligence

Implement:

-  Source Registry;
-  Source Reputation;
-  Source Independence;
-  improved editorial priority.

---

## Phase 3 — Edition Construction

Implement:

-  Edition Builder;
-  Front Page Engine;
-  dynamic Layout Engine.

---

## Phase 4 — Visual System

Implement:

-  visual decision logic;
-  maps;
-  charts;
-  timelines;
-  illustrations;
-  AI visual safeguards.

---

## Phase 5 — Audio

Implement:

-  complete edition audio generation;
-  audio formatting;
-  audio QC;
-  Telegram audio delivery.

---

## Phase 6 — Publication Package

Integrate:


```
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
QC
+
Delivery metadata
```

---

## Phase 7 — Autonomous Runner

Create one production-safe command capable of:

-  building one edition;
-  validating it;
-  generating the publication package;
-  delivering it;
-  recording persistent state.

---

## Phase 8 — Scheduler

Implement:


```
America/New_York

07:00
13:00
20:00
```

The scheduler must be hosted independently of Codespace and the user's computer.

---

## Phase 9 — Production Hardening

Implement:

-  monitoring;
-  alerts;
-  failure recovery;
-  retries;
-  persistent logging;
-  operational safeguards.

---

## Phase 10 — Final Rehearsal

Run a complete end-to-end production rehearsal.

Verify:


```
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
QC
↓
Telegram Audio
↓
Telegram Text
↓
Persistent Delivery State
```

Verify restart safety.

Verify duplicate scheduler safety.

Verify timezone behavior.

Verify all three daily schedules.

---

## Phase 11 — Autonomous Launch

Only after the final production rehearsal succeeds should autonomous publication be activated.

---

# 50. NON-NEGOTIABLE PRINCIPLES

1.  Never invent facts.
2.  Never present AI-generated imagery as documentary photography.
3.  Never publish the same event twice because of duplicate source articles.
4.  Never duplicate a successful delivery after restart.
5.  Never expose Telegram secrets.
6.  Never allow ordinary tests to publish externally.
7.  Never artificially fill an edition.
8.  Never artificially fill a page.
9.  Never confuse audience timezone with operator location.
10.  Never omit mandatory Audio Edition publication.
11.  Telegram publication order must be Audio → Text.
12.  Audio and text must belong to the same Edition ID.
13.  Production delivery must be restart-safe.
14.  Production scheduler must operate independently of the user's browser and computer.
15.  Autonomous publication must not be activated before complete production rehearsal.
16.  A failed QC result must not be represented as successful publication.

---

# 51. VERSION CONTROL

This document is the current master technical specification for AROUND THE MAIN v6.

Current version:


```
v1.1
```

The original v1.0 specification remains the historical source document.

Version `v1.1` incorporates the subsequently approved architectural and product decisions, including:

-  English-language launch;
- `America/New_York`;
-  three daily editions;
-  07:00 / 13:00 / 20:00;
-  autonomous operation;
-  mandatory full-edition audio;
-  Audio → Text Telegram publication order;
-  Edition ID;
-  persistent event memory;
-  persistent delivery state;
-  production scheduler;
-  current Telegram production implementation.

Future changes must be explicitly reflected in the version history.

---

# 52. DEFINITION OF PRODUCTION COMPLETE

AROUND THE MAIN is considered production-complete only when:

-  the complete pipeline runs successfully;
-  the edition is prepared before publication;
-  all required verification passes;
-  editorial QC passes;
-  visual requirements pass;
-  the complete audio edition is generated;
-  audio QC passes;
-  the publication package is internally consistent;
-  Telegram audio is published first;
-  Telegram text/printed version is published second;
-  persistent delivery state is recorded;
-  duplicate delivery is prevented;
-  failed deliveries can be safely retried;
-  scheduler execution is independent of the user's computer;
-  the English channel operates at 07:00, 13:00 and 20:00 `America/New_York`;
-  monitoring is operational;
-  failure recovery is operational;
-  the complete end-to-end rehearsal succeeds.

Only then may autonomous production be activated.

---

# 53. MASTER PROJECT RULE

This document is the controlling technical reference for AROUND THE MAIN v6.

When a new architectural or product decision is approved, it must be reflected in this document before the implementation is considered complete.

The code must implement the specification.

The specification must describe the actual production architecture.

No important production requirement should exist only in chat history.

---

**AROUND THE MAIN v6**

**MINIMUM TEXT. MAXIMUM MEANING.**

**VERIFIED FACTS. CLEAR SOURCES. NO AUTOMATED OPINION.**
