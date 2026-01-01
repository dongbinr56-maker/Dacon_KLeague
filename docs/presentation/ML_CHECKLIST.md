# ML 모델 개발 남은 작업 체크리스트 (발표/리뷰용 DoD 포함)

## 원칙

* 모든 항목은 "완료(체크)" 시점에 **증거 링크/해시/로그**가 반드시 첨부되어야 한다.
* 증거 없는 완료 표시는 금지한다.
* PR은 "목적 단위"로 분리한다(락파일/CI vs ML 기능).

---

## 🔴 즉시 필요 (발표/리뷰 준비)

### 1) PR 분리 및 브랜치 정리

#### PR-A (CI/lockfile)
- [ ] `package-lock.json` 관련 커밋을 `fix/lockfile-sync`로 분리하고 PR 생성

  **DoD**: PR 본문에 아래 3개 포함
  1. `git diff --name-only origin/main...HEAD`
  2. `cd frontend && npm ci` 실행 로그(요약)
  3. `cd frontend && npm run build` 실행 로그(요약)

  **증거**: PR 링크, 커밋 해시, 실행 로그 캡처

#### PR-B (ML 기능)
- [ ] ML 기능을 `feat/will-have-shot-ml` 브랜치로 분리하고 PR 생성

  **DoD**: PR 본문에 아래 3개 포함
  1. `git diff --name-only origin/main...HEAD`
  2. `/api/health`에 ML 상태 포함 스크린샷/응답 예시
  3. "모델 파일 없음" 상태에서 서비스 정상 동작 확인 로그

  **증거**: PR 링크, 커밋 해시, health 응답, 테스트 로그

#### PR 영향 범위 명시
- [ ] PR 영향 범위 명시(필수 템플릿 적용)

  **DoD**: PR 본문에 "Backend/Frontend/Scripts/Docs 영향" 체크섹션 존재

  **증거**: PR 본문 링크

---

### 2) 설정 기반 제어 (백엔드)

#### 설정 추가
- [ ] `backend/app/core/config.py`에 설정 추가
  - `enable_will_have_shot: bool`
  - `will_have_shot_model_path: Optional[str]`
  - `will_have_shot_threshold: Optional[float]`

  **DoD**: `get_settings()`로 읽히고, 기본값/None 처리로 서버 크래시가 없어야 함

  **증거**: 관련 커밋 해시

#### 예측기 수정
- [ ] `WillHaveShotPredictor`가 설정을 읽어 동작하도록 수정

  **DoD**:
  - enable=false → 예측/알림 생성 비활성
  - model_path=None 또는 로드 실패 → "비활성 + 에러 메시지"로 health에만 표시

  **증거**: health 응답 2종(enable on/off) 캡처

#### 문서화
- [ ] `.env.example`에 신규 설정 반영

  **DoD**: README/문서에 "ML 켜는 법" env 3줄로 요약

  **증거**: 커밋 해시, 문서 링크

---

### 3) 발표용 메트릭(운영 관점) 고정

#### 학습 리포트 개선
- [ ] `train_will_have_shot.py` 출력/리포트에 운영 지표 포함
  - threshold sweep (Precision/Recall/F1)
  - Precision@K (K=10, 20)
  - 경기당 예상 알림 수(쿨다운 포함)

  **DoD**: `artifacts/will_have_shot_metrics.json`에 위 항목이 구조화되어 저장

  **증거**: metrics.json 첨부(요약), 커밋 해시

> **주의**: "Precision≥0.6 목표"는 현재 결과와 괴리가 커서 발표용 핵심 KPI로 사용 금지. 운영지표(알림 예산/Top-K)로 설득한다.

#### /api/health ML 상태 추가
- [ ] (검증 대기) `/api/health`에 ML 상태 포함

  **DoD**: 
  - `ml.enabled`, `ml.loaded`, `ml.model_path`, `ml.error` 필드 포함
  - 모델 파일 없을 때도 정상 응답 (에러 필드에 메시지)

  **증거**: PR 링크/커밋 해시, health 응답 예시 (모델 있음/없음 2종)

---

## 🟡 모델 개선 (단기: 1–2주, 성능 향상)

### 4) 피처 엔지니어링 (우선순위 높은 것만)

- [ ] 시퀀스 피처(최근 N개 이벤트 타입/결과)
- [ ] 이벤트 간격 통계(mean/std)
- [ ] 최근 10초 vs 이전 10초 비교 피처(공격 강도 변화)
- [ ] 피처 중요도/중복 제거(상관관계)

  **DoD**:
  - `feature_columns.json` 버전 업데이트
  - PR-AUC 및 Precision@K가 베이스라인 대비 개선(수치 명시)

  **증거**: 전/후 성능표, 커밋 해시

---

### 5) 하이퍼파라미터 튜닝

- [ ] LogisticRegression / HGB 튜닝(그리드 또는 Optuna)
- [ ] game_id 그룹 기반 CV로 안정성 확인

  **DoD**: 최적 파라미터/성능/학습시간 테이블 문서화

  **증거**: 튜닝 결과 테이블, 커밋 해시

---

### 6) 앙상블

- [ ] Voting(soft/hard) 비교
- [ ] Stacking 비교

  **DoD**: 예측 시간(서빙)과 성능의 trade-off 문서화

  **증거**: 성능 비교표, 커밋 해시

---

## 🟢 운영 정책 개선 (발표 후 우선 적용)

### 7) 알림 예산(Top-K) 시스템

- [ ] `max_alerts_per_game`, 하프별 K 제한
- [ ] 우선순위: 확률 상위 K만 발행

  **DoD**: "threshold 기반"과 "Top-K 기반" 두 모드 지원(설정으로 선택)

  **증거**: 데모 로그(알림 수 제한 동작), 커밋 해시

---

### 8) 쿨다운 정책 정교화

- [ ] 패턴별 쿨다운 설정화
- [ ] 확률 기반 예외(예: p>0.8이면 완화)

  **DoD**: 설정 파일로 제어 가능 + 테스트 케이스 2개 이상

  **증거**: 테스트 로그, 커밋 해시

---

## 🔵 프론트엔드 개선 (발표 후)

### 9) 필터/정렬

- [ ] 확률 정렬, 패턴 그룹화, 시간대 필터

  **DoD**: UX가 깨지지 않는 최소 구현(스크린샷)

  **증거**: 스크린샷/커밋

---

## 📝 작업 기록

### 완료된 작업 (검증 대기)
- [ ] (검증 대기) `/api/health` ML 상태 추가
  - **증거 필요**: PR 링크/커밋 해시, health 응답 예시 (모델 있음/없음 2종)

- [ ] (검증 대기) 학습 리포트 개선 (threshold sweep, Precision@K, 경기당 알림 수)
  - **증거 필요**: PR 링크/커밋 해시, metrics.json 요약

### 진행 중인 작업
- (없음)

### 다음 작업 예정
- PR 분리
- 설정 기반 제어 추가

---

*마지막 업데이트: 2026-01-02 (Asia/Seoul)*

