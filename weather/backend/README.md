# Backend

이 폴더는 날씨 비상근무 알림 시스템의 FastAPI 초안이다.

## 실행

```bash
cd weather/backend
uvicorn app.main:app --reload
```

## 구성

- `app/main.py`: FastAPI 앱 진입점
- `app/core/config.py`: 설정
- `app/core/database.py`: SQLite 연결과 테이블 초기화
- `app/api/routes/*`: API 라우터

## 주요 API

- `GET /api/health`: 상태 확인
- `GET /api/departments`: 부서 목록
- `GET /api/regions`: 지역 목록
- `POST /api/regions`: 지역 추가
- `GET /api/employees`: 직원 목록
- `POST /api/employees`: 직원 추가
- `GET /api/manual-entries`: 수기 입력 목록
- `POST /api/manual-entries`: 수기 입력 추가
- `PUT /api/manual-entries/{entry_id}`: 수기 입력 수정
- `GET /api/policies`: 부서별 특보 정책 목록
- `POST /api/policies`: 정책 저장
- `PUT /api/policies/{policy_id}`: 정책 수정
- `GET /api/weather/alerts`: 특보 목록
- `POST /api/weather/alerts`: 특보 저장
- `GET /api/alerts`: 알림 이력
- `POST /api/alerts`: 알림 이력 저장
- `GET /api/imports/jobs`: 파일 업로드 작업 이력
- `POST /api/imports/upload`: 파일 업로드(JSON base64)
