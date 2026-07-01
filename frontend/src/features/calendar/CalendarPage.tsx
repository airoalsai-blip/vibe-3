const schedules = [
  { date: "2026-07-01", owner: "행정지원팀", type: "근무", title: "민원 접수 현황 점검" },
  { date: "2026-07-02", owner: "복지행정팀", type: "출장", title: "현장 점검" },
  { date: "2026-07-03", owner: "총무팀", type: "휴가", title: "연차" },
];

export function CalendarPage() {
  return (
    <section className="workspace-section">
      <div className="section-header">
        <h2>팀원 스케줄 관리</h2>
        <button type="button">일정 추가</button>
      </div>
      <div className="schedule-grid">
        {schedules.map((schedule) => (
          <article className="feature-card" key={`${schedule.date}-${schedule.title}`}>
            <span>{schedule.date}</span>
            <strong>{schedule.title}</strong>
            <p>{schedule.owner} · {schedule.type}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
