const articles = [
  { source: "행정 브리핑", title: "공공 행정 서비스 개선 동향", category: "전자정부" },
  { source: "정책 뉴스", title: "지방자치 민원 대응 체계 점검", category: "민원" },
];

export function NewsPage() {
  return (
    <section className="workspace-section">
      <div className="section-header">
        <h2>뉴스 기사 수집</h2>
        <button type="button">수동 수집</button>
      </div>
      <div className="article-list">
        {articles.map((article) => (
          <article className="feature-card" key={article.title}>
            <span>{article.category}</span>
            <strong>{article.title}</strong>
            <p>{article.source}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
