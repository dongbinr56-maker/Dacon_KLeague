# E2E 작업 체크리스트

> 각 체크 항목은 완료 시 증거(명령어/로그/샘플 JSON/스크린샷 등)를 첨부한다.

## A. 프로젝트 부팅/환경
- [ ] `docker-compose up --build`가 백엔드/프론트를 에러 없이 기동한다.
- [ ] 백엔드 Health/Docs 엔드포인트 동작(`/api/health`, `/api/docs`).
- [ ] CORS가 `http://localhost:3000` 기준으로 정상(브라우저 콘솔 에러 없음).

## B. Track2 데이터 “기본 사용” 보장
- [x] 백엔드 설정에 Track2 기본 경로가 있다(ENV override 가능). *(config: events_data_path, match_info_path)*
- [x] 서버 부팅 시 Track2 파일 존재/스키마 검증, 실패 시 친절한 에러. *(main.py startup validation + health)*
- [x] 세션 생성 시 Track2의 `game_id` 기반으로 소스를 구성한다. *(event_log ingest requires game_id)*
- [x] 분석 루프가 Track2 이벤트 스트림(`time_seconds` 정렬)을 소비한다. *(EventIngest + event loop)*

## C. 입력 모드/세션 플로우(프론트/백엔드)
- [x] StartScreen에 `Event Log (Track2)` 입력 모드가 존재한다.
- [x] `game_id` 선택 UI가 있고, 선택값이 백엔드로 전달된다.
- [ ] Start → AnalysisScreen 전환이 정상.
- [ ] WS 연결 및 세션 상태/알림이 화면에 갱신된다.

## D. Offline-RealTime 이벤트 루프(핵심)
- [ ] 이벤트는 `time_seconds` 오름차순으로 처리된다.
- [ ] 재생 속도를 파라미터로 조절 가능하다(예: 5x/10x).
- [ ] 롤링 윈도우(예: 45초)를 유지한다.
- [ ] 30~60초 내 Alert가 최소 1개 이상 발생한다(임계값 포함).
- [ ] stop 시 ingest/loop/task가 종료되어 리소스 누수 없음.

## E. Alert 스키마/일관성
- [ ] `ts_start/ts_end`는 경기 시작 기준 초(sec)로 통일(UNIX timestamp 금지).
- [ ] severity는 `low|medium|high` Enum 준수.
- [ ] Alert payload에 metrics가 최소 1~2개 포함된다.

## F. Evidence 2개 강제 생성(데이터 기반)
- [ ] Alert당 Evidence 최소 2개 생성
  - [ ] (A) `clip_{alert_id}.mp4`: 이벤트 피치 애니메이션 10초
  - [ ] (B) `overlay_{alert_id}.png`: 대표 프레임 + 오버레이
- [ ] Evidence 경로 규칙 고정 `{evidence_path}/{session_id}/clip_{alert_id}.mp4` 및 `overlay_{alert_id}.png`
- [ ] Evidence URL 규칙 고정 `/api/evidence/{session_id}/clip_{alert_id}.mp4` 및 `overlay_{alert_id}.png`

## G. Evidence 서빙/404 제거
- [x] FastAPI가 `/api/evidence`를 StaticFiles로 서빙한다.
- [ ] 프론트 Evidence 링크 클릭 시 404가 없다.
- [ ] mp4 재생/다운로드 및 png 로드가 정상.

## H. 업로드/세션 저장 안정성(최소)
- [ ] 업로드 인덱스가 디스크로 persist 된다(`upload_index.json`).
- [ ] 백엔드 재시작 후 `/api/uploads/{file_id}`가 404가 아니다.
- [ ] (선택) 세션 목록도 persist.

## I. 데모 시나리오(리허설 고정)
- [ ] (1) Track2 `game_id` 선택 → 세션 생성
- [ ] (2) Start → 30~60초 내 Alert 표시
- [ ] (3) Alert 클릭 → Evidence 2개 열림
- [ ] (4) 서버 재시작 → 업로드 다운로드/증거 서빙 유지

## J. 문서화/재현성
- [x] README에 데모 실행 절차(10줄 내) 명시
- [ ] 외부 데이터/모델 사용 시 `docs/external_data.md`에 출처/라이선스/스크립트 기록
- [ ] Alert 샘플 JSON 1개와 evidence 파일 경로 예시 문서화
