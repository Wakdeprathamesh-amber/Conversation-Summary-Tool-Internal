import datetime
import re
from typing import List, Dict, Any

WHATSAPP_PATTERNS = re.compile(r"whatsapp|wa", re.IGNORECASE)
CALL_PATTERNS = re.compile(r"call|phone", re.IGNORECASE)
EMAIL_PATTERNS = re.compile(r"mail|email", re.IGNORECASE)
SUMMARY_PATTERNS = re.compile(r"summary", re.IGNORECASE)

# Helper to parse timestamps to datetime

def parse_timestamp(ts):
    if isinstance(ts, datetime.datetime):
        return ts
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M", "%B %d, %Y, %I:%M %p"):
        try:
            return datetime.datetime.strptime(ts, fmt)
        except Exception:
            continue
    return None

# Main consolidator

def consolidate_and_report(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    events = []
    for k, v in raw_data.items():
        if SUMMARY_PATTERNS.search(k):
            continue
        # WhatsApp
        if WHATSAPP_PATTERNS.search(k):
            if isinstance(v, list):
                for msg in v:
                    ts = msg.get("timestamp") or msg.get("created_at")
                    events.append({
                        "type": "whatsapp",
                        "timestamp": ts,
                        "content": msg.get("content", msg.get("message_content", "")),
                        "source": "whatsapp",
                        "raw": msg
                    })
            elif isinstance(v, dict):
                ts = v.get("timestamp") or v.get("created_at")
                events.append({
                    "type": "whatsapp",
                    "timestamp": ts,
                    "content": v.get("content", v.get("message_content", "")),
                    "source": "whatsapp",
                    "raw": v
                })
        # Calls
        elif CALL_PATTERNS.search(k):
            if isinstance(v, list):
                for call in v:
                    ts = call.get("timestamp") or call.get("created_at")
                    events.append({
                        "type": "call",
                        "timestamp": ts,
                        "content": call.get("content", call.get("message_content", call if isinstance(call, str) else "")),
                        "source": "call",
                        "raw": call
                    })
            elif isinstance(v, dict):
                ts = v.get("timestamp") or v.get("created_at")
                events.append({
                    "type": "call",
                    "timestamp": ts,
                    "content": v.get("content", v.get("message_content", v if isinstance(v, str) else "")),
                    "source": "call",
                    "raw": v
                })
            elif isinstance(v, str) and v.strip():
                events.append({
                    "type": "call",
                    "timestamp": None,
                    "content": v.strip(),
                    "source": "call",
                    "raw": v
                })
        # Email
        elif EMAIL_PATTERNS.search(k):
            if isinstance(v, list):
                for email in v:
                    ts = email.get("timestamp") or email.get("created_at")
                    events.append({
                        "type": "email",
                        "timestamp": ts,
                        "content": email.get("content", email.get("message_content", email if isinstance(email, str) else "")),
                        "source": "email",
                        "raw": email
                    })
            elif isinstance(v, dict):
                ts = v.get("timestamp") or v.get("created_at")
                events.append({
                    "type": "email",
                    "timestamp": ts,
                    "content": v.get("content", v.get("message_content", v if isinstance(v, str) else "")),
                    "source": "email",
                    "raw": v
                })
            elif isinstance(v, str) and v.strip():
                events.append({
                    "type": "email",
                    "timestamp": None,
                    "content": v.strip(),
                    "source": "email",
                    "raw": v
                })
    # Sort all events chronologically
    def event_sort_key(ev):
        ts = parse_timestamp(ev.get("timestamp", ""))
        return ts or datetime.datetime.min
    events = sorted(events, key=event_sort_key)

    # Pack consecutive WhatsApp messages as a single session until the medium changes
    timeline = []
    whatsapp_pack = []
    def flush_whatsapp_pack():
        if whatsapp_pack:
            session_start = whatsapp_pack[0].get("timestamp")
            content = "\n".join([m.get("content", "") for m in whatsapp_pack])
            timeline.append({
                "type": "whatsapp_pack",
                "timestamp": session_start,
                "content": content,
                "source": "whatsapp",
                "count": len(whatsapp_pack),
                "raw": [m["raw"] for m in whatsapp_pack]
            })
            whatsapp_pack.clear()
    for ev in events:
        if ev["type"] == "whatsapp":
            whatsapp_pack.append(ev)
        else:
            flush_whatsapp_pack()
            timeline.append({
                "type": ev["type"],
                "timestamp": ev.get("timestamp"),
                "content": ev.get("content", ""),
                "source": ev.get("source", ""),
                "raw": ev.get("raw")
            })
    flush_whatsapp_pack()

    # Count totals
    total_calls = sum(1 for ev in timeline if ev["type"] == "call")
    total_emails = sum(1 for ev in timeline if ev["type"] == "email")
    total_whatsapp_packs = sum(1 for ev in timeline if ev["type"] == "whatsapp_pack")

    # Preprocess for LLM: build llm_timeline with rich content, no raw
    llm_timeline = []
    llm_lines = []
    for ev in timeline:
        rich_content = ev.get("content", "")
        channel = ev["type"].replace("_pack", "").upper()
        ts = ev.get("timestamp") or ""
        # For emails, try to extract subject, snippet, and body from raw
        if ev["type"] == "email" and ev.get("raw"):
            raw = ev["raw"]
            subject = raw.get("subject", "") if isinstance(raw, dict) else ""
            snippet = raw.get("snippet", "") if isinstance(raw, dict) else ""
            body = ""
            if isinstance(raw, dict):
                raw_data = raw.get("raw_data")
                if raw_data:
                    try:
                        import json as _json
                        if isinstance(raw_data, str):
                            parsed = _json.loads(raw_data)
                            body = parsed.get("content", "") or parsed.get("snippet", "")
                            if not snippet:
                                snippet = parsed.get("snippet", "")
                        elif isinstance(raw_data, dict):
                            body = raw_data.get("content", "") or raw_data.get("snippet", "")
                            if not snippet:
                                snippet = raw_data.get("snippet", "")
                    except Exception:
                        if isinstance(raw_data, str):
                            body = raw_data
                elif raw.get("raw_data") and not body:
                    body = str(raw.get("raw_data"))
            rich_content = "\n".join([x for x in [subject, snippet, body] if x])
        elif ev["type"] == "whatsapp_pack" and ev.get("raw"):
            msgs = ev["raw"]
            if isinstance(msgs, list):
                rich_content = "\n".join([m.get("message_content", m.get("content", "")) for m in msgs if isinstance(m, dict)])
        elif ev["type"] == "call" and ev.get("raw"):
            raw = ev["raw"]
            if isinstance(raw, dict):
                rich_content = raw.get("transcription", raw.get("content", ""))
            elif isinstance(raw, str):
                rich_content = raw
        llm_timeline.append({
            k: v for k, v in ev.items() if k not in ("raw",)
        } | {"content": rich_content})
        # Compose minimal metadata line
        line = f"[{ts}] [{channel}] {rich_content}".strip()
        llm_lines.append(line)
    llm_text = "\n".join(llm_lines)

    return {
        "timeline": timeline,         # full, with raw, for incremental logic
        "llm_timeline": llm_timeline, # content-rich, for LLM input (if needed)
        "llm_text": llm_text,         # minimal metadata, content-rich, for LLM summarization
        "counts": {
            "calls": total_calls,
            "emails": total_emails,
            "whatsapp_packs": total_whatsapp_packs
        }
    } 