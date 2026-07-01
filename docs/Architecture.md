# 공공직군 행정업무 슈퍼앱 Architecture

## 1. 문서 목적

본 문서는 공공직군 행정업무 슈퍼앱의 기술 요구사항, 시스템 구조, 프로젝트 구조, 모듈별 역할을 정의한다. 현재 저장소에는 `frontend`와 `backend` 디렉터리가 존재하며, 프론트엔드는 React/Vite 기반 의존성이 준비되어 있다.

## 2. 기술 스택 제안

| 영역 | 권장 기술 | 비고 |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | 현재 `frontend/package.json` 기준 |
| Backend | Python FastAPI | 행정 자동화, 파일 처리, AI 연동에 적합 |
| Database | PostgreSQL | 일정, 사용자, 작업 이력, 뉴스 메타데이터 저장 |
| Cache/Queue | Redis, Celery 또는 RQ | 엑셀 처리, 뉴스 수집, 문서 색인 비동기 처리 |
| File Storage | 내부 파일 서버 또는 S3 호환 스토리지 | 엑셀, 매뉴얼, 처리 결과 저장 |
| AI/RAG | 임베딩 모델, 벡터 DB, LLM API | 민원 매뉴얼 기반 검색 증강 생성 |
| Scheduler | Celery Beat, APScheduler, cron | 매일 아침 뉴스 수집 |
| Auth | 세션/JWT, SSO 연동 고려 | 내부망 운영 시 기관 인증 연동 가능 |
| Logging | 구조화 로그, 감사 로그 테이블 | 추적성과 감사 대응 |

## 3. 전체 아키텍처

```text
사용자 브라우저
    |
    v
Frontend: React/Vite
    |
    v
Backend API: FastAPI
    |
    +--> PostgreSQL: 사용자, 일정, 이력, 뉴스 메타데이터
    |
    +--> File Storage: 업로드 파일, 매뉴얼, 결과 파일
    |
    +--> Worker Queue: 엑셀 처리, 문서 색인, 뉴스 수집
    |
    +--> Vector Store: 민원 매뉴얼 임베딩 검색
    |
    +--> External Services: LLM API, 뉴스 검색 API/RSS
```

## 4. 프로젝트 구조

```text
DAY3/
  docs/
    PRD.md
    Architecture.md
    Operation.md
    index.html
  frontend/
    package.json
    package-lock.json
    src/
      app/
      components/
      features/
        calendar/
        excel/
        chatbot/
        news/
        admin/
      lib/
      routes/
      styles/
  backend/
    app/
      main.py
      core/
        config.py
        security.py
        logging.py
      api/
        routes/
          auth.py
          users.py
          schedules.py
          excel.py
          chatbot.py
          news.py
          admin.py
      domain/
        users/
        schedules/
        excel_jobs/
        chatbot/
        news/
      services/
        excel_processor.py
        manual_indexer.py
        chatbot_service.py
        news_collector.py
        scheduler.py
      workers/
      models/
      schemas/
      repositories/
      tests/
```

## 5. 모듈별 역할

### 5.1 Frontend

| 모듈 | 역할 |
| --- | --- |
| `app` | 앱 초기화, 라우팅, 전역 상태 연결 |
| `components` | 버튼, 입력, 모달, 테이블 등 공통 UI |
| `features/calendar` | 팀원 일정 캘린더 화면, 일정 등록/수정 폼 |
| `features/excel` | 엑셀 업로드, 미리보기, 컬럼 선택, 결과 다운로드 |
| `features/chatbot` | 민원 질문 입력, 답변, 근거 문서 표시 |
| `features/news` | 아침 뉴스 브리핑, 키워드 필터, 기사 상세 |
| `features/admin` | 사용자, 권한, 키워드, 매뉴얼 관리 |
| `lib` | API 클라이언트, 날짜/파일 유틸리티 |
| `styles` | 전역 스타일, 디자인 토큰 |

### 5.2 Backend API

| 모듈 | 역할 |
| --- | --- |
| `auth` | 로그인, 토큰 발급, 사용자 인증 |
| `users` | 사용자, 팀, 역할 관리 |
| `schedules` | 일정 CRUD, 캘린더 조회, 권한 필터링 |
| `excel` | 파일 업로드, 작업 생성, 처리 결과 조회 |
| `chatbot` | 질문 접수, 매뉴얼 검색, 답변 생성 |
| `news` | 뉴스 목록 조회, 수집 실행, 키워드 관리 |
| `admin` | 시스템 설정, 감사 로그, 매뉴얼 관리 |

### 5.3 Worker

| 작업 | 설명 |
| --- | --- |
| 엑셀 분할 | 기준 컬럼 값별로 파일 생성 |
| 엑셀 병합 | 여러 파일을 하나로 통합하고 컬럼 불일치 검사 |
| 문서 색인 | 업로드된 민원 매뉴얼을 텍스트 추출 후 벡터화 |
| 뉴스 수집 | 지정 시간에 키워드 기반 기사 수집 |
| 요약 생성 | 수집 기사 요약 및 카테고리 분류 |

## 6. 데이터 모델 초안

### User

| 필드 | 설명 |
| --- | --- |
| `id` | 사용자 ID |
| `name` | 이름 |
| `email` | 이메일 또는 로그인 ID |
| `department_id` | 소속 부서 |
| `role` | 사용자 역할 |
| `is_active` | 활성 여부 |

### Schedule

| 필드 | 설명 |
| --- | --- |
| `id` | 일정 ID |
| `owner_id` | 일정 소유자 |
| `type` | 휴가, 근무, 출장, 교육 등 |
| `title` | 일정 제목 |
| `description` | 상세 설명 |
| `start_at` | 시작 일시 |
| `end_at` | 종료 일시 |
| `visibility` | 공개 범위 |

### ExcelJob

| 필드 | 설명 |
| --- | --- |
| `id` | 작업 ID |
| `user_id` | 요청자 |
| `job_type` | split 또는 merge |
| `status` | pending, running, completed, failed |
| `source_file_id` | 원본 파일 |
| `result_file_id` | 결과 파일 |
| `options` | 기준 컬럼, 헤더 행 등 처리 옵션 |
| `error_message` | 실패 사유 |

### ManualDocument

| 필드 | 설명 |
| --- | --- |
| `id` | 매뉴얼 ID |
| `title` | 문서명 |
| `file_id` | 원본 파일 |
| `version` | 버전 |
| `indexed_at` | 색인 완료 시각 |
| `status` | active, archived, failed |

### ChatbotConversation

| 필드 | 설명 |
| --- | --- |
| `id` | 대화 ID |
| `user_id` | 질문자 |
| `question` | 사용자 질문 |
| `answer` | 생성 답변 |
| `citations` | 참조 매뉴얼 조각 |
| `created_at` | 생성 시각 |

### NewsArticle

| 필드 | 설명 |
| --- | --- |
| `id` | 기사 ID |
| `title` | 제목 |
| `source` | 언론사 또는 출처 |
| `url` | 원문 링크 |
| `published_at` | 발행일 |
| `summary` | 요약 |
| `category` | 분류 |
| `collected_at` | 수집 시각 |

## 7. API 설계 초안

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/api/auth/login` | 로그인 |
| `GET` | `/api/schedules` | 일정 목록 조회 |
| `POST` | `/api/schedules` | 일정 생성 |
| `PATCH` | `/api/schedules/{id}` | 일정 수정 |
| `DELETE` | `/api/schedules/{id}` | 일정 삭제 |
| `POST` | `/api/excel/split` | 엑셀 분할 작업 생성 |
| `POST` | `/api/excel/merge` | 엑셀 병합 작업 생성 |
| `GET` | `/api/excel/jobs/{id}` | 엑셀 작업 상태 조회 |
| `POST` | `/api/manuals` | 민원 매뉴얼 업로드 |
| `POST` | `/api/chatbot/messages` | 챗봇 질문 및 답변 생성 |
| `GET` | `/api/news/articles` | 뉴스 목록 조회 |
| `POST` | `/api/news/collect` | 뉴스 수집 수동 실행 |

## 8. 주요 처리 흐름

### 엑셀 분할

1. 사용자가 파일을 업로드한다.
2. 서버가 파일을 임시 저장하고 컬럼 미리보기를 반환한다.
3. 사용자가 기준 컬럼과 옵션을 선택한다.
4. 백엔드는 작업을 큐에 등록한다.
5. 워커가 파일을 읽고 기준 컬럼 값별로 파일을 생성한다.
6. 결과 파일을 스토리지에 저장하고 다운로드 URL을 제공한다.

### 민원 챗봇

1. 관리자가 민원 매뉴얼을 업로드한다.
2. 워커가 문서 텍스트를 추출하고 청크 단위로 분할한다.
3. 청크를 임베딩하여 벡터 저장소에 저장한다.
4. 사용자가 민원 질문을 입력한다.
5. 백엔드는 관련 매뉴얼 청크를 검색한다.
6. LLM은 검색 결과를 기반으로 답변 초안을 생성한다.
7. 답변과 근거 문서를 사용자에게 표시한다.

### 뉴스 수집

1. 스케줄러가 매일 아침 수집 작업을 실행한다.
2. 등록된 키워드로 뉴스 API 또는 RSS를 조회한다.
3. URL, 제목, 발행일 기준으로 중복을 제거한다.
4. 기사 메타데이터와 요약을 저장한다.
5. 사용자는 브리핑 화면에서 결과를 확인한다.

## 9. 보안 설계

- 모든 API는 인증 후 접근을 기본값으로 한다.
- 역할 기반 권한 검사를 API와 화면 양쪽에서 적용한다.
- 업로드 파일은 확장자, MIME 타입, 크기를 검사한다.
- 파일 저장 경로는 사용자 입력값을 직접 사용하지 않는다.
- 챗봇 질의 로그에는 개인정보 마스킹을 적용한다.
- 관리자 기능은 별도 권한을 요구한다.
- 감사 로그는 일반 사용자에게 노출하지 않는다.

## 10. 배포 구성

```text
Reverse Proxy
  |
  +--> Frontend Static Server
  |
  +--> Backend API Server
        |
        +--> PostgreSQL
        +--> Redis
        +--> Worker Process
        +--> File Storage
```

## 11. 향후 확장 고려사항

- 기관 SSO 연동
- 전자결재 시스템 연동
- 조직도 및 인사 데이터 연동
- 업무 알림 메신저 연동
- 민원 유형별 추천 답변 템플릿 관리
- 관리자 대시보드 및 통계 리포트
