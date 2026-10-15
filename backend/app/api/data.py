"""נתוני עזר: קטלוג, עיסוקים, עובדים לדוגמה (קורא מה-seed). הכללים — ב-api/rules.py."""
from fastapi import APIRouter

from app import seed
from app.contracts import Car, Occupation

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/catalog", response_model=list[Car])
def get_catalog():
    return seed.catalog()


@router.get("/occupations", response_model=list[Occupation])
def get_occupations():
    return seed.occupations()


@router.get("/demo-employees")
def get_demo_employees():
    """6 העובדים לדוגמה — לכפתורי "מלא נתוני דמו" בהדגמה. בלי ת״ז."""
    return [{k: v for k, v in e.items() if k != "national_id"} for e in seed.employees()]
