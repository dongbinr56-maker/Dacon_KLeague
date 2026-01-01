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

---

## 다음 단계

### 즉시 실행 필요
1. 데이터셋 빌더 실행 → 양성 비율 확인
2. 모델 학습 실행 → test PR-AUC + Precision/Recall 확인

### 이후 단계
- 백엔드 통합 (SessionManager)
- 프론트 표시
- 모델 튜닝/앙상블

---

## 주요 결정 사항 요약

1. **라벨 정의**: 팀 기준 (공격 주체의 미래 슈팅)
2. **좌표 스케일**: x: 0~105, y: 0~68 (미터)
3. **평가 지표**: PR-AUC 우선, Precision≥0.6 목표
4. **데이터 분할**: game_id 홀드아웃 필수
5. **모델**: 1차는 2개만 (복잡도 최소화)

---

*마지막 업데이트: 2025-01-02*

