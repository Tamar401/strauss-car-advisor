import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, NavLink, Navigate, Route, Routes } from "react-router-dom";

import "./design/tokens.css";
import AdminPage from "./pages/AdminPage";
import DesignPage from "./pages/DesignPage";
import EmployeePage from "./pages/EmployeePage";
import RepPage from "./pages/RepPage";

const NAV = [
  { to: "/employee", label: "עובד" },
  { to: "/rep", label: "נציג תחבורה" },
  { to: "/admin", label: "כללים" },
  // /design — דף ייחוס פנימי למפתחות, לא בתפריט. נכנסים בכתובת ישירה
];

function Shell() {
  return (
    <div className="aurora relative isolate min-h-screen">
      <header className="glass sticky top-0 z-10 border-b border-border/60">
        <div className="petal-ribbon h-1" />
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <img src="/strauss-logo.svg" alt="שטראוס" className="h-11 w-auto" />
            <div className="h-9 w-px bg-border" />
            <div className="leading-tight">
              <div className="font-display text-lg font-bold">יועץ הרכב</div>
              <div className="text-xs text-ink-soft">מה יקרה לנטו שלי?</div>
            </div>
          </div>
          <nav className="flex max-w-full gap-1 overflow-x-auto rounded-full bg-muted/80 p-1">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  `whitespace-nowrap rounded-full px-4 py-1.5 text-sm transition ${
                    isActive ? "bg-surface font-medium text-brand shadow-card" : "text-ink-soft hover:text-ink"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/employee" replace />} />
          <Route path="/employee" element={<EmployeePage />} />
          <Route path="/rep" element={<RepPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/design" element={<DesignPage />} />
        </Routes>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  </React.StrictMode>,
);
