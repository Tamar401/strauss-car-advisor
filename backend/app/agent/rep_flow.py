"""תשובת נציג → עדכון הפרופיל → חישוב מחדש → הודעה בשיחה של העובד.

דטרמיניסטי לגמרי (בלי מודל שפה): הנציג נתן מספר, המנוע מחשב, וההודעה נבנית מתוצאת המנוע.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from google.genai import types

from app import seed
from app.agent.orchestrator import update_status
from app.agent.tools import run_comparison
from app.contracts import ChatMessage, RepQuestion, Tracked
from app.store import Store


def apply_rep_answer(q: RepQuestion, store: Store) -> None:
    record = store.get(q.conversation_id)
    if record is None or q.answer is None:
        return

    note = f"בתוקף מ-{q.answer.effective_from}" if q.answer.effective_from else None
    car_id = q.field.split(":", 1)[1] if q.field.startswith("participation:") else None
    comparison = None
    if car_id:
        value = float(q.answer.value)
        record.participations[car_id] = Tracked(value=value, source="rep", confirmed=True, note=note)
        car = next(c for c in seed.catalog() if c["id"] == car_id)
        answer_text = f"ההשתתפות שלך ב-{car['model']} היא {value:,.0f} ₪" + (f" ({note})" if note else "")
    else:
        answer_text = f"{q.answer.value}" + (f" ({note})" if note else "")

    lines = [f"עדכון מנציג התחבורה: {answer_text}."]
    if record.alternatives:
        comparison = run_comparison(record)
        updated = next((a for a in comparison.alternatives if a.option.car_id == car_id), None)
        if updated is not None:
            lines.append(updated.explanation)
        else:
            lines.append("עדכנתי את ההשוואה.")
    text = "\n".join(lines)

    record.state.messages.append(
        ChatMessage(id=uuid4().hex, role="assistant", text=text, created_at=datetime.now(timezone.utc), comparison=comparison)
    )
    # הסוכן צריך לדעת מה קרה, כדי להמשיך מאותה נקודה בהודעה הבאה של העובד
    record.history += [
        types.Content(role="user", parts=[types.Part(text=f"[הודעת מערכת: נציג התחבורה ענה — {answer_text}. ההשוואה עודכנה.]")]).model_dump(mode="json", exclude_none=True),
        types.Content(role="model", parts=[types.Part(text=text)]).model_dump(mode="json", exclude_none=True),
    ]
    store.save(record)  # קודם שומרים — update_status קורא את השאלות הפתוחות מה-DB
    update_status(record, store)
    store.save(record)
