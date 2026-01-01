# ML 모델 개발 진행 기록

## 프로젝트 개요
- **목표**: K리그 경기 데이터 기반 AI 전술 피드백 서비스
- **대회**: 데이콘 K리그 AI 챌린지
- **현재 상태**: Track2 이벤트 로그 기반 규칙 탐지 → ML 모델 도입 진행 중

---

## Phase 0: 스키마 확장 및 버그 수정 (PR#1)

### 목적
Track2 데이터의 모든 필드를 활용하고 좌표 체크 버그를 수정

### 변경 사항
1. **EventRecord 스키마 확장**
   - 추가 필드: `team_id`, `player_id`, `period_id`, `dx`, `dy` (모두 Optional)
   - 기본값 처리로 기존 코드 호환성 유지

2. **Track2 로더 개선**
   - CSV에서 새 필드 읽기
   - `dx`, `dy` 자동 계산 (CSV에 없을 경우)

3. **좌표 체크 버그 수정**
   - `if ev.end_x and ev.end_x > 70` → `if ev.end_x is not None and ev.end_x > 70`
   - 좌표가 0인 경우 False 처리되던 문제 해결

### 증빙
- 컴파일 검증: `python3 -m compileall backend/app` 통과
- 변경 파일: 3개 (29 insertions, 5 deletions)

---

## Phase 1: EDA (PR#2)

### 목적
Track2 데이터의 실제 분포와 특성 파악

### 주요 발견
1. **좌표 스케일 확정**
   - x축: 0~105 (피치 길이, 미터)
   - y축: 0~68 (피치 폭, 미터)
   - 임계값 검증: final_third=70, penalty_area=88 적절

2. **Shot 이벤트 통계**
   - 총 4,381개 (전체의 0.76%)
   - 게임당 평균 22.1개
   - period 2에 더 많음 (2,601 vs 1,780)

3. **team_id**
   - 모든 게임이 2팀 (198게임)
   - 결측 없음

4. **type_name 분포**
   - Pass: 178,582 (30.8%)
   - Pass Received: 167,531 (28.9%)
   - Carry: 88,739 (15.3%)
   - Shot: 4,381 (0.76%)

### 산출물
- `EDA/eda_track2_summary.json`: 분석 결과 요약
- `EDA/eda_track2_report.md`: 마크다운 리포트

---

## Phase 2: 데이터셋 빌더 (PR#3)

### 목적
`will_have_shot` (10초 내 슈팅 발생) 라벨 데이터셋 생성

### 설계 결정
1. **윈도우 설정**
   - Feature window: 45초 (과거 ~ 현재)
   - Label lookahead: 10초 (미래)
   - Stride: 5초

2. **라벨 정의 (팀 기준)**
   - 현재 시점 t에서 마지막 이벤트의 `team_id` (=공격 주체) 기준
   - 미래 10초 내 그 팀의 Shot 발생 여부
   - 이유: 서비스적으로 "누가 곧 슈팅하나"가 의미 있고, 알림 해석이 깔끔

3. **좌표 임계값 (EDA 결과 반영)**
   - final_third: 70 (=105×2/3)
   - penalty_area: 88 (=105-16.5, 실무적)
   - 채널 분할: left=22.7 (=68/3), right=45.3 (=68×2/3)

4. **피처 세트**
   - 기본 통계: event_count, time_span, event_rate
   - 타입 카운트: Pass, Carry, Shot, Duel, Interception 등
   - 성공률: successful_count, unsuccessful_count, success_rate
   - 공간 피처: mean_dx, mean_dy, forward_ratio, 채널 분포
   - 침투 지표: final_third_entries, penalty_area_entries
   - 볼 소유: possession_changes

### 산출물
- `artifacts/will_have_shot_dataset.parquet`
- `artifacts/feature_columns.json`
- game-level 양성 비율 통계

### 데이터셋 빌드 결과 (실행 완료)

**전체 통계:**
- 총 샘플 수: 122,656개
- 양성 샘플: 5,657개 (4.61%)
- 음성 샘플: 116,999개 (95.39%)

**Game-level 양성 비율 분포:**
- 평균: 4.62%
- 최대: 8.76%
- 최소: 1.56%
- 0% 양성 게임: 0개 (모든 게임에 양성 샘플 존재)
- >10% 양성 게임: 0개 (불균형은 있으나 극단적이지 않음)

**분석:**
- 이벤트 기준 0.76% → 윈도우 기준 4.61%로 증가 (예상됨)
- 클래스 불균형이 있으나 `class_weight="balanced"`로 처리 가능
- 모든 게임에 양성 샘플이 있어 데이터 분할에 문제 없음

---

## Phase 3: 모델 학습 (PR#4)

### 목적
`will_have_shot` 예측 모델 학습 및 평가

### 설계 결정
1. **평가 지표 (우선순위)**
   - 1순위: PR-AUC (불균형 데이터에 적합)
   - 2순위: ROC-AUC
   - 운영 지표: Precision@Threshold (F1 최대 + Precision≥0.6)

2. **데이터 분할**
   - game_id 홀드아웃 (시간 누수 방지)
   - train/val/test 모두 game_id 단위

3. **모델 (1차 베이스라인)**
   - LogisticRegression (class_weight="balanced")
   - HistGradientBoostingClassifier
   - 앙상블은 이후 단계

4. **산출물 포함 정보**
   - feature_columns
   - window_sec, lookahead_sec, stride_sec
   - threshold (F1 최대, Precision≥0.6)
   - metrics (PR-AUC, Precision, Recall, F1)
   - train/test game_id 목록

### 모델 학습 결과 (실행 완료)

**모델 비교:**
- LogisticRegression: Val PR-AUC 0.0696 (선택됨)
- HistGradientBoostingClassifier: Val PR-AUC 0.0647

**최종 모델 (LogisticRegression) Test 성능:**
- **Test PR-AUC: 0.0627** (1순위 지표)
- Test ROC-AUC: 0.6203
- F1 최대 threshold 기준:
  - Precision: 0.0641
  - Recall: 0.5740
  - F1: 0.1153
- Precision≥0.6 threshold: 달성 실패 (최대 0.0622)

**분석:**
- PR-AUC가 낮은 이유: 양성 비율이 4.61%로 낮고, 예측이 어려운 패턴
- Recall이 높은 이유: 모델이 보수적으로 예측 (낮은 threshold)
- Precision이 낮은 이유: False Positive가 많음
- 개선 방향: 피처 엔지니어링, 앙상블, 하이퍼파라미터 튜닝 필요

**산출물:**
- `artifacts/will_have_shot_model.joblib`: 학습된 모델
- `artifacts/will_have_shot_metrics.json`: 평가 지표

---

## Phase 4: 백엔드 통합 (PR#5)

### 목적
ML 모델을 SessionManager에 통합하여 실시간 예측 및 알림 생성

### 구현 내용
1. **예측기 모듈 추가**
   - `backend/app/services/alerts/will_have_shot.py`: 싱글톤 예측기 클래스
   - 서버 시작 시 모델 자동 로드 (모델 파일 없으면 비활성 상태)
   - `predict_proba(features_dict) -> float` 메서드 제공

2. **SessionManager 통합**
   - `_extract_features_for_ml()`: 이벤트 윈도우에서 30개 피처 추출
   - `_evaluate_event_alerts()`에 ML 예측 블록 추가
   - 쿨다운 15초 적용 (과도한 연속 알림 방지)
   - 예외 처리: ML 예측 실패해도 서비스 정상 동작

3. **알림 생성**
   - `pattern_type="will_have_shot"` 지원
   - `Severity.high`로 설정
   - metrics에 `shot_probability`, `lead_time_seconds` 포함
   - claim/recommendation/risk 텍스트 자동 생성

### 주요 설계 결정
- **Fallback 유지**: 모델 파일 없으면 규칙 기반만 동작
- **최소 침습**: 기존 코드 구조 유지, ML 블록만 추가
- **에러 안전성**: 예외 발생해도 서비스 중단 없음

---

## Phase 5: 프론트 표시 (PR#6)

### 목적
`will_have_shot` 알림을 프론트엔드에 표시

### 구현 내용
1. **AlertsPanel.tsx 개선**
   - `getPatternLabel()`에 "10초 내 슈팅" 라벨 추가
   - 확률 표시: `evidence.metrics["shot_probability"].value` 접근
   - 소수점 1자리로 표시 (예: "예측 확률: 6.4%")

2. **UI/UX**
   - 기존 알림 패널과 동일한 스타일 유지
   - 확률은 accent 색상으로 강조
   - 패턴 필터에 자동 포함

### 사용자 경험
- 알림 목록에서 "10초 내 슈팅" 패턴 확인 가능
- 확률 값으로 예측 신뢰도 파악
- 클릭 시 상세 정보 (claim/recommendation/risk) 확인

---

## 다음 단계

### 모델 개선 (향후)
- 피처 엔지니어링 (시퀀스 피처, 시간적 패턴)
- 앙상블 모델 (LogisticRegression + HistGradientBoosting)
- 하이퍼파라미터 튜닝
- Precision 목표 달성 (현재 0.064 → 0.6 목표)

### 추가 라벨 (향후)
- `will_have_goal` (슈팅 → 골)
- `will_have_turnover` (볼 소유 변화)
- `will_enter_final_third` (파이널서드 진입)

---

## 주요 결정 사항 요약

1. **라벨 정의**: 팀 기준 (공격 주체의 미래 슈팅)
2. **좌표 스케일**: x: 0~105, y: 0~68 (미터)
3. **평가 지표**: PR-AUC 우선, Precision≥0.6 목표
4. **데이터 분할**: game_id 홀드아웃 필수
5. **모델**: 1차는 2개만 (복잡도 최소화)

---

*마지막 업데이트: 2025-01-02*

