# 📜 Scam Court AI — Integration Contract v2.0.0

> Stable JSON contract for external consumers: Gradio UI, Chrome extensions, WhatsApp Web, Gmail, customer-support workflows, and agent-trace sharing.

---

## Schema Overview

Every analysis produces a single `CourtroomReport` object serialized as JSON. The schema is versioned (`schema_version: "2.0.0"`) and self-describing.

```json
{
  "report_id": "scr-aB3dEf4g",
  "created_at": "2026-06-05T14:30:00+00:00",
  "schema_version": "2.0.0",
  "input_text": "URGENT: verify your account...",
  "risk_score": 72,
  "risk_level": "high",
  "verdict": "SUSPICIOUS",
  "confidence": 0.77,
  "detected_patterns": [...],
  "evidence_items": [...],
  "detective_report": {...},
  "prosecutor_argument": "...",
  "defender_argument": "...",
  "judge_summary": {...},
  "safety_reply": "...",
  "next_steps": [...],
  "recommended_action": "verify_independently",
  "user_profile": null,
  "agent_trace": {...},
  "model_backend": "heuristic_v1",
  "limitations": [...]
}
```

---

## Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `report_id` | string | Unique identifier (`scr-{urlsafe}`). |
| `created_at` | string | ISO 8601 timestamp in UTC. |
| `schema_version` | string | Contract version (`2.0.0`). |
| `input_text` | string | Sanitized user input (≤4000 chars, HTML-escaped). |
| `risk_score` | integer | 0–100 risk score. |
| `risk_level` | string | `critical` \| `high` \| `medium` \| `low`. |
| `verdict` | string | `SCAM` \| `SUSPICIOUS` \| `CAUTION` \| `LIKELY SAFE`. |
| `confidence` | float | 0.25–0.97 heuristic confidence derived from score. |
| `detected_patterns` | array | Structured list of matched heuristic patterns. |
| `evidence_items` | array | Alias of `detected_patterns` for UI framing. |
| `detective_report` | object | Evidence board with role metadata. |
| `prosecutor_argument` | string | Manipulation-tactics explanation. |
| `defender_argument` | string | Devil's-advocate legitimacy check. |
| `judge_summary` | object | Verdict + rationale + score. |
| `safety_reply` | string | Safe message the user can send or ignore. |
| `next_steps` | array | Ordered actionable guidance. |
| `recommended_action` | string | Machine-readable action code (see below). |
| `user_profile` | object \| null | Reserved for future per-user calibration. |
| `agent_trace` | object | Full execution trace with per-agent latency. |
| `model_backend` | string | Backend identifier (`heuristic_v1`, `smollm3-3b_v1`, etc.). |
| `limitations` | array | Known caveats for this backend. |

---

## Pattern Object

```json
{
  "id": "urgency",
  "label": "Creates false urgency",
  "category": "manipulation",
  "severity": "medium",
  "weight": 15
}
```

**Categories:** `manipulation`, `impersonation`, `theft`, `financial`, `technical`.  
**Severities:** `low` (weight < 15), `medium` (15–19), `high` (≥ 20).

---

## Recommended Actions

| Action Code | Score Range | Human Meaning |
|-------------|-------------|---------------|
| `block_and_report` | 80–100 | Treat as confirmed scam. Block sender and report. |
| `verify_independently` | 50–79 | Do not act via message. Verify through trusted channel. |
| `pause_and_verify` | 20–49 | Slow down. Check sender identity before proceeding. |
| `standard_caution` | 0–19 | No strong concern. Maintain normal security habits. |

---

## Integration Examples

### 1. Gradio Space

```python
from courtroom import CourtroomEngine

engine = CourtroomEngine()
report = engine.analyze("Your car warranty is expiring...")

# Render in UI
print(report.verdict)           # "SCAM"
print(report.risk_score)        # 88
print(report.safety_reply)      # actionable guidance

# Export for sharing
json_payload = report.to_json()
```

### 2. Chrome Extension — Right-Click Selected Text

```javascript
// content.js — user highlights text and right-clicks
const selected = window.getSelection().toString();

fetch('http://localhost:7860/api/analyze', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({text: selected, source: 'chrome_extension'})
})
.then(r => r.json())
.then(report => {
  // Mini overlay
  showBadge(report.risk_score, report.verdict);
  showSafeReply(report.safety_reply);
});
```

**Privacy rule:** The extension only sends text the user has *actively selected*. No background scanning, no DOM watchers, no clipboard access.

### 3. Customer Support / Family Safety Workflow

```python
# Batch monitor a family member's forwarded messages
from courtroom import CourtroomEngine

engine = CourtroomEngine()

for msg in family_member_forwarded_messages:
    report = engine.analyze(msg)
    if report.risk_level in ("critical", "high"):
        alert_caregiver(
            report_id=report.report_id,
            verdict=report.verdict,
            safe_reply=report.safety_reply,
            next_steps=report.next_steps,
        )
    # Store for audit
    save_to_family_safety_log(report.to_dict())
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-06-05 | Flat integration contract. Added `report_id`, `created_at`, `confidence`, `detected_patterns`, `recommended_action`, `user_profile`, `limitations`. |
| 1.0.0 | 2026-06-05 | Initial nested schema (`input`, `analysis`, `court`, `trace`). |
