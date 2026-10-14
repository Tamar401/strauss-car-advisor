// מסך העובד — הצ'אט וכרטיס הפרופיל: מפתחת ב'. אזור ההשוואה: מפתחת א'.
import { useEffect, useRef, useState } from "react";

import { api } from "../api";
import OptionCard from "../components/OptionCard";
import { Button, Card, ChatBubble, PetalMark, SectionTitle } from "../design/components";

const STORAGE_KEY = "conversation_id";

const STARTERS = [
  "אני שוקל/ת לעבור לרכב חשמלי. כמה זה ישנה לי בנטו?",
  "מה יקרה לנטו אם אוותר על הרכב?",
  "יש לי 4 ילדים, מגיע לי רכב משפחתי?",
];

function readStoredId() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeId(id) {
  try {
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* מצב פרטי — השיחה פשוט לא תשוחזר אחרי רענון */
  }
}

export default function EmployeePage() {
  const [state, setState] = useState(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  // אחרי רענון: משחזרים את השיחה מהשרת
  useEffect(() => {
    const id = readStoredId();
    if (id) api.conversation(id).then(setState).catch(() => storeId(null));
  }, []);

  // בסוגריים מסולסלים בכוונה: בדפדפנים חדשים scrollIntoView מחזיר Promise, ו-React ינסה להפעיל אותו כ-cleanup
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [state?.messages.length]);

  async function send(message) {
    if (!message.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const next = await api.chat(state?.conversation_id ?? null, message.trim());
      storeId(next.conversation_id);
      setState(next);
      setText("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    storeId(null);
    setState(null);
  }

  const comparison = state?.last_comparison;

  return (
    <div className="space-y-8">
      <section className="max-w-2xl">
        <h1 className="font-display text-3xl font-bold leading-tight sm:text-5xl">
          מה יקרה <span className="petal-text">לנטו שלי?</span>
        </h1>
        <p className="mt-3 text-ink-soft sm:text-lg">
          רכב חשמלי, רכב אחר או ויתור על הרכב: תשובה מדויקת תוך דקה, עם הסבר לכל שקל.
        </p>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)]">
        <Card className="glass flex h-[68vh] min-h-[460px] flex-col p-0">
          <div className="flex items-center justify-between border-b border-border/70 px-5 py-3">
            <div className="flex items-center gap-2.5">
              <div className="relative">
                <PetalMark size={30} />
                <span className="absolute -bottom-0.5 -left-0.5 h-2.5 w-2.5 rounded-full border-2 border-surface bg-up" />
              </div>
              <div className="leading-tight">
                <div className="font-display font-bold">יועץ הרכב</div>
                <div className="text-xs text-ink-soft">{busy ? "מקליד…" : "זמין עכשיו"}</div>
              </div>
            </div>
            <Button variant="ghost" onClick={reset}>
              שיחה חדשה
            </Button>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto px-5 py-5">
            {!state && (
              <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
                <PetalMark size={56} />
                <p className="max-w-xs text-sm text-ink-soft">במה אפשר לעזור? אפשר לכתוב חופשי, או להתחיל מכאן:</p>
                <div className="flex flex-col gap-2">
                  {STARTERS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-full border border-border bg-surface px-4 py-2 text-sm transition hover:border-brand hover:text-brand"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {state?.messages.map((m) => (
              <ChatBubble key={m.id} role={m.role}>
                {m.text}
              </ChatBubble>
            ))}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
            }}
            className="flex gap-2 border-t border-border/70 p-3"
          >
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="כתבו כאן…"
              className="flex-1 rounded-full border border-border bg-surface px-4 py-2.5 text-sm outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/15"
            />
            <Button type="submit" disabled={busy}>
              שליחה
            </Button>
          </form>
          {error && <div className="px-5 pb-3 text-sm text-down">{error}</div>}
        </Card>

        <div>
          <SectionTitle hint={comparison ? `כללים: ${comparison.rules_version}` : undefined}>ההשוואה שלך</SectionTitle>
          {comparison ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <OptionCard result={comparison.current} isCurrent />
              {comparison.alternatives.map((a, i) => (
                <OptionCard key={i} result={a} />
              ))}
            </div>
          ) : (
            <Card className="glass flex flex-col items-center gap-3 py-12 text-center">
              <div className="petal-ribbon h-1.5 w-24 rounded-full opacity-70" />
              <p className="max-w-sm text-sm text-ink-soft">
                ההשוואה תופיע כאן ברגע שיהיו מספיק נתונים: כל חלופה עם הנטו המשוער, ההפרש מול היום, והסבר במילים פשוטות.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
