# 외부 데이터셋 통합 계획

**작성일**: 2026-01-02 (Asia/Seoul)  
**상태**: 다운로드 완료, 검증 및 통합 진행 중

---

## 다운로드 완료된 데이터셋

### ✅ 1. StatsBomb Open Data
- **위치**: `~/Downloads/football_datasets/open-data`
- **용도**: 압박(Pressure) 이벤트, 오프사이드 이벤트
- **특징**: `under_pressure`, `counterpress` 속성 포함
- **통합 우선순위**: 🔴 높음 (압박 이벤트가 Track2에 없음)

### ✅ 2. SkillCorner OpenData
- **위치**: `~/Downloads/football_datasets/opendata`
- **용도**: 선수/공 추적 좌표 + 이벤트 + 공격/수비 세그먼트
- **특징**: 프레임별 좌표 데이터
- **통합 우선순위**: 🟡 중간 (추적 데이터로 오프사이드 라인 계산 가능)

### ✅ 3. Metrica Sports Sample Data
- **위치**: `~/Downloads/football_datasets/sample-data`
- **용도**: 피처 설계/검증(pressure, spacing, speed) 레시피
- **특징**: 교육/연구용 샘플, 경기 수 적음
- **통합 우선순위**: 🟢 낮음 (프로토타입용)

### ✅ 4. SoccerNet Tracking
- **위치**: `~/Downloads/football_datasets/sn-tracking`
- **용도**: 방송 카메라 기반 트래킹 벤치마크
- **특징**: 12경기, 트래킹 데이터
- **통합 우선순위**: 🟢 낮음 (R&D용)

---

## 통합 단계별 계획

### Phase 1: 데이터 검증 및 스키마 분석 (현재)

**목표**: 각 데이터셋의 스키마 확인 및 Track2와의 매핑 가능성 분석

**작업**:
1. ✅ 다운로드 완료
2. ✅ 검증 스크립트 작성 (`scripts/validate_external_datasets.py`)
3. 🔄 검증 실행 및 결과 분석
4. ⏳ 스키마 문서화
5. ⏳ Track2 매핑 테이블 작성

**산출물**:
- `artifacts/external_datasets_validation.json`: 검증 결과
- `docs/presentation/EXTERNAL_DATASETS_SCHEMA.md`: 스키마 문서

---

### Phase 2: StatsBomb 통합 (1순위)

**목표**: StatsBomb의 압박 이벤트를 Track2 이벤트 로그에 통합

**작업**:
1. StatsBomb 이벤트 데이터 파싱
2. Track2와 시간/게임 매칭
3. 압박 이벤트를 Track2 스키마에 매핑
4. 압박 피처 생성 (이벤트 기반)

**예상 효과**:
- 압박 프록시 대신 실제 압박 이벤트 사용 가능
- `will_have_shot` 모델 성능 개선 기대

**산출물**:
- `scripts/integrate_statsbomb.py`: 통합 스크립트
- `00_data/Track2/enhanced_events.csv`: 압박 이벤트 포함 확장 데이터

---

### Phase 3: SkillCorner 통합 (2순위)

**목표**: 추적 좌표 데이터로 오프사이드 라인 및 압박 강도 계산

**작업**:
1. SkillCorner 추적 데이터 파싱
2. Track2와 시간/게임 매칭
3. 오프사이드 라인 계산 (최종 수비수 x좌표)
4. 압박 강도 계산 (공 주변 수비수 거리/속도)
5. 추적 기반 피처 생성

**예상 효과**:
- 오프사이드 라인 피처 추가
- 정량적 압박 강도 피처 추가
- `will_have_shot` 모델 성능 개선 기대

**산출물**:
- `scripts/integrate_skillcorner.py`: 통합 스크립트
- `scripts/calculate_offside_line.py`: 오프사이드 라인 계산
- `scripts/calculate_pressure_intensity.py`: 압박 강도 계산

---

### Phase 4: Metrica/SoccerNet 활용 (R&D)

**목표**: 피처 설계 레시피 및 검증

**작업**:
1. Metrica 샘플 데이터로 pressure/spacing/speed 피처 설계
2. SoccerNet으로 트래킹 파이프라인 검증
3. Track2에 적용 가능한 피처 추출

---

## 통합 우선순위

1. **StatsBomb** (즉시)
   - 압박 이벤트가 Track2에 없어서 가장 높은 우선순위
   - 이벤트 기반이라 통합이 상대적으로 쉬움

2. **SkillCorner** (단기)
   - 추적 데이터로 오프사이드 라인/압박 강도 계산
   - 시간 매칭 및 좌표 변환 필요

3. **Metrica/SoccerNet** (중기)
   - R&D 및 피처 설계 레시피
   - 프로토타입 검증용

---

## 다음 작업

1. ✅ 데이터셋 다운로드 완료
2. ✅ 검증 스크립트 작성 완료
3. 🔄 검증 실행 및 결과 분석
4. ⏳ StatsBomb 통합 스크립트 작성
5. ⏳ Track2 매핑 테이블 작성

---

## 참고

- 검증 결과: `artifacts/external_datasets_validation.json`
- 다운로드 가이드: `docs/presentation/DATASET_DOWNLOAD_GUIDE.md`
- GPT 데이터 전략: `docs/presentation/GPT_DATA_STRATEGY.md`

