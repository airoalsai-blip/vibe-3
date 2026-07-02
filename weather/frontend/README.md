# Frontend

이 폴더는 날씨 비상근무 알림 시스템의 HTML/CSS/JavaScript 초안이다.

## 확인 방법

브라우저에서 `index.html`을 열면 된다.

화면은 `http://127.0.0.1:8000` 백엔드와 직접 통신한다.
파일 업로드는 브라우저에서 파일을 읽어 JSON(base64)으로 전송한다.
수기 입력은 별도 폼에서 `manual_entries`에 저장한다.
상단의 `백엔드 URL` 입력칸에 로컬 주소나 Cloudflare Tunnel 주소를 넣고 저장할 수 있다.

## 구성

- `index.html`: 화면 구조
- `css/styles.css`: 스타일
- `js/app.js`: API 연동, 파일 업로드, 정책 수정, 폼 제출 처리
