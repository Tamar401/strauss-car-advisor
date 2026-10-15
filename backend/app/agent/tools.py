"""הכלים של הסוכן. כל כלי מקבל את רשומת השיחה, מאמת את הקלט, ומחזיר dict קטן שהמודל קורא.

עיקרון: הכלים הם המקום היחיד שבו נכנס מידע לפרופיל ומספרים לשיחה. המודל רק בוחר איזה כלי להפעיל.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app import seed
from app.contracts import CompareRequest, CompareResponse, OptionRequest, RepQuestion, Tracked
from app.engine.compare import DRIVE_LABELS, compare
from app.engine.eligibility import check_car
from app.engine.rules import load_rules
from app.store import ConversationRecord, Store

PROFILE_NUMBERS = ["base_salary", "commissions", "bonus", "pension_pct", "study_fund_pct", "credit_points"]

TOOL_SPECS = [
    {
        "name": "update_profile",
        "description": "שמירת נתונים שהעובד מסר במפורש. לקרוא מיד כשהעובד אומר נתון. לעולם לא להמציא ערך.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "שם פרטי של העובד, אם אמר"},
                "occupation": {"type": "string", "description": "שם העיסוק בדיוק כמו ברשימת העיסוקים"},
                "group": {"type": "string", "enum": ["א", "ב", "ג", "ד"], "description": "רק אם העיסוק לא ידוע"},
                "base_salary": {"type": "number", "description": "שכר בסיס חודשי ברוטו בש״ח"},
                "commissions": {"type": "number", "description": "עמלות חודשיות בש״ח (0 אם אין)"},
                "bonus": {"type": "number", "description": "בונוס חודשי בש״ח (0 אם אין)"},
                "pension_pct": {"type": "number", "description": "אחוז הפרשת העובד לפנסיה, למשל 6"},
                "study_fund_pct": {"type": "number", "description": "אחוז הפרשת העובד לקרן השתלמות, למשל 2.5 (0 אם אין)"},
                "credit_points": {"type": "number", "description": "נקודות זיכוי, למשל 2.25"},
                "children_under_23": {"type": "integer", "description": "מספר הילדים עד גיל 23"},
            },
        },
    },
    {
        "name": "set_current_situation",
        "description": "מה יש לעובד היום: רכב מהקטלוג (car_id) והשתתפותו בו, או ויתור (אחזקת רכב).",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["car", "waiver"]},
                "car_id": {"type": "string", "description": "מזהה מהקטלוג, למשל CAR-09. רק כש-kind=car"},
                "participation": {"type": "number", "description": "השתתפות חודשית היום בש״ח, כפי שהעובד אמר"},
            },
            "required": ["kind"],
        },
    },
    {
        "name": "list_catalog",
        "description": "קטלוג הרכבים עם זכאות לפי הפרופיל. לחפש כאן את car_id לפי שם הדגם שהעובד אמר.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "compare_options",
        "description": (
            "מריץ את מנוע החישוב: נטו היום מול כל חלופה. כל המספרים שמותר להגיד לעובד מגיעים מכאן. "
            "participation: מה שהעובד אמר על ההשתתפות ברכב החדש; null אם לא ידוע (ואז לשאול את הנציג עם ask_rep)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "kind": {"type": "string", "enum": ["car", "waiver"]},
                            "car_id": {"type": "string"},
                            "participation": {"type": ["number", "null"]},
                        },
                        "required": ["kind"],
                    },
                }
            },
            "required": ["options"],
        },
    },
    {
        "name": "ask_rep",
        "description": (
            "שליחת שאלה לנציג התחבורה כשחסר מידע שהעובד לא יודע (בעיקר השתתפות ברכב חדש). "
            "מחזיר גם השוואה חלקית לבינתיים (comparison_meanwhile): הנטו היום, והחלופה תתעדכן כשהנציג יענה."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "car_id": {"type": "string", "description": "הרכב שעליו השאלה, אם רלוונטי"},
                "question_text": {"type": "string", "description": "השאלה לנציג, בעברית"},
            },
            "required": ["question_text"],
        },
    },
]


class ToolError(Exception):
    pass


def _catalog() -> dict[str, dict]:
    return {c["id"]: c for c in seed.catalog()}


def _occupations() -> dict[str, dict]:
    return {o["name"]: o for o in seed.occupations()}


def _tracked(value):
    return Tracked(value=value, source="employee", confirmed=True)


def update_profile(record: ConversationRecord, store: Store, **fields) -> dict:
    profile = record.state.profile
    saved = {}
    if fields.get("name"):
        record.state.employee_display_name = str(fields.pop("name")).strip()[:40]
        saved["name"] = record.state.employee_display_name
    if "occupation" in fields:
        name = fields.pop("occupation")
        if name not in _occupations():
            raise ToolError(f"עיסוק לא מוכר: {name}. העיסוקים האפשריים: {', '.join(_occupations())}")
        profile.occupation = _tracked(name)
        saved["occupation"] = name
        saved["group_from_occupation"] = _occupations()[name]["group"]
    if "group" in fields:
        profile.group = _tracked(fields.pop("group"))
        saved["group"] = profile.group.value
    if "children_under_23" in fields:
        children = int(fields.pop("children_under_23"))
        if children < 0:
            raise ToolError("מספר ילדים לא יכול להיות שלילי")
        profile.children_under_23 = _tracked(children)
        saved["children_under_23"] = children
    for name in PROFILE_NUMBERS:
        if name in fields:
            value = float(fields.pop(name))
            if value < 0 or (name.endswith("_pct") and value > 30):
                raise ToolError(f"ערך לא סביר ל-{name}: {value}")
            setattr(profile, name, _tracked(value))
            saved[name] = value
    return {"saved": saved, "still_missing": missing_profile_fields(record)}


def set_current_situation(record: ConversationRecord, store: Store, kind: str, car_id: str | None = None, participation: float | None = None) -> dict:
    if kind == "waiver":
        option = OptionRequest(kind="waiver")
    else:
        if car_id not in _catalog():
            raise ToolError(f"רכב לא מוכר בקטלוג: {car_id}. לחפש עם list_catalog")
        option = OptionRequest(
            kind="car",
            car_id=car_id,
            participation=_tracked(participation) if participation is not None else Tracked(source="missing"),
        )
    record.state.profile.current_option = _tracked(option)
    return {"saved": option.model_dump(exclude_none=True), "still_missing": missing_profile_fields(record)}


def list_catalog(record: ConversationRecord, store: Store) -> dict:
    rules = load_rules()
    profile = record.state.profile
    occupation = _occupations().get(profile.occupation.value) if profile.occupation.value else None
    group = occupation["group"] if occupation else profile.group.value
    children = profile.children_under_23.value
    cars = []
    for c in seed.catalog():
        elig = check_car(c, group, children, rules)
        cars.append({
            "car_id": c["id"],
            "name": f"{c['manufacturer']} {c['model']} ({c['registration_year']})",
            "drive": DRIVE_LABELS[c["drive"]],
            "group": c["group"],
            "eligible": None if elig.eligibility is None else elig.eligibility.eligible,
        })
    return {"employee_group": group, "cars": cars}


def compare_options(record: ConversationRecord, store: Store, options: list[dict]) -> dict:
    current = record.state.profile.current_option.value
    alternatives = []
    for o in options:
        if o.get("kind") == "car":
            car_id = o.get("car_id")
            if car_id not in _catalog():
                raise ToolError(f"רכב לא מוכר בקטלוג: {car_id}")
            if current and current.kind == "car" and current.car_id == car_id:
                continue  # המצב היום הוא נקודת ההשוואה, לא חלופה
            if o.get("participation") is not None:
                record.participations[car_id] = _tracked(float(o["participation"]))
            alternatives.append(OptionRequest(kind="car", car_id=car_id))
        elif not (current and current.kind == "waiver"):
            alternatives.append(OptionRequest(kind="waiver"))
    record.alternatives = alternatives
    resp = run_comparison(record)
    return summarize(resp)


def ask_rep(record: ConversationRecord, store: Store, question_text: str, car_id: str | None = None) -> dict:
    field = f"participation:{car_id}" if car_id else "other"
    for q in store.questions(conversation_id=record.state.conversation_id, status="open"):
        if q.field == field:
            return {"already_open": True, "question_id": q.id}
    catalog = _catalog()
    profile = record.state.profile
    current = profile.current_option.value
    current_text = "ויתור" if current and current.kind == "waiver" else (catalog[current.car_id]["model"] if current else "לא ידוע")
    group = profile.group.value
    if profile.occupation.value:
        group = _occupations()[profile.occupation.value]["group"]
    context = f"קבוצה {group or '?'} · היום: {current_text}"
    if car_id in catalog:
        context += f" · מבוקש: {catalog[car_id]['model']} ({catalog[car_id]['registration_year']})"
    q = RepQuestion(
        id=uuid4().hex[:10],
        conversation_id=record.state.conversation_id,
        employee_display_name=record.state.employee_display_name or "עובד/ת",
        field=field,
        question_text=question_text,
        context=context,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    store.save_question(q)
    record.state.status = "waiting_for_rep"
    result = {"sent": True, "question_id": q.id}
    # בינתיים: השוואה חלקית — המצב היום מחושב, והחלופה תתעדכן כשהנציג יענה
    if car_id in catalog and not any(a.car_id == car_id for a in record.alternatives):
        record.alternatives.append(OptionRequest(kind="car", car_id=car_id))
    if record.alternatives:
        result["comparison_meanwhile"] = summarize(run_comparison(record))
    return result


TOOLS = {
    "update_profile": update_profile,
    "set_current_situation": set_current_situation,
    "list_catalog": list_catalog,
    "compare_options": compare_options,
    "ask_rep": ask_rep,
}


# ---------- עזר משותף לסוכן ולמענה הנציג ----------


def run_comparison(record: ConversationRecord) -> CompareResponse:
    """מריץ את ההשוואה האחרונה מחדש עם כל מה שידוע עכשיו (למשל אחרי תשובת נציג)."""
    alternatives = []
    for alt in record.alternatives:
        if alt.kind == "car":
            known = record.participations.get(alt.car_id)
            alternatives.append(OptionRequest(kind="car", car_id=alt.car_id, participation=known or Tracked(source="missing")))
        else:
            alternatives.append(alt)
    resp = compare(CompareRequest(profile=record.state.profile, alternatives=alternatives))
    record.state.last_comparison = resp
    return resp


def summarize(resp: CompareResponse) -> dict:
    """מה שהמודל רואה מההשוואה — מספרים מעוגלים לשקל, כמו בתצוגה."""

    def one(r, is_current=False):
        out = {"label": r.label, "status": r.status, "explanation": r.explanation}
        if r.net is not None:
            out["net"] = round(r.net)
        if not is_current:
            out["eligible"] = r.eligibility.eligible
            if r.delta_display is not None:
                out["delta"] = r.delta_display
        if r.missing:
            out["missing"] = r.missing
        return out

    return {"today": one(resp.current, True), "alternatives": [one(a) for a in resp.alternatives]}


def missing_profile_fields(record: ConversationRecord) -> list[str]:
    p = record.state.profile
    missing = [f for f in PROFILE_NUMBERS if p.__getattribute__(f).value is None]
    if p.occupation.value is None and p.group.value is None:
        missing.insert(0, "occupation")
    if p.current_option.value is None:
        missing.append("current_situation")
    elif p.current_option.value.kind == "car" and p.current_option.value.participation.value is None:
        missing.append("current_participation")
    return missing
