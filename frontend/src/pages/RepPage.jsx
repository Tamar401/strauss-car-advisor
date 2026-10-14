// מסך הנציג — בעלות: מפתחת א'.
import { useEffect, useState } from "react";

import { api } from "../api";
import { Badge, Button, Card, Input, SectionTitle } from "../design/components";

function QuestionCard({ q, onAnswered }) {
  const [value, setValue] = useState("");
  const [from, setFrom] = useState("");

  async function submit(e) {
    e.preventDefault();
    await api.answerQuestion(q.id, { value: Number(value), effective_from: from || null });
    onAnswered();
  }

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-display font-bold">{q.employee_display_name}</div>
          <div className="text-xs text-ink-soft">{q.context}</div>
        </div>
        <Badge tone={q.status === "open" ? "warn" : "up"}>{q.status === "open" ? "פתוחה" : "נענתה"}</Badge>
      </div>
      <p className="mt-3 text-sm">{q.question_text}</p>
      {q.status === "open" ? (
        <form onSubmit={submit} className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <Input label="תשובה (₪)" type="number" required value={value} onChange={(e) => setValue(e.target.value)} />
          <Input label="בתוקף מ-" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          <Button type="submit">שליחה לעובד</Button>
        </form>
      ) : (
        <div className="mt-3 text-sm text-up">
          נענתה: <span className="num">{q.answer.value}</span>
          {q.answer.effective_from && ` · בתוקף מ-${q.answer.effective_from}`}
        </div>
      )}
    </Card>
  );
}

export default function RepPage() {
  const [questions, setQuestions] = useState([]);
  const load = () => api.repQuestions().then(setQuestions);

  useEffect(() => {
    load();
    const t = setInterval(load, 2000); // שאלות חדשות מופיעות בלי רענון
    return () => clearInterval(t);
  }, []);

  const open = questions.filter((q) => q.status === "open").length;

  return (
    <div className="mx-auto max-w-3xl">
      <SectionTitle hint={`${open} פתוחות`}>שאלות מעובדים</SectionTitle>
      <div className="space-y-4">
        {questions.map((q) => (
          <QuestionCard key={q.id} q={q} onAnswered={load} />
        ))}
      </div>
    </div>
  );
}
