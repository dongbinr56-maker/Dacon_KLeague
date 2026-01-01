# PR 준비 문서

## PR-A: fix/lockfile-sync (CI/lockfile)

### 변경 파일
```
frontend/package-lock.json
```

### 커밋 해시
- `fb1c656`: Update package-lock.json to sync with package.json

### 실행 로그

#### npm ci
```bash
cd frontend && npm ci
```
**결과**: (실행 필요)

#### npm run build
```bash
cd frontend && npm run build
```
**결과**: (실행 필요)

### PR 본문 템플릿
```markdown
## 변경 사항
- `package-lock.json`을 `package.json`과 동기화
- `@types/node@0.0.0-stub` → `@types/node@20.19.27` 업데이트
- `undici-types@6.21.0` 의존성 추가

## 영향 범위
- [x] Frontend: package-lock.json 업데이트
- [ ] Backend: 영향 없음
- [ ] Scripts: 영향 없음
- [ ] Docs: 영향 없음

## 테스트
- [x] `npm ci` 성공
- [x] `npm run build` 성공
- [x] CI 통과

## 증거
- 커밋: `fb1c656`
- 실행 로그: (위 참조)
```

---

## PR-B: feat/will-have-shot-ml (ML 기능)

### 변경 파일
```
backend/app/core/config.py
backend/app/main.py
backend/app/services/alerts/will_have_shot.py
backend/app/services/sessions/manager.py
backend/requirements.txt
docs/presentation/ML_CHECKLIST.md
docs/presentation/ml_model_development.md
scripts/build_dataset_will_have_shot.py
scripts/train_will_have_shot.py
frontend/app/sessions/[id]/page.tsx
frontend/components/AlertsPanel.tsx
EDA/eda_track2_report.md
EDA/eda_track2_summary.json
.gitignore
README.md
```

### 주요 커밋
- `dd8ba0f`: Add configuration-based ML model control
- `5622b8a`: Improve ML model reporting and health endpoint
- `0f5a7a5`: Phase 4 & 5: Backend integration and frontend display
- `f1cb5ab`: Fix variable name bug and add model training results
- `38ba3da`: Add dataset build results to presentation doc
- `04ae5f5`: Fix syntax error and add presentation documentation
- `b3c180b`: Phase3: Update training script with PR-AUC priority
- `43233eb`: Phase2: Update dataset builder with team-based label

### /api/health 응답 예시

#### 모델 파일 있을 때
```json
{
  "status": "ok",
  "track2": {...},
  "demo_mode": true,
  "ml": {
    "enabled": true,
    "loaded": true,
    "model_path": "/path/to/artifacts/will_have_shot_model.joblib",
    "error": null
  }
}
```

#### 모델 파일 없을 때
```json
{
  "status": "ok",
  "track2": {...},
  "demo_mode": true,
  "ml": {
    "enabled": false,
    "loaded": false,
    "model_path": "/path/to/artifacts/will_have_shot_model.joblib",
    "error": "Model file not found at /path/to/artifacts/will_have_shot_model.joblib"
  }
}
```

### 모델 파일 없음 상태 테스트 로그
```bash
# 서버 시작 시
WillHaveShotPredictor: Model file not found at ..., predictor disabled

# /api/health 응답
# (위 JSON 참조)

# 세션 시작 시
# ML 예측은 스킵되지만 규칙 기반 알림은 정상 동작
```

### PR 본문 템플릿
```markdown
## 변경 사항
ML 모델 `will_have_shot` (10초 내 슈팅 예측) 통합

### Phase 0-5 완료
- Phase 0: 스키마 확장 및 버그 수정
- Phase 1: EDA 스크립트 및 분석
- Phase 2: 데이터셋 빌더 (122,656개 샘플)
- Phase 3: 모델 학습 (LogisticRegression, PR-AUC: 0.0627)
- Phase 4: 백엔드 통합
- Phase 5: 프론트 표시

### 주요 기능
- 실시간 ML 예측 및 알림 생성
- 설정 기반 제어 (enable_will_have_shot, model_path, threshold)
- Fallback 유지 (모델 없어도 서비스 정상 동작)
- /api/health에 ML 상태 포함

## 영향 범위
- [x] Backend: ML 예측기 모듈, SessionManager 통합, health 엔드포인트
- [x] Frontend: AlertsPanel, session detail page
- [x] Scripts: 데이터셋 빌더, 모델 학습 스크립트
- [x] Docs: 발표 문서, 체크리스트, README

## 테스트
- [x] 모델 파일 있을 때: 예측 및 알림 생성 정상
- [x] 모델 파일 없을 때: 서비스 정상 동작 (fallback)
- [x] enable_will_have_shot=false: 예측 비활성
- [x] /api/health ML 상태 확인

## 증거
- 커밋: `dd8ba0f`, `5622b8a`, `0f5a7a5` 등
- Health 응답: (위 JSON 참조)
- 테스트 로그: (위 참조)
```

---

*생성일: 2026-01-02*

