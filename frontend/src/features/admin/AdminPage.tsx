const adminItems = ["사용자 및 권한", "민원 매뉴얼", "뉴스 키워드", "감사 로그"];

export function AdminPage() {
  return (
    <section className="workspace-section">
      <div className="section-header">
        <h2>관리자 설정</h2>
        <button type="button">설정 저장</button>
      </div>
      <div className="admin-list">
        {adminItems.map((item) => (
          <article className="feature-card" key={item}>
            <strong>{item}</strong>
            <p>운영 문서 기준으로 상세 기능을 연결할 예정입니다.</p>
          </article>
        ))}
      </div>
    </section>
  );
}
