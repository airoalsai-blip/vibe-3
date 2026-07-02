import { useEffect, useMemo, useState } from "react";
import { AdminPage } from "../features/admin/AdminPage";
import { CalendarPage } from "../features/calendar/CalendarPage";
import { ChatbotPage } from "../features/chatbot/ChatbotPage";
import { ExcelPage } from "../features/excel/ExcelPage";
import { NewsPage } from "../features/news/NewsPage";
import { api, type DbHealthStatus, type HealthStatus } from "../lib/api";
import { StatusBadge } from "../components/StatusBadge";

type PageKey = "calendar" | "excel" | "chatbot" | "news" | "admin";

const pages: Array<{ key: PageKey; label: string }> = [
  { key: "calendar", label: "팀원 일정" },
  { key: "excel", label: "엑셀 자동화" },
  { key: "chatbot", label: "민원 챗봇" },
  { key: "news", label: "뉴스 수집" },
  { key: "admin", label: "관리자" },
];

export function App() {
  const [activePage, setActivePage] = useState<PageKey>("calendar");
  const [apiHealth, setApiHealth] = useState<HealthStatus | null>(null);
  const [dbHealth, setDbHealth] = useState<DbHealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkConnections() {
      try {
        const [apiStatus, dbStatus] = await Promise.all([api.health(), api.dbHealth()]);
        setApiHealth(apiStatus);
        setDbHealth(dbStatus);
        setError(null);
      } catch (currentError) {
        setError(currentError instanceof Error ? currentError.message : "Unknown error");
      }
    }

    checkConnections();
  }, []);

  const currentPage = useMemo(() => {
    switch (activePage) {
      case "calendar":
        return <CalendarPage />;
      case "excel":
        return <ExcelPage />;
      case "chatbot":
        return <ChatbotPage />;
      case "news":
        return <NewsPage />;
      case "admin":
        return <AdminPage />;
    }
  }, [activePage]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>행정업무 슈퍼앱</strong>
          <span>Public Admin Workspace</span>
        </div>
        <nav className="side-nav" aria-label="주요 기능">
          {pages.map((page) => (
            <button
              className={page.key === activePage ? "is-active" : ""}
              key={page.key}
              onClick={() => setActivePage(page.key)}
              type="button"
            >
              {page.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-panel">
        <section className="connection-panel">
          <div>
            <h1>대시보드 연동 확인</h1>
            <p>FE 페이지 구조, FE-BE API, BE-DB 연결 상태를 확인합니다.</p>
          </div>
          <div className="connection-grid">
            <div>
              <span>FE-BE</span>
              <StatusBadge status={apiHealth ? "ok" : error ? "error" : "idle"} label={apiHealth?.status ?? "checking"} />
              <small>{apiHealth?.service ?? error ?? "API 확인 중"}</small>
            </div>
            <div>
              <span>BE-DB</span>
              <StatusBadge status={dbHealth ? "ok" : error ? "error" : "idle"} label={dbHealth?.status ?? "checking"} />
              <small>{dbHealth ? `${dbHealth.database} / ${dbHealth.tables.length} tables` : "DB 확인 중"}</small>
            </div>
          </div>
        </section>

        {currentPage}
      </main>
    </div>
  );
}
