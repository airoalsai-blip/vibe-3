export function ChatbotPage() {
  return (
    <section className="workspace-section">
      <div className="section-header">
        <h2>민원 대응 챗봇</h2>
        <button type="button">매뉴얼 등록</button>
      </div>
      <div className="chat-panel">
        <div className="chat-message chat-message--system">
          매뉴얼 기반 답변 초안과 전화 응대 스크립트를 생성하는 영역입니다.
        </div>
        <label>
          민원 질문
          <textarea placeholder="예: 장기 미처리 민원에 대한 안내 문구를 작성해줘." />
        </label>
        <button type="button">답변 초안 생성</button>
      </div>
    </section>
  );
}
