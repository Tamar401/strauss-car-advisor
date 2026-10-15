"""Number Guard: כל מספר בתשובת הבוט חייב להגיע ממקור מאומת.

מקורות מאומתים: הפרופיל (מה שהעובד מסר), תוצאות ההשוואה וה-trace, קובץ הכללים, הקטלוג,
טבלת העיסוקים, ומה שהעובד עצמו כתב. מספר שלא מופיע באף אחד מהם = המודל המציא אותו → חסימה.
"""
from __future__ import annotations

import re

from app import seed
from app.contracts import CompareResponse, OptionResult
from app.engine.rules import Rules
from app.store import ConversationRecord

NUMBER = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
SMALL_INTEGERS = set(range(0, 13))  # ספירות, מספרי דגמים (MG4, EV3), "שתי שורות" וכו'
YEARS = set(range(2020, 2031))
TOLERANCE = 1.0  # עיגול לשקל בתצוגה


def numbers_in(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in NUMBER.findall(text)]


def _result_numbers(r: OptionResult) -> set[float]:
    values = {
        r.budget, r.monthly_cost, r.employee_participation, r.family_gap_employee, r.value_of_use,
        r.electric_bonus_gross, r.maintenance, r.gross, r.taxable_income, r.income_tax,
        r.national_insurance, r.health_tax, r.pension_employee, r.study_fund_employee, r.net,
        r.delta_net, r.delta_display,
    }
    values |= {t.amount for t in r.trace}
    values |= {s.amount for s in r.waterfall}
    if r.national_insurance is not None and r.health_tax is not None:
        values.add(r.national_insurance + r.health_tax)
    values |= set(numbers_in(r.explanation)) | set(numbers_in(r.eligibility.reason_text))
    return {abs(v) for v in values if v is not None}


def allowed_numbers(record: ConversationRecord, rules: Rules, comparisons: list[CompareResponse]) -> set[float]:
    allowed: set[float] = set(SMALL_INTEGERS) | YEARS
    p = record.state.profile
    for name in ("base_salary", "commissions", "bonus", "pension_pct", "study_fund_pct", "credit_points", "children_under_23"):
        value = getattr(p, name).value
        if value is not None:
            allowed.add(float(value))
    for t in record.participations.values():
        if t.value is not None:
            allowed.add(float(t.value))
    for comparison in comparisons:
        for r in [comparison.current, *comparison.alternatives]:
            allowed |= _result_numbers(r)
    allowed |= set(rules.budgets.values())
    allowed |= {rules.electric.net_bonus, rules.family_track.min_children, rules.family_track.child_max_age}
    allowed |= {rules.family_track.gap_split_employee * 100}
    for c in seed.catalog():
        allowed |= {c["monthly_cost"], c["default_participation"], c["value_of_use"], c["list_price"]}
    allowed |= {o["waiver_maintenance"] for o in seed.occupations()}
    for m in record.state.messages:  # מה שהעובד והנציג כתבו
        if m.role in ("user", "system"):
            allowed |= set(numbers_in(m.text))
    return allowed


def check(text: str, allowed: set[float]) -> list[float]:
    """מחזיר את המספרים שאין להם מקור. רשימה ריקה = התשובה עברה."""
    return [n for n in numbers_in(text) if not any(abs(n - a) <= TOLERANCE for a in allowed)]
