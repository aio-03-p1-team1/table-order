# F&BGrowth API 경로 목록

2026-10-18 기준 `backend/app/routers/`에 등록된 경로만 정리합니다. 요청 필드·쿼리·응답 모델은 실행 중인 서버의 `/docs`에서 확인합니다.

- 경로 원본: `backend/app/core/api_paths.py`의 `API_PREFIX = "/api"`, `ADMIN_API_PREFIX = f"{API_PREFIX}/admin"`.
- 화면은 `shared/api_paths.py`에서 같은 상수를 가져옵니다.
- 관리자 API 전체에는 `require_admin` 인증이 적용됩니다. 현재 인증 방식은 `ADMIN_TOKEN`입니다.
- 경로가 등록되어 있어도 더미 응답인 기능이 있습니다. 구현 상태는 라우터의 `dummy.` 호출과 `backend/app/dummy/`의 `DUMMY_ENDPOINTS`로 확인합니다.
- 담당 범위와 향후 구현 내용은 담당 분배표와 `docs/todo/TODO_*.md`에서 관리합니다.

## 손님·로그인·개발 API

| 메서드 | 경로 | 기능 |
|---|---|---|
| POST | `/api/auth/qr` | 테이블 QR 로그인 발급 |
| GET | `/api/auth/qr/{secret}` | QR 로그인 진행 상태 조회 |
| GET | `/api/auth/kakao/start` | QR 스캔 처리와 카카오 로그인 시작 |
| GET | `/api/auth/kakao/continue` | 문자 수신 동의 기록 후 로그인 계속 |
| GET | `/api/auth/kakao/callback` | 카카오 로그인 결과 처리 |
| GET | `/api/auth/supabase/callback/{state}` | Supabase 로그인 결과 처리 |
| GET | `/api/members/me` | 로그인한 회원 정보 조회 |
| POST | `/api/members/me/opt-out` | 로그인한 회원의 문자 수신거부 |
| GET | `/api/tables/{table_no}/logins` | 태블릿 로그인 회원과 룰렛 사용 여부 조회 |
| GET | `/api/store` | 매장 정보 조회 |
| GET | `/api/content` | 공통 콘텐츠 전체 조회 |
| GET | `/api/content/{name}` | 공통 콘텐츠 항목 조회 |
| GET | `/api/menus` | 손님 메뉴 목록 조회 |
| POST | `/api/orders` | 주문 생성과 쿠폰 사용 요청 |
| GET | `/api/coupons` | 로그인한 회원의 쿠폰함 조회 |
| GET | `/api/tables/{table_no}/coupons` | 태블릿 로그인 회원들의 쿠폰함 조회 |
| PUT | `/api/tables/{table_no}/logins/prize` | 룰렛 당첨 기록과 쿠폰 발급 요청 |
| GET | `/api/roulette/prizes` | DB에 저장된 룰렛 칸과 가중치 조회 |
| POST | `/api/calls` | 직원 호출 등록 |
| POST | `/api/recommendations` | AI 추천 노출 기록 요청 |
| POST | `/api/dev/db-test` | 개발용 DB 쓰기·읽기 확인 |
| GET | `/api/categories` | 손님 카테고리 목록 조회 |

## 관리자 API

| 메서드 | 경로 | 기능 |
|---|---|---|
| GET | `/api/admin/menus` | 관리자 메뉴 목록과 카테고리 이름 조회 |
| PUT | `/api/admin/menus/{menu_id}` | 메뉴 한 건 등록·수정 또는 여러 메뉴 수정·삭제를 원자적으로 일괄 저장 |
| DELETE | `/api/admin/menus/{menu_id}` | 메뉴 삭제 |
| GET | `/api/admin/categories` | 카테고리 목록 조회(메뉴 개수·가상 카테고리 여부 포함) |
| POST | `/api/admin/categories` | 카테고리 추가 |
| PATCH | `/api/admin/categories/{category_id}` | 카테고리 부분 수정 |
| DELETE | `/api/admin/categories/{category_id}` | 빈 카테고리 삭제(메뉴가 남았거나 가상이면 409) |
| GET | `/api/admin/orders` | 관리자 주문 이력 조회 |
| GET | `/api/admin/members` | 회원 목록과 등급 조회 |
| POST | `/api/admin/members/{member_id}/opt-out` | 회원 문자 수신거부 |
| GET | `/api/admin/customers/grades` | 등급별 고객 수 조회 |
| GET | `/api/admin/customers/grades/rules` | 고객 등급 기준 조회 |
| PUT | `/api/admin/customers/grades/rules` | 고객 등급 기준 저장 |
| GET | `/api/admin/customers` | 고객 목록과 등급 조회 |
| POST | `/api/admin/customers/{member_id}/opt-out` | 고객 문자 수신거부 |
| GET | `/api/admin/marketing/regular-preferences` | 오늘 방문한 단골의 주문·선호 안주 조회 |
| GET | `/api/admin/stats` | 대시보드 기본 통계 묶음 조회 |
| GET | `/api/admin/stats/sales` | 매출 기본 통계 조회 |
| GET | `/api/admin/stats/menus/ranking` | 인기 메뉴 순위 조회 |
| GET | `/api/admin/stats/customers` | 고객 통계 조회 |
| GET | `/api/admin/stats/ai-recommendations` | AI 추천 통계 조회 |
| GET | `/api/admin/stats/insights` | 대시보드 추가 통계 묶음 조회 |
| GET | `/api/admin/stats/sales/hourly` | 시간대별 매출 조회 |
| GET | `/api/admin/stats/sales/weekday` | 요일별 매출 조회 |
| GET | `/api/admin/stats/sales/trends` | 기간별 매출 추이 조회 |
| GET | `/api/admin/stats/sales/tickets` | 객단가와 주문 금액 분포 조회 |
| GET | `/api/admin/stats/tables` | 테이블별 주문·매출 통계 조회 |
| GET | `/api/admin/marketing/sms/usage` | 문자 사용량과 한도 조회 |
| POST | `/api/admin/marketing/sms/preview` | 문자 대상·비용·발송 가능 여부 미리보기 |
| POST | `/api/admin/marketing/sms/send` | 문자 즉시·예약 발송 |
| POST | `/api/admin/sms/test` | 문자 1건 테스트 발송 |
| POST | `/api/admin/marketing/sms/logs/{log_id}/cancel` | 예약 문자 발송 취소 |
| GET | `/api/admin/marketing/sms/logs` | 문자 발송·예약 기록 조회 |
| POST | `/api/admin/marketing/sms/candidates` | AI 문자 후보 생성 |
| PUT | `/api/admin/content/{name}` | 공통 콘텐츠 항목 전체 교체 요청 |
| GET | `/api/admin/system/db` | DB 연결과 테이블 확인 |
| PUT | `/api/admin/owner/roulette/prizes` | 룰렛 칸과 가중치 전체 교체 |
| GET | `/api/admin/marketing/external-context` | 날씨·행사 정보 조회 |
| GET | `/api/admin/alerts` | 품절 메뉴와 인기 품절 메뉴 조회 |

## 응답을 구분할 때

- 관리자 메뉴 목록의 `categories`는 `{id, name}` 목록입니다. 메뉴 개수가 필요하면 관리자 카테고리 목록을 조회합니다.
- 손님 카테고리 목록은 `[{id, icon, name, colors}]`입니다. 관리자 카테고리 목록에는 `menu_count`, `is_virtual`이 추가됩니다.
- 메뉴 등록·단건 수정은 메뉴 ID가 포함된 PUT 경로를 사용합니다. 여러 메뉴를 바꿀 때는 같은 경로에 `[{id, ...변경 필드}]`를, 삭제할 때는 `[{id, delete: true}]`를 포함해 한 트랜잭션으로 저장합니다. URL의 ID는 목록 첫 항목의 ID와 같아야 합니다.
- 공통 콘텐츠는 `categories`, `staff_calls`, `quiz_questions`, `weather`, `rules` 이름으로 조회할 수 있습니다. 카테고리·룰렛 화면은 각각의 전용 API를 사용합니다.

## 기타 등록 경로

| 방식 | 경로 | 기능 |
|---|---|---|
| GET | `/health` | 서버 상태 확인 |
| GET | `/api/auth/kakao/mock` | 개발용 모의 카카오 로그인(OpenAPI 목록에서 숨김) |
| WebSocket | `/api/auth/ws/{secret}` | QR 로그인 상태 수신 |

## 아직 API가 등록되지 않은 기능

테이블 누적 주문, 관리자 전용 로그인, 관리자 직원 호출 관리, 챗봇 대화 저장, 마케팅 추천 카드는 API 미등록 상태입니다. 요구사항은 담당 TODO에 남기고, 경로는 실제 라우트를 추가할 때 이 목록에 등록합니다.
