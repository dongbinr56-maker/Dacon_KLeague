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
  1. `git diff --name-only origin/main...HEAD` ✅ (준비됨: `docs/presentation/PR_PREPARATION.md`)
  2. `cd frontend && npm ci` 실행 로그(요약) ✅
     ```
     added 29 packages in 2s
     ```
  3. `cd frontend && npm run build` 실행 로그(요약) ✅
     ```
     ✓ Compiled successfully
     ✓ Generating static pages (4/4)
     Route (app)                              Size     First Load JS
     ┌ ○ /                                    5.84 kB        96.3 kB
     └ ƒ /sessions/[id]                       7.25 kB        97.7 kB
     ```

  **증거**: 
  - 커밋 해시: `fb1c656`
  - PR 템플릿: `docs/presentation/PR_PREPARATION.md`
  - 실행 로그: 위 참조 (2026-01-02 실행)

#### PR-B (ML 기능)
- [ ] ML 기능을 `feat/will-have-shot-ml` 브랜치로 분리하고 PR 생성

  **DoD**: PR 본문에 아래 3개 포함
  1. `git diff --name-only origin/main...HEAD` ✅ (준비됨: `docs/presentation/PR_PREPARATION.md`)
  2. `/api/health`에 ML 상태 포함 스크린샷/응답 예시 ✅ (준비됨: JSON 예시 포함)
  3. "모델 파일 없음" 상태에서 서비스 정상 동작 확인 로그 ⏳ (서버 실행 후 수집)

  **증거**: 
  - 커밋 해시: `dd8ba0f`, `5622b8a`, `0f5a7a5` 등
  - PR 템플릿: `docs/presentation/PR_PREPARATION.md`
  - Health 응답 예시: (위 문서 참조)
  - 테스트 로그: (서버 실행 후 수집)

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
- [x] `train_will_have_shot.py` 출력/리포트에 운영 지표 포함
  - threshold sweep (Precision/Recall/F1) ✅
  - Precision@K (K=10, 20) ✅
  - 경기당 예상 알림 수(쿨다운 포함) ✅

  **DoD**: `artifacts/will_have_shot_metrics.json`에 위 항목이 구조화되어 저장 ✅

  **증거**: 
  - 커밋 `dd8ba0f`, `scripts/train_will_have_shot.py` (라인 185-228, 383-394)
  - `operational_metrics` 섹션에 threshold_sweep, precision_at_10/20, alerts_per_game_at_best_threshold 포함
  - 다음 학습 실행 시 metrics.json에 저장됨

> **주의**: "Precision≥0.6 목표"는 현재 결과와 괴리가 커서 발표용 핵심 KPI로 사용 금지. 운영지표(알림 예산/Top-K)로 설득한다.

#### /api/health ML 상태 추가
- [x] `/api/health`에 ML 상태 포함

  **DoD**: 
  - `ml.enabled`, `ml.loaded`, `ml.model_path`, `ml.error` 필드 포함 ✅
  - 모델 파일 없을 때도 정상 응답 (에러 필드에 메시지) ✅

  **증거**: 
  - 커밋 `5622b8a`, `backend/app/main.py` (라인 72-86)
  - `ml_status` 딕셔너리에 enabled, loaded, model_path, error 필드 포함
  - health 응답 테스트 필요 (서버 실행 후)

---

## 🟡 모델 개선 (단기: 1–2주, 성능 향상)

### 4) 피처 엔지니어링 (우선순위 높은 것만)

- [x] 시퀀스 피처(최근 N개 이벤트 타입/결과) ✅
- [x] 이벤트 간격 통계(mean/std) ✅
- [x] 최근 10초 vs 이전 10초 비교 피처(공격 강도 변화) ✅
- [x] 피처 중요도/중복 제거(상관관계) ✅ (분석 완료)

  **DoD**:
  - `feature_columns.json` 버전 업데이트 ✅ (29개 → 54개 피처로 증가)
  - PR-AUC 및 Precision@K가 베이스라인 대비 개선(수치 명시) ⏳ (학습 실행 중)

  **증거**: 
  - 커밋 `bad93bb`, `scripts/build_dataset_will_have_shot.py` (라인 147-239)
  - 추가된 피처:
    * 시퀀스: `recent_5/10_{pass|carry|shot|duel}_count`, `recent_5/10_success_rate`, `recent_5/10_mean_end_x`
    * 간격 통계: `event_interval_mean/std/min/max`
    * 비교 피처: `recent_10s_*`, `previous_10s_*`, `*_change` (event_count, end_x, success_rate)
  - 전/후 성능표: (다음 학습 실행 후 업데이트)

---

### 5) 하이퍼파라미터 튜닝

- [x] LogisticRegression / HGB 튜닝(그리드 또는 RandomizedSearch) ✅
- [x] game_id 그룹 기반 CV로 안정성 확인 ✅

  **DoD**: 최적 파라미터/성능/학습시간 테이블 문서화 ⚠️ (학습 완료, metrics.json에 저장됨, 하지만 목표 지표 미달로 재튜닝 필요)

  **증거**: 
  - 커밋 `bad93bb`, `scripts/train_will_have_shot.py` (라인 92-177)
  - LogisticRegression: GridSearchCV (C, solver, class_weight)
  - HistGradientBoostingClassifier: RandomizedSearchCV (max_iter, learning_rate, max_depth, min_samples_leaf)
  - GroupShuffleSplit 기반 CV로 데이터 누수 방지
  - 튜닝 결과 테이블: (다음 학습 실행 후 업데이트)

---

### 6) 앙상블

- [x] Voting(soft) 구현 ✅
- [x] Stacking 구현 ✅

  **DoD**: 예측 시간(서빙)과 성능의 trade-off 문서화 ⚠️ (학습 완료, Stacking이 최고 성능이지만 목표 지표 미달로 개선 필요)

  **증거**: 
  - 커밋 `bad93bb`, `scripts/train_will_have_shot.py` (라인 179-230)
  - VotingClassifier (soft voting): LR + HGB
  - StackingClassifier: LR + HGB → LogisticRegression (final estimator)
  - Pipeline을 사용하여 LR의 scaled 데이터 요구사항 처리
  - 성능 비교표: (다음 학습 실행 후 업데이트)

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

### 완료된 작업

#### 설정 기반 제어 (완료)
- ✅ `backend/app/core/config.py`에 ML 설정 추가 (커밋 `dd8ba0f`)
- ✅ `WillHaveShotPredictor`가 설정을 읽도록 수정 (커밋 `dd8ba0f`)
- ✅ README에 ML 설정 섹션 추가 (커밋 `dd8ba0f`)

#### /api/health ML 상태 추가 (완료)
- ✅ `/api/health`에 ML 상태 포함 (커밋 `5622b8a`)
- **증거**: `backend/app/main.py` (라인 72-86), `ml_status` 딕셔너리 포함
- **테스트 필요**: 서버 실행 후 health 응답 확인 (모델 있음/없음 2종)

#### 학습 리포트 개선 (완료)
- ✅ threshold sweep, Precision@K, 경기당 알림 수 추가 (커밋 `dd8ba0f`)
- **증거**: `scripts/train_will_have_shot.py` (라인 185-228, 383-394)
- **테스트 필요**: 다음 학습 실행 시 metrics.json에 `operational_metrics` 섹션 확인

### 진행 중인 작업
- ✅ 피처 엔지니어링 완료 (29→54개 피처)
- ✅ 하이퍼파라미터 튜닝 구현 완료 (GridSearchCV, RandomizedSearchCV)
- ✅ 앙상블 모델 구현 완료 (Voting, Stacking)
- ⚠️ 모델 학습 완료 (목표 지표 미달)
  - 현재 성능: PR-AUC 0.0829, Precision@10 0.20, 경기당 알림 95.42개
  - 목표: PR-AUC ≥ 0.15, Precision@10 ≥ 0.40, 경기당 알림 10-20개
  - 상태: 베이스라인 대비 개선(+32%)했으나 운영 목표 미달 → 개선 필요
- 🔄 RuntimeWarning 해결 중 (피처 클리핑 및 검증 강화)

### 현재 모델 성능 (2026-01-02 기준)
- **PR-AUC**: 0.0829 (목표: ≥0.15) ❌
- **ROC-AUC**: 0.6688
- **Precision@10**: 0.20 (목표: ≥0.40) ❌
- **Precision@20**: 0.15
- **경기당 알림 수**: 95.42개 (목표: 10-20개) ❌
- **베이스라인 대비**: +32% 개선했으나 운영 목표 미달

### 진행 상황 요약 (2026-01-02)

#### 완료된 작업 ✅
1. **RuntimeWarning 해결**
   - 피처 클리핑 및 검증 강화 완료
   - 무한대/이상치 처리 개선 완료
   - 커밋: `0b53632`

2. **피처 중요도 분석 및 선택**
   - 모델의 feature_importances_ 또는 coefficients 분석 완료
   - 상관관계 높은 피처 쌍 식별 완료
   - 상위 19개 피처 선택 (누적 중요도 80%)
   - 분석 스크립트: `scripts/analyze_feature_importance.py`
   - 커밋: `f301709`

3. **GPT 데이터 전략 리서치 문서화**
   - AIHub 데이터셋 구성 및 활용 방안
   - 무료/공개 추적 데이터셋 추천
   - Track2 이벤트 로그만으로 가능한 보완 방법
   - PR-AUC/Precision@10 개선 전략 우선순위
   - 문서: `docs/presentation/GPT_DATA_STRATEGY.md`
   - 커밋: `142bf24`

#### 진행 중인 작업 🔄
1. **피처 선택 후 재학습** (완료, 성능 하락 확인)
   - 선택된 19개 피처로 데이터셋 필터링 ✅
   - 학습 스크립트에 `--selected-features-path` 옵션 추가 ✅
   - 모델 재학습 완료 (하이퍼파라미터 튜닝 + 앙상블 포함) ✅
   - **결과**: 성능 하락 확인
     - PR-AUC: 0.0829 → 0.0713 (-14% 하락)
     - Precision@10: 0.20 → 0.20 (동일)
     - 경기당 알림: 95.42 → 216.45개 (더 악화)
   - **분석 필요**: 피처 축소가 오히려 성능을 떨어뜨림
   - 커밋: `142bf24`

#### 다음 작업 예정 (우선순위) - GPT 답변 반영

1. ✅ **시퀀스 피처 다층화** (완료)
   - 여러 시간 범위(1초/5초/10초/20초) 동시 반영 ✅
   - 윈도우 기반 집계 생성 (이동 평균/분산/최대/최소) ✅
   - 각 윈도우별: 이벤트 수, 타입별 카운트, 성공률, 평균/최대 x좌표, 간격 통계 ✅
   - 커밋: `2ccccd3`

2. ✅ **상호작용 피처 생성** (완료)
   - 피처 쌍의 곱/비율/차이 생성 ✅
   - 상호작용 피처 8개 추가 (pass_success_interaction, final_third_event_density 등) ✅
   - 커밋: `2ccccd3`

3. **데이터셋 재빌드** (진행 중)
   - 새로운 피처로 데이터셋 재생성
   - 예상 피처 수: 53개 → 약 100개 이상 (시퀀스 다층화 + 상호작용)

4. **모델 재학습** (다음 단계)
   - 새로운 피처로 모델 재학습
   - 성능 비교 (PR-AUC, Precision@10)
   - 목표: PR-AUC ≥0.15, Precision@10 ≥0.40

4. **피처 선택 방법 개선** (중기)
   - Wrapper 방법 또는 SHAP 기반 재선정
   - 교차 검증 기반 선택
   - 상호작용을 반영한 중요도 측정

5. **Threshold/랭킹 후처리** (단기)
   - 경기당 알림 수 조절 (10-20개 목표)
   - Top-K 기반 알림 시스템 구현
- PR-A: package-lock.json 분리
- PR-B: ML 기능 PR 생성 및 영향 범위 명시

---

*마지막 업데이트: 2026-01-02 (Asia/Seoul)*

