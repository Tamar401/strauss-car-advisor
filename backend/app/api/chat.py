"""/api/chat ו-/api/conversations — בעלות: מפתחת ב'.

כרגע: בוט מדומה עם זיכרון בתהליך, כדי שהממשק יעבוד מול החוזה.
להחליף ב: orchestrator של Gemini + שמירה ב-SQLite (המצב חייב לשרוד רענון וגם הפעלה מחדש של השרת).
"""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app import seed
from app.contracts import ChatMessage, ChatRequest, CompareResponse, ConversationState, EmployeeProfile

router = APIRouter(prefix="/api", tags=["chat"])

_conversations: dict[str, ConversationState] = {}


def _now():
    return datetime.now(timezone.utc)


def _msg(role, text, comparison=None):
    return ChatMessage(id=uuid4().hex, role=role, text=text, created_at=_now(), comparison=comparison)


@router.post("/chat", response_model=ConversationState)
def chat(req: ChatRequest):
    if req.conversation_id is None:
        conv = ConversationState(
            conversation_id=uuid4().hex,
            status="collecting",
            messages=[],
            profile=EmployeeProfile(),
        )
        _conversations[conv.conversation_id] = conv
    else:
        conv = _conversations.get(req.conversation_id)
        if conv is None:
            raise HTTPException(404, "שיחה לא נמצאה")

    conv.messages.append(_msg("user", req.message))

    # תסריט מדומה: הודעה ראשונה → שאלת פתיחה; כל הודעה אחרת → השוואה לדוגמה
    if len(conv.messages) == 1:
        conv.messages.append(_msg("assistant", "בכיף! נתחיל מהבסיס: באיזו קבוצת זכאות את/ה (א-ד), ומה שכר הבסיס החודשי שלך?"))
    else:
        comparison = CompareResponse.model_validate(seed.mock("compare_E-001.json"))
        conv.last_comparison = comparison
        conv.status = "ready"
        conv.messages.append(_msg(
            "assistant",
            "הנה ההשוואה (נתוני דמו): מעבר ל-ATTO 3 מעלה את הנטו ב-661 ₪ בחודש.",
            comparison=comparison,
        ))
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationState)
def get_conversation(conversation_id: str):
    conv = _conversations.get(conversation_id)
    if conv is None:
        raise HTTPException(404, "שיחה לא נמצאה")
    return conv
