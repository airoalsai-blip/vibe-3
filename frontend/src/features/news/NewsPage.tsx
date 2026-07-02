import { useEffect, useMemo, useState } from "react";
import { api, type NewsArticle, type NewsCollectionRun } from "../../lib/api";

function toDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function toKstDateInput(date: Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Seoul" }).format(date);
}

function formatDisplayDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  return value.slice(0, 10);
}

export function NewsPage() {
  const [adminPin, setAdminPin] = useState("1234");
  const [selectedDate, setSelectedDate] = useState(toKstDateInput(addDays(new Date(), -1)));
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [runs, setRuns] = useState<NewsCollectionRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCollecting, setIsCollecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedDateLabel = useMemo(() => selectedDate.replace(/-/g, "."), [selectedDate]);

  async function loadData() {
    setIsLoading(true);
    setError(null);
    try {
      const [articleResult, runResult] = await Promise.all([
        api.newsArticles(selectedDate),
        api.newsRuns(10),
      ]);
      setArticles(articleResult.items);
      setRuns(runResult.items);
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "뉴스 데이터를 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [selectedDate]);

  async function handleCollect() {
    setIsCollecting(true);
    setError(null);
    setMessage(null);
    try {
      const result = await api.collectNews(selectedDate, adminPin);
      setMessage(
        `수집 완료: ${result.inserted_count}건 저장, ${result.duplicate_count}건 중복, ${result.fetched_count}건 확인`,
      );
      await loadData();
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "수집에 실패했습니다.");
    } finally {
      setIsCollecting(false);
    }
  }

  return (
    <section className="workspace-section news-workspace">
      <div className="section-header">
        <div>
          <h2>정책브리핑 기사 수집</h2>
          <p>대한민국 정책브리핑의 정책뉴스를 날짜 기준으로 수집하고 DB에 저장합니다.</p>
        </div>
        <label className="pin-field">
          관리자 PIN
          <input value={adminPin} onChange={(event) => setAdminPin(event.target.value)} type="password" />
        </label>
      </div>

      <div className="news-controls">
        <label>
          수집 날짜
          <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>
        <button type="button" onClick={handleCollect} disabled={isCollecting}>
          {isCollecting ? "수집 중..." : "선택 날짜 수집"}
        </button>
      </div>

      {error ? <div className="inline-alert">{error}</div> : null}
      {message ? <div className="success-alert">{message}</div> : null}

      <div className="news-grid">
        <section className="news-panel">
          <div className="section-header compact">
            <h3>{selectedDateLabel} 기사</h3>
            <span>{articles.length}건</span>
          </div>
          {isLoading ? <p>기사 목록을 불러오는 중입니다.</p> : null}
          {!isLoading && articles.length === 0 ? <p>선택한 날짜의 저장된 기사가 없습니다.</p> : null}
          <div className="article-list">
            {articles.map((article) => (
              <article className="feature-card" key={article.id}>
                <span>
                  {article.category ?? "정책뉴스"} · {formatDisplayDate(article.published_at)}
                </span>
                <strong>{article.title}</strong>
                <p>{article.summary ?? "요약 없음"}</p>
                <a href={article.url} target="_blank" rel="noreferrer">
                  원문 보기
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="news-panel">
          <div className="section-header compact">
            <h3>최근 수집 실행</h3>
            <span>{runs.length}건</span>
          </div>
          <div className="run-list">
            {runs.map((run) => (
              <article className="list-card" key={run.id}>
                <strong>
                  {run.target_date} / {run.mode} / {run.status}
                </strong>
                <span>
                  저장 {run.inserted_count}건 · 중복 {run.duplicate_count}건 · 확인 {run.fetched_count}건
                </span>
                <small>시작 {run.started_at}</small>
                <small>종료 {run.finished_at ?? "-"}</small>
                {run.error_message ? <small className="error-text">{run.error_message}</small> : null}
              </article>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
