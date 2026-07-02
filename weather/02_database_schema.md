# 비상근무 알림 시스템 SQLite 초안

## 1. 설계 목표

- SQLite 기준으로 빠르게 시작한다.
- 특보 수집, 명단, 정책, 순번, 알림 이력을 분리해서 관리한다.
- 나중에 PostgreSQL로 옮기기 쉽게 구조를 잡는다.

## 2. 핵심 테이블

### 2.1 regions

선택 가능한 지역을 저장한다.

필드:
- id
- 시도명
- 시군구명
- 행정코드
- 활성여부
- 생성일시
- 수정일시

### 2.2 weather_alerts

수집한 특보 정보를 저장한다.

필드:
- id
- region_id
- 특보유형
- 특보등급
- 발효시각
- 종료시각
- 상태
- 원본응답JSON
- 수집시각

### 2.3 departments

부서 정보를 저장한다.

필드:
- id
- 부서명
- 설명
- 활성여부
- 생성일시
- 수정일시

### 2.4 employees

비상근무 대상자를 저장한다.

필드:
- id
- 부서_id
- 이름
- 직책
- 연락처
- 이메일
- 순번
- 상태
- 비고
- 생성일시
- 수정일시

### 2.5 department_weather_policy

부서별로 알림을 받을 특보 유형을 저장한다.

필드:
- id
- 부서_id
- region_id
- 특보유형
- 알림사용여부
- 수정가능여부
- 생성일시
- 수정일시

설명:
- 한 부서가 여러 특보 유형을 가질 수 있으므로 row 단위로 저장한다.
- 수정 시 기존 row를 덮어쓰거나 버전 row를 남길 수 있다.

### 2.6 duty_rotations

순번 정보를 관리한다.

필드:
- id
- 부서_id
- 현재순번
- 다음순번
- 사전알림분
- 활성여부
- 생성일시
- 수정일시

### 2.7 notification_rules

알림 발송 규칙을 저장한다.

필드:
- id
- 부서_id
- region_id
- 특보유형
- 즉시발송여부
- 사전발송여부
- 사전발송채널
- 즉시발송채널
- 생성일시
- 수정일시

### 2.8 notification_logs

발송 이력을 저장한다.

필드:
- id
- employee_id
- department_id
- region_id
- 특보유형
- 발송유형
- 발송채널
- 발송대상시각
- 실제발송시각
- 상태
- 실패사유
- 재시도횟수
- 외부메시지ID
- 생성일시

### 2.9 file_import_jobs

명단 파일 업로드 작업을 관리한다.

필드:
- id
- 파일명
- 원본형식
- 상태
- 처리건수
- 성공건수
- 실패건수
- 실패사유
- 생성일시
- 완료일시

### 2.10 manual_entries

수기 입력한 명단 원본을 저장한다.

필드:
- id
- 부서_id
- 이름
- 직책
- 연락처
- 이메일
- 순번
- 상태
- 생성일시
- 수정일시

## 3. 테이블 관계

- regions 1 : N weather_alerts
- departments 1 : N employees
- departments 1 : N department_weather_policy
- departments 1 : N duty_rotations
- departments 1 : N notification_rules
- employees 1 : N notification_logs
- regions 1 : N notification_logs

## 4. 인덱스 권장

- weather_alerts(region_id, 특보유형, 발효시각)
- employees(department_id, 순번)
- department_weather_policy(department_id, region_id, 특보유형)
- notification_logs(department_id, region_id, 특보유형, 생성일시)
- file_import_jobs(생성일시)

## 5. 초기 제약 조건

- 부서명은 중복 방지
- 같은 부서 + 지역 + 특보유형 정책은 중복 방지
- 순번은 부서 단위로만 유일하게 관리
- 발송 로그는 동일 이벤트 중복 발송 방지를 위한 식별키를 둔다

## 6. SQLite 우선 설계 이유

- 시작이 빠르다
- 배포와 테스트가 쉽다
- 로컬 개발 환경에서 의존성이 적다
- 추후 PostgreSQL 전환 시 테이블 구조를 유지하기 쉽다

