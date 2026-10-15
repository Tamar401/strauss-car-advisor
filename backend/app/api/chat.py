"""/api/chat ו-/api/conversations — השיחה עם הסוכן. בעלות: מפתחת ב'."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import seed
from app.agent.orchestrator import handle_message
from app.contracts import ChatMessage, ChatRequest, ConversationState, EmployeeProfile
from app.engine.compare import demo_profile
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
