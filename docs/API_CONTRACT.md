# 📜 Scam Court AI — API Contract v1.0.0

> Stable JSON schema for external consumers: Gradio UI, Chrome extensions, WhatsApp Web, Gmail, and third-party integrations.

---

## Overview

The `CourtroomReport` object is the single source of truth for every analysis. It is produced by `CourtroomEngine.analyze(text)` and serialized via `report.to_dict()` or `report.to_json()`.

**Version:** `1.0.0`  
**Content-Type:** `application/json`  
**Encoding:** UTF-8  

---

## Top-Level Schema

```json
{
  "version": "1.0.0",
  "input": { ... },
  "analysis": { ... },
  "court": { ... },
  "trace": { ... }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version. Follows SemVer. |
| `input` | object | Sanitized input metadata. |
| `analysis` | object | Core risk assessment. |
| `court` | object | Per-role outputs (detective, prosecutor, defender, judge, clerk). |
| `trace` | object | Execution trace for observability and debugging. |

---

## 1. Input Block

```json
{
  "input": {
    "raw_text": "Hi honey, it's Mom...",
    "source": "user_paste"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `raw_text` | string | Sanitized user input (HTML-escaped, truncated to 4000 chars). |
| `source` | string | Origin hint: `user_paste`, `chrome_extension`, `whatsapp_web`, `gmail`, etc. |

---

## 2. Analysis Block

```json
{
  "analysis": {
    "risk_score": 88,
    "risk_level": "critical",
    "verdict": "SCAM"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `risk_score` | integer | 0–100 risk score. Higher = more dangerous. |
| `risk_level` | string | `critical` (80+), `high` (50–79), `medium` (20–49), `low` (0–19). |
| `verdict` | string | `SCAM`, `SUSPICIOUS`, `CAUTION`, or `LIKELY SAFE`. |

**Risk Level Mapping**

| Score Range | Level | Verdict Likelihood |
|-------------|-------|-------------------|
| 80–100 | `critical` | `SCAM` |
| 50–79 | `high` | `SUSPICIOUS` |
| 20–49 | `medium` | `CAUTION` |
| 0–19 | `low` | `LIKELY SAFE` |

---

## 3. Court Block

The `court` object contains one entry per persona. Each entry is self-describing and safe to render directly in a UI.

### Detective

```json
{
  "detective": {
    "role": "detective",
    "title": "Detective Evidence Board",
    "evidence": [
      "Creates false urgency",
      "Impersonates a family member",
      "Requests payment or money transfer"
    ]
  }
}
```

### Prosecutor

```json
{
  "prosecutor": {
    "role": "prosecutor",
    "title": "Prosecutor Argument",
    "argument": "Your Honor, the prosecution presents..."
  }
}
```

### Defender

```json
{
  "defender": {
    "role": "defender",
    "title": "Defender Argument",
    "argument": "Your Honor, the defense respectfully disagrees..."
  }
}
```

### Judge

```json
{
  "judge": {
    "role": "judge",
    "title": "Judge Verdict",
    "verdict": "SCAM",
    "rationale": "The evidence is overwhelming...",
    "risk_score": 88
  }
}
```

### Clerk

```json
{
  "clerk": {
    "role": "clerk",
    "title": "Safety Clerk",
    "safe_reply": "Do not reply. Do not click links...",
    "next_steps": [
      "Forward the message to your carrier...",
      "Report to the FTC..."
    ]
  }
}
```

---

## 4. Trace Block

```json
{
  "trace": {
    "engine_version": "heuristic_v1",
    "agents": [
      {
        "agent": "detective",
        "latency_ms": 12,
        "output": { "evidence": ["..."] }
      },
      {
        "agent": "judge",
        "latency_ms": 5,
        "output": {
          "verdict": "SCAM",
          "risk_score": 88,
          "rationale": "..."
        }
      }
    ],
    "flags_triggered": ["urgency", "impersonation_family", "payment_request"],
    "personas_used": ["detective", "prosecutor", "defender", "judge", "clerk"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `engine_version` | string | Backend identifier (e.g., `heuristic_v1`, `smollm3-3b_v1`). |
| `agents` | array | Ordered list of agent executions with latency and raw output. |
| `flags_triggered` | string[] | Keys of heuristic patterns that matched. |
| `personas_used` | string[] | Ordered list of personas consulted. |

---

## Backward Compatibility

`CourtroomReport` exposes read-only properties for legacy flat-field access:

```python
report.risk_score          # → analysis["risk_score"]
report.judge_verdict       # → analysis["verdict"]
report.judge_rationale     # → court["judge"]["rationale"]
report.detective_evidence  # → court["detective"]["evidence"]
report.prosecutor_argument # → court["prosecutor"]["argument"]
report.defender_argument   # → court["defender"]["argument"]
report.clerk_safe_reply    # → court["clerk"]["safe_reply"]
report.clerk_next_steps    # → court["clerk"]["next_steps"]
```

Existing UI code (e.g., `app.py`) can continue using these properties without modification.

---

## Integration Checklist

| Consumer | Required Fields | Notes |
|----------|----------------|-------|
| Gradio UI | `analysis`, `court` | Use backward-compatible properties. |
| Chrome Extension | `analysis`, `court.clerk` | Render verdict badge + safe reply. |
| WhatsApp Web | `analysis`, `court.detective` | Overlay red flags on selected text. |
| Gmail | `analysis`, `court.judge` | Sidebar verdict card. |
| External API | Full schema | `trace` aids debugging and audit. |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-05 | Initial stable contract. Nested `court` and `trace` blocks. `risk_level` introduced. |
