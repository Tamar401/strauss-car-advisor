"""/api/rep — תור השאלות לנציג. בעלות: מפתחת א'.

כרגע: זיכרון בתהליך עם שאלה אחת לדוגמה.
להחליף ב: טבלת rep_questions ב-SQLite; מענה → עדכון הפרופיל בשיחה (source='rep') → חישוב מחדש.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.contracts import RepAnswer, RepQuestion

router = APIRouter(prefix="/api/rep", tags=["rep"])

_questions: dict[str, RepQuestion] = {
    "q-demo-1": RepQuestion(
        id="q-demo-1",
        conversation_id="demo",
        employee_display_name="נועה לוי",
        field="participation:CAR-13",
        question_text="מה גובה ההשתתפות החודשית של העובדת ב-MAZDA 3 (2025)?",
        context="קבוצה ג · רכב היום: COROLLA CROSS (השתתפות 300 ₪) · מבוקש: MAZDA 3",
        status="open",
        created_at=datetime.now(timezone.utc),
    )
}


@router.get("/questions", response_model=list[RepQuestion])
def list_questions(status: str | None = None):
    qs = sorted(_questions.values(), key=lambda q: q.created_at, reverse=True)
    return [q for q in qs if status is None or q.status == status]


@router.post("/questions/{question_id}/answer", response_model=RepQuestion)
def answer_question(question_id: str, answer: RepAnswer):
    q = _questions.get(question_id)
    if q is None:
        raise HTTPException(404, "שאלה לא נמצאה")
    q.answer = answer
    q.status = "answered"
    q.answered_at = datetime.now(timezone.utc)
    return q
