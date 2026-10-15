// כרטיס הפרופיל — מה הבוט יודע, ומאיפה כל נתון הגיע. בעלות: מפתחת ב'.
import { Card, SourceBadge } from "../design/components";

const FIELDS = [
  ["occupation", "עיסוק"],
  ["base_salary", "שכר בסיס", "₪"],
  ["commissions", "עמלות", "₪"],
  ["bonus", "בונוס", "₪"],
  ["pension_pct", "פנסיה", "%"],
  ["study_fund_pct", "קרן השתלמות", "%"],
  ["credit_points", "נקודות זיכוי"],
];

function show(value, unit) {
  if (value == null) return "—";
  if (typeof value === "number") {
    const n = value.toLocaleString("he-IL", { maximumFractionDigits: 2 });
    return unit === "₪" ? `${n} ₪` : unit === "%" ? `${n}%` : n;
  }
  return value;
}

function currentText(option, catalog) {
  if (!option) return null;
  if (option.kind === "waiver") return "ויתור (אחזקת רכב)";
  // רכב מהקטלוג, רכב מהמאגר (vou_key), או רכב שעוד לא זוהה — vehicle_label מכסה את שני האחרונים
  const car = option.car_id ? catalog[option.car_id] : null;
  const name = car ? `${car.model} (${car.registration_year})` : option.vehicle_label ?? option.car_id ?? "רכב";
  const part = option.participation?.value;
  return part != null ? `${name} · השתתפות ${part.toLocaleString("he-IL")} ₪` : name;
}

function Row({ label, value, source }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <span className="text-ink-soft">{label}</span>
      <span className="flex items-center gap-2 text-left">
        <span className="num font-medium">{value}</span>
        <SourceBadge source={source} />
      </span>
    </div>
  );
}

export default function ProfileCard({ state, catalog }) {
  const p = state.profile;
  const current = p.current_option?.value;
  const known = FIELDS.filter(([key]) => p[key]?.value != null).length + (current ? 1 : 0);
  const total = FIELDS.length + 1;

  return (
    <Card className="glass">
      <div className="mb-2 flex items-baseline justify-between">
        <div className="font-display font-bold">
          מה אני יודע עליך{state.employee_display_name ? `, ${state.employee_display_name}` : ""}
        </div>
        <span className="num text-xs text-ink-soft">
          {known}/{total}
        </span>
      </div>
      {/* פס התקדמות: כמה מהנתונים הדרושים כבר נאספו */}
      <div className="mb-3 h-1.5 overflow-hidden rounded-full bg-muted">
        <div className="petal-ribbon h-full transition-all duration-500" style={{ width: `${(known / total) * 100}%` }} />
      </div>
      <div className="divide-y divide-border/60 text-sm">
        {FIELDS.map(([key, label, unit]) => (
          <Row key={key} label={label} value={show(p[key]?.value, unit)} source={p[key]?.source ?? "missing"} />
        ))}
        <Row
          label="היום"
          value={currentText(current, catalog) ?? "—"}
          source={current ? p.current_option.source : "missing"}
        />
        {p.children_under_23?.value != null && (
          <Row label="ילדים עד 23" value={p.children_under_23.value} source={p.children_under_23.source} />
        )}
      </div>
    </Card>
  );
}
