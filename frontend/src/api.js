// לקוח ה-API — מקביל לנתיבים ב-backend/app/api. כל המבנים מוגדרים ב-backend/app/contracts.py
async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail;
    // detail יכול להיות מחרוזת, או {message, problems} בשגיאת ולידציה של הכללים
    const err = new Error(typeof detail === "string" ? detail : detail?.message ?? `שגיאה ${res.status}`);
    err.problems = detail?.problems ?? [];
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  catalog: () => request("/catalog"),
  occupations: () => request("/occupations"),
  demoEmployees: () => request("/demo-employees"),
  compare: (profile, alternatives) => request("/compare", { method: "POST", body: { profile, alternatives } }),
  compareAll: (profile) => request("/compare/all", { method: "POST", body: { profile } }),
  demoCompare: (employeeId) => request(`/demo/compare/${employeeId}`),
  chat: (conversationId, message) =>
    request("/chat", { method: "POST", body: { conversation_id: conversationId, message } }),
  conversation: (id) => request(`/conversations/${id}`),
  explore: (id) => request(`/conversations/${id}/explore`, { method: "POST" }),
  loadDemo: (conversationId, employeeId) =>
    request(`/conversations/${conversationId ?? "new"}/demo/${employeeId}`, { method: "POST" }),
  repQuestions: (status) => request(`/rep/questions${status ? `?status=${status}` : ""}`),
  answerQuestion: (id, answer) => request(`/rep/questions/${id}/answer`, { method: "POST", body: answer }),
  rules: () => request("/rules"),
  previewRules: (rules) => request("/rules/preview", { method: "POST", body: { rules } }),
  saveRules: (rules) => request("/rules", { method: "PUT", body: { rules } }),
  undoRules: () => request("/rules/undo", { method: "POST" }),
};
