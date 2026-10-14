"""בדיקות שהחוזה, ה-seed וה-API המדומה מסונכרנים. אם נשבר כאן — מישהי שינתה חוזה בלי לעדכן."""
from fastapi.testclient import TestClient

from app import seed
from app.contracts import Car, CompareResponse, Occupation
from app.main import app

client = TestClient(app)


def test_seed_matches_contracts():
    assert len(seed.catalog()) == 20
    assert len(seed.occupations()) == 14
    for c in seed.catalog():
        Car.model_validate(c)
    for o in seed.occupations():
        Occupation.model_validate(o)


def test_mock_compare_is_valid_and_matches_golden():
    resp = CompareResponse.model_validate(seed.mock("compare_E-001.json"))
    golden = next(g for g in seed.golden() if g["employee_id"] == "E-001")
    atto3 = next(a for a in resp.alternatives if a.option.car_id == "CAR-10")
    assert round(resp.current.net) == golden["net_today"]
    assert round(atto3.net) == golden["net_alternative"]
    assert round(atto3.delta_net) == golden["delta"]


def test_waterfall_sums_to_delta():
    resp = CompareResponse.model_validate(seed.mock("compare_E-001.json"))
    for alt in resp.alternatives:
        if alt.waterfall:
            assert abs(sum(s.amount for s in alt.waterfall) - alt.delta_net) < 1e-6


def test_chat_flow_and_resume():
    first = client.post("/api/chat", json={"message": "אני שוקלת לעבור לרכב חשמלי"}).json()
    cid = first["conversation_id"]
    client.post("/api/chat", json={"conversation_id": cid, "message": "קבוצה ג, 18,500"})
    resumed = client.get(f"/api/conversations/{cid}").json()
    assert len(resumed["messages"]) == 4
    assert resumed["last_comparison"] is not None


def test_rep_answer():
    open_qs = client.get("/api/rep/questions", params={"status": "open"}).json()
    q = open_qs[0]
    answered = client.post(f"/api/rep/questions/{q['id']}/answer", json={"value": 350, "effective_from": "2027-01-01"}).json()
    assert answered["status"] == "answered"
