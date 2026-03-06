# RAILMonitor Architecture — v2.3.0 Planning

> Internal design doc for the monitoring/logging layer planned for SDK v2.3.0.

---

## Overview

A centralized event bus that captures every RAIL API call (eval, safe-regenerate, compliance) across all clients and sessions, routes events to pluggable sinks (console, file, callback, external), and tracks per-application stats.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     rail_score_sdk.init()                        │
│                                                                 │
│  Sets global api_key, creates singleton RAILMonitor,            │
│  auto-attaches to all clients/sessions created after init.      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                       RAILMonitor                               │
│                                                                 │
│  Central event bus. Receives events from all clients/sessions.  │
│  Routes to configured sinks. Tracks global stats.               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐     │
│  │ EventBuffer  │  │ StatsAggr   │  │ SessionRegistry     │     │
│  │             │  │             │  │                     │     │
│  │ In-memory   │  │ Running     │  │ app_id -> Session   │     │
│  │ ring buffer │  │ counts,     │  │ Tracks per-app      │     │
│  │ of last N   │  │ avg scores, │  │ sessions, scores,   │     │
│  │ events      │  │ regen rate  │  │ history             │     │
│  └─────────────┘  └─────────────┘  └─────────────────────┘     │
└────────────┬──────────────┬──────────────┬──────────────────────┘
             │              │              │
        emit("eval")   emit("regen")  emit("compliance")
             │              │              │
             ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Sinks                                   │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ Console  │  │ JSONL    │  │ Callback │  │ Langfuse/     │   │
│  │ Logger   │  │ File     │  │ Hook     │  │ External      │   │
│  │          │  │          │  │          │  │               │   │
│  │ Colored  │  │ Append-  │  │ async fn │  │ Push to any   │   │
│  │ summary  │  │ only,    │  │ per event│  │ observability │   │
│  │ per call │  │ rotate   │  │ or batch │  │ platform      │   │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Global init — one line to start monitoring everything

```python
import rail_score_sdk

rail_score_sdk.init(
    api_key="rail_xxx",
    monitor={
        "console": True,                     # print scores to stderr
        "log_file": "rail_scores.jsonl",     # structured event log
        "on_event": my_webhook_callback,     # async hook per event
        "buffer_size": 1000,                 # in-memory ring buffer
    },
)
```

After `init()`, every `RailScoreClient()` and `RAILSession()` created without an explicit `api_key` picks it up from the global config. Every call auto-emits events to the monitor.

---

### 2. Sessions are scoped by `app_id`

```python
# Chatbot A — healthcare domain
chatbot_session = RAILSession(
    app_id="chatbot-healthcare",
    threshold=8.0,
    policy="safe_regenerate",
    domain="healthcare",
)

# Chatbot B — general assistant
assistant_session = RAILSession(
    app_id="assistant-general",
    threshold=7.0,
    policy="log_only",
)

# Content moderation pipeline
moderation_client = RailScoreClient(app_id="content-mod")
```

The `SessionRegistry` inside the monitor groups events by `app_id`. You can query per-app stats:

```python
monitor = rail_score_sdk.get_monitor()
monitor.stats("chatbot-healthcare")
# -> {"total_evals": 342, "avg_score": 7.8, "regen_rate": 0.12, ...}
monitor.stats()
# -> global stats across all apps
```

---

### 3. Event schema — every event is a flat dict

**Eval event:**
```json
{
  "event": "eval",
  "timestamp": "2026-03-07T14:23:01.123Z",
  "app_id": "chatbot-healthcare",
  "session_id": "turn-47",
  "score": 7.5,
  "confidence": 0.82,
  "mode": "basic",
  "dimensions": {"safety": 9.0, "fairness": 6.8},
  "credits": 1.0,
  "latency_ms": 230,
  "cached": false
}
```

**Safe-regenerate event:**
```json
{
  "event": "safe_regenerate",
  "timestamp": "2026-03-07T14:23:04.456Z",
  "app_id": "chatbot-healthcare",
  "status": "passed",
  "iterations": 2,
  "before_score": 5.1,
  "after_score": 8.2,
  "credits": 5.0,
  "latency_ms": 12400
}
```

**Compliance event:**
```json
{
  "event": "compliance",
  "timestamp": "2026-03-07T14:25:00.789Z",
  "app_id": "content-mod",
  "framework": "gdpr",
  "score": 3.8,
  "requirements_passed": 2,
  "requirements_failed": 10,
  "credits": 5.0
}
```

**Error event:**
```json
{
  "event": "error",
  "timestamp": "2026-03-07T14:26:00.000Z",
  "app_id": "assistant-general",
  "error_type": "ContentTooHarmfulError",
  "status_code": 422,
  "credits": 1.0
}
```

---

### 4. Sinks are pluggable

```python
# Built-in sinks configured via init()
rail_score_sdk.init(
    api_key="rail_xxx",
    monitor={
        "console": True,                         # stderr
        "log_file": "rail.jsonl",                # file
        "on_event": my_async_callback,           # custom hook
    },
)

# Or add sinks programmatically after init
monitor = rail_score_sdk.get_monitor()
monitor.add_sink(LangfuseSink(public_key="..."))
monitor.add_sink(WebhookSink(url="https://..."))
```

---

### 5. How it attaches to clients — thin wrapper, not monkey-patching

Internally, `init()` stores a global `_config` and `_monitor`. The clients check for it:

```python
# Inside RailScoreClient.__init__:
class RailScoreClient:
    def __init__(self, api_key=None, app_id=None, ...):
        self.api_key = api_key or _global_config.api_key
        self.app_id = app_id or "default"
        self._monitor = _global_config.monitor  # can be None

# Inside RailScoreClient.eval:
    def eval(self, ...):
        t0 = time.monotonic()
        result = ...  # actual API call
        if self._monitor:
            self._monitor.emit({
                "event": "eval",
                "app_id": self.app_id,
                "score": result.rail_score.score,
                ...
            })
        return result
```

No magic. If there is no monitor, the overhead is a single `if None` check.

---

## File Structure for 2.3.0

```
rail_score_sdk/
├── __init__.py          # adds init(), get_monitor()
├── _config.py           # global config singleton
├── monitor.py           # RAILMonitor, EventBuffer, StatsAggregator
├── sinks/
│   ├── __init__.py
│   ├── console.py       # colored stderr output
│   ├── jsonl.py         # append-only file sink
│   └── callback.py      # async function sink
├── client.py            # emit events after each call
├── async_client.py      # emit events after each call
├── session.py           # emit events, register with SessionRegistry
└── ...
```

---

## Open Questions

- Should `init()` be a global singleton (like Sentry/Langfuse), or explicit `monitor=RAILMonitor()` passed to each client/session? Global is simpler for users but less flexible.
- Should the JSONL sink support log rotation (by size or time)?
- Should `StatsAggregator` expose a `/metrics`-style endpoint for Prometheus scraping?
- Should the session enhancement (native safe-regenerate in RAILSession) also ship in 2.3.0 or be deferred to 2.4.0?
