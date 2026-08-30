# WORLD PULSE v6 — CHANGELOG

All significant architectural and production changes are recorded here.

---

## [Unreleased]

Current development continues toward fully autonomous production.

### Next Major Stage

Integration of Persistent Event Memory with the production edition flow.

Planned work:

- connect Event Memory with edition construction;
- associate events with stable Edition IDs;
- record event usage by edition;
- define safe repeat-event handling;
- integrate persistent event state into the production flow;
- maintain restart-safe operation.

---

## 2026-08-30 — Article Pipeline to Edition Builder

### Added

Integrated the article processing pipeline with the WORLD PULSE edition builder.

The new `build_edition_from_articles()` flow now connects:

`Articles → process_articles() → build_edition()`

The function accepts optional:

- `publication_date`;
- `edition_time`.

When both values are supplied, a stable `Edition ID` is generated as part of the edition.

### Tests

Full project regression:

`259 passed`

### Commit

`b28a2a8 connect article pipeline to edition builder`

---

## 2026-08-30 — Persistent Event Memory

### Added

- `pipeline/event_memory.py`
- `tests/test_event_memory.py`

### Implemented

Persistent SQLite event memory using the existing canonical `event_fingerprint()` mechanism.

The memory currently tracks:

- deterministic event fingerprint;
- first seen timestamp;
- last seen timestamp;
- occurrence count;
- last associated Edition ID.

Supported operations:

- remember event;
- check whether an event has been seen;
- retrieve event memory;
- forget an event;
- clear event memory;
- persistence across process restarts.

Event Memory does not independently block publication of previously seen events.

This allows the editorial system to distinguish event history from delivery idempotency and leaves future repeat-publication decisions to the editorial layer.

### Tests

Event Memory tests:

`13 passed`

Full project regression:

`259 passed`

### Commit

`3178781 add persistent event memory`

---

## 2026-08-30 — Stable Edition ID

### Added

- `pipeline/edition_id.py`
- `tests/test_edition_id.py`

### Implemented

Stable deterministic Edition ID generation.

Edition identity is based on:

- publication language;
- publication date;
- edition time.

Current format:

`WORLD-PULSE-EN-YYYY-MM-DD-HHMM`

Example:

`WORLD-PULSE-EN-2026-08-30-0700`

The Edition Builder now accepts:

- `publication_date`;
- `edition_time`.

When supplied, the resulting edition contains the stable `edition_id`.

### Tests

Edition ID tests:

`11 passed`

Edition integration tests:

`23 passed`

Full project regression after the integration:

`246 passed`

### Commit

`08b5405 add stable edition id`

---

## 2026-08-30 — Persistent SQLite Delivery Log

### Added

- `pipeline/sqlite_delivery_log.py`
- `tests/test_sqlite_delivery_log.py`

### Implemented

Persistent SQLite delivery state supporting:

- `SENT` state;
- `FAILED` state;
- persistent records across process restarts;
- channel-specific delivery state;
- idempotent delivery checks;
- clearing stored records;
- validation of events and channels.

### Tests

SQLite-specific tests:

`8 passed`

Full project regression:

`234 passed`

### Commit

`b9014a0 add persistent sqlite delivery log`

---

## 2026-08-30 — Production Telegram Runner

### Added

- `pipeline/telegram_runner.py`
- `tests/test_telegram_runner.py`

### Implemented

- production Telegram runner;
- production-safe Telegram execution path;
- integration with the delivery/orchestration layers;
- controlled Telegram publication flow.

### Tests

Telegram runner tests:

`8 passed`

Full project regression at this stage:

`226 passed`

### Commit

`9118abf add telegram production runner`

---

## 2026-08-30 — Production Delivery Orchestrator

### Added

- `pipeline/orchestrator.py`
- `tests/test_orchestrator.py`

### Implemented

- production delivery orchestration;
- multiple-event handling;
- delivery coordination;
- channel-aware publication;
- idempotent delivery behavior;
- integration with publisher abstractions.

### Tests

Orchestrator tests:

`5 passed`

Full project regression:

`218 passed`

### Commit

`dd8ad2c add production delivery orchestrator`

---

## 2026-08-30 — Telegram HTTP Transport

### Added

- `pipeline/telegram_transport.py`
- `tests/test_telegram_transport.py`

### Implemented

- Telegram Bot API HTTP transport;
- Telegram request handling;
- response processing;
- error handling;
- transport-level testing.

### Tests

Telegram transport tests:

`5 passed`

### Commit

`c9e245c add telegram http transport`

---

## 2026-08-30 — Telegram Publisher Factory

### Added

- `pipeline/telegram_factory.py`
- `tests/test_telegram_factory.py`

### Implemented

- Telegram publisher factory;
- configuration-based publisher creation;
- separation between configuration and publication;
- safe handling of missing Telegram configuration.

### Tests

Telegram factory tests:

`3 passed`

### Commit

`5f5627f add telegram publisher factory`

---

## 2026-08-30 — Telegram Configuration

### Implemented

Telegram configuration through environment variables:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Secrets are not stored in source code.

Configuration validation requires both values.

---

## 2026-08-30 — Telegram Publisher and Idempotency

### Implemented

- Telegram publisher;
- Telegram message publication;
- delivery result handling;
- idempotency protection;
- `SENT` / `SKIPPED` behavior.

### Real Telegram Verification

Production channel:

`@WorldPulseDaily`

Real Telegram delivery:

`STATUS: SENT`

`CHANNEL: telegram`

`MESSAGE_ID: 29`

`REAL TELEGRAM TEST: SUCCESS`

Idempotency verification:

`FIRST: SENT`

`FIRST MESSAGE_ID: 30`

`SECOND: SKIPPED`

`LOG: SENT`

`IDEMPOTENCY TEST: SUCCESS`

---

## 2026-08-29 — Final Technical Specification v1.1

### Added

`WORLD_PULSE_FINAL_TZ_v1.1.md`

The document became the controlling technical specification for WORLD PULSE v6.

### Core Production Configuration

Language:

`English`

Audience timezone:

`America/New_York`

Daily editions:

- `07:00`
- `13:00`
- `20:00`

Telegram channel:

`@WorldPulseDaily`

Publication order:

`Audio Edition → Text / Printed Edition`

The final production system is intended to operate autonomously without:

- an open browser;
- an active ChatGPT session;
- an active Codespace;
- the user's computer;
- manual publication commands.

### Commit

`c089eb6 add final world pulse technical specification v1.1`

---

## 2026-08-29 — Project README

### Updated

`README.md`

The README became the high-level project overview.

The detailed technical requirements remain in:

`WORLD_PULSE_FINAL_TZ_v1.1.md`

### Commit

`2ddda3c update project README`

---

## Development Policy

The following rules apply to future changes:

1. Production architecture must follow the master technical specification.
2. Important architectural decisions must not exist only in chat history.
3. New production behavior must be covered by tests.
4. Existing functionality must remain regression-safe.
5. Real Telegram publication must never occur from ordinary unit tests.
6. Secrets must never be committed to Git.
7. Production state must be persistent.
8. Delivery must remain idempotent.
9. Autonomous publication must not depend on the user's computer or Codespace.
10. Significant architectural changes must be recorded in this changelog.

---

## Current Production Direction

The final target is a fully autonomous English-language WORLD PULSE publication system operating on:

`America/New_York`

Daily editions:

- `07:00`
- `13:00`
- `20:00`

Mandatory Telegram publication order:

`🔊 Audio Edition → 📰 Text / Printed Edition`

The system is not considered production-complete until the complete end-to-end pipeline, persistent state, audio generation, visual generation, quality control, delivery, scheduling, monitoring and failure recovery have been successfully validated.
