// מסך הכללים — בעלות: מפתחת ב'. כרגע תצוגה בלבד; עריכה + ולידציה ב-18/10.
import { useEffect, useState } from "react";

import { api } from "../api";
import { Card, Money, SectionTitle } from "../design/components";

export default function AdminPage() {
  const [rules, setRules] = useState(null);
  useEffect(() => {
    api.rules().then(setRules);
  }, []);
  if (!rules) return null;

  return (
    <div className="space-y-6">
      <SectionTitle hint={`גרסה ${rules.version}`}>קובץ הכללים</SectionTitle>
      <Card>
        <div className="mb-3 font-medium">תקציב רכב חודשי לפי קבוצה</div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Object.entries(rules.budgets).map(([g, b]) => (
            <div key={g} className="rounded-xl bg-muted p-3">
              <div className="text-xs text-ink-soft">קבוצה {g}</div>
              <Money value={b} className="text-lg font-bold" />
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <pre className="num max-h-96 overflow-auto text-left text-xs">{JSON.stringify(rules, null, 2)}</pre>
      </Card>
    </div>
  );
}
