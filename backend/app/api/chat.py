"""/api/chat ו-/api/conversations — השיחה עם הסוכן. בעלות: מפתחת ב'."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import seed
from app.agent.orchestrator import handle_message
from app.agent.tools import missing_profile_fields
from app.contracts import ChatMessage, ChatRequest, CompareRequest, ConversationState, EmployeeProfile
from app.engine.compare import FIELD_NAMES, all_options, compare, demo_profile
from app.store import ConversationRecord, get_store

router = APIRouter(prefix="/api", tags=["chat"])


def _get(conversation_id: str) -> ConversationRecord:
    record = get_store().get(conversation_id)
    if record is None:
        raise HTTPException(404, "שיחה לא נמצאה")
    return record


@router.post("/chat", response_model=ConversationState)
def chat(req: ChatRequest):
    store = get_store()
    if not req.message.strip():
        raise HTTPException(400, "הודעה ריקה")
    if req.conversation_id is None:
        record = ConversationRecord(
            state=ConversationState(conversation_id=uuid4().hex, status="collecting", messages=[], profile=EmployeeProfile())
        )
    else:
        record = _get(req.conversation_id)
    record = handle_message(record, req.message.strip()[:2000], store)
    store.save(record)
    return record.state


@router.get("/conversations/{conversation_id}", response_model=ConversationState)
def get_conversation(conversation_id: str):
    return _get(conversation_id).state


@router.post("/conversations/{conversation_id}/explore", response_model=ConversationState)
def explore_all_options(conversation_id: str):
    """כל החלופות בבת אחת, מהמשתלמת ביותר. דטרמיניסטי — בלי מודל שפה, בלי מכסה."""
    store = get_store()
    record = _get(conversation_id)
    missing = missing_profile_fields(record)
    if missing:
        names = ", ".join(FIELD_NAMES.get(m, m) for m in missing)
        raise HTTPException(409, f"כדי להציג את כל האפשרויות חסר לי עוד: {names}")

    # השתתפות ידועה (מהעובד / מהנציג) — משתמשים בה; אחרת ברירת המחדל מהקטלוג, ומסומנת ככזו בכרטיס.
    # לא נוגעים ב-record.alternatives: הסקירה לא מחליפה את החלופות שהשיחה עוקבת אחריהן.
    options = [
        o.model_copy(update={"participation": record.participations.get(o.car_id)}) if o.kind == "car" else o
        for o in all_options(record.state.profile)
    ]
    comparison = compare(CompareRequest(profile=record.state.profile, alternatives=options))
    comparison.alternatives.sort(key=lambda a: ({"complete": 0, "partial": 1, "blocked": 2}[a.status], -(a.delta_net or 0)))
    record.state.last_comparison = comparison

    available = [a for a in comparison.alternatives if a.status == "complete"]
    blocked = sum(a.status == "blocked" for a in comparison.alternatives)
    if available:
        best = available[0]
        text = (
            f"הנה כל האפשרויות שלך ({len(available)} זמינות), מהמשתלמת ביותר.\n"
            f"הכי משתלמת: {best.label} — {best.explanation.splitlines()[0]}"
        )
    else:
        text = "בדקתי את כל האפשרויות, ואף אחת מהן לא זמינה לך כרגע."
    if blocked:
        text += f"\n{blocked} אפשרויות לא זמינות לך, וגם הן מופיעות עם הסיבה."
    text += "\nבחלופות שלא שאלנו עליהן, ההשתתפות היא ברירת המחדל מהקטלוג (מסומן בכל כרטיס)."

    record.state.messages.append(
        ChatMessage(id=uuid4().hex, role="assistant", text=text, created_at=datetime.now(timezone.utc), comparison=comparison)
    )
    store.save(record)
    return record.state


@router.post("/conversations/{conversation_id}/demo/{employee_id}", response_model=ConversationState)
def load_demo_employee(conversation_id: str, employee_id: str):
    """ממלא את הפרופיל מאחד העובדים לדוגמה — כדי להדגים בלי להקליד את כל הנתונים."""
    store = get_store()
    employee = next((e for e in seed.employees() if e["id"] == employee_id), None)
    if employee is None:
        raise HTTPException(404, "עובד לדוגמה לא נמצא")
    record = store.get(conversation_id) if conversation_id != "new" else None
    if record is None:
        record = ConversationRecord(
            state=ConversationState(conversation_id=uuid4().hex, status="collecting", messages=[], profile=EmployeeProfile())
        )
    record.state.profile = demo_profile(employee)
    record.state.employee_display_name = employee["name"].split()[0]
    record.state.messages.append(ChatMessage(
        id=uuid4().hex,
        role="system",
        text=f"נטענו נתוני הדמו של {employee['name']} ({employee['occupation']}). אפשר לשאול: {employee['question']}",
        created_at=datetime.now(timezone.utc),
    ))
    store.save(record)
    return record.state
