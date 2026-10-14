"""POST /api/compare — בעלות: מפתחת א'.

כרגע מחזיר תשובה מדומה (עובדת E-001, המספרים אמיתיים ונבדקו מול נטו הייחוס).
כשהמנוע מוכן: מחליפים את גוף הפונקציה בקריאה ל-engine.compare(req) — החוזה לא משתנה.
"""
from fastapi import APIRouter

from app import seed
from app.contracts import CompareRequest, CompareResponse

router = APIRouter(prefix="/api", tags=["compare"])


@router.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest):
    return seed.mock("compare_E-001.json")
