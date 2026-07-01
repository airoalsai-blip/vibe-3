export function ExcelPage() {
  return (
    <section className="workspace-section">
      <div className="section-header">
        <h2>엑셀 업무 자동화</h2>
        <button type="button">파일 업로드</button>
      </div>
      <div className="split-layout">
        <article className="feature-card">
          <span>Split</span>
          <strong>기준 컬럼별 파일 분할</strong>
          <p>부서명, 담당자, 지역 등 선택한 컬럼 값 기준으로 결과 파일을 생성합니다.</p>
        </article>
        <article className="feature-card">
          <span>Merge</span>
          <strong>여러 엑셀 파일 병합</strong>
          <p>동일 양식의 파일을 하나로 합치고 컬럼 불일치 경고를 표시합니다.</p>
        </article>
      </div>
    </section>
  );
}
