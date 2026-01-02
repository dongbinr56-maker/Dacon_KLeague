# 추가 데이터셋 다운로드 가이드

**작성일**: 2026-01-02 (Asia/Seoul)  
**목적**: GPT 리서치에서 추천된 무료/공개 축구 데이터셋 다운로드 방법

---

## 우선순위별 데이터셋

### 🔴 1순위: StatsBomb Open Data (압박 이벤트 포함)

**용도**: 압박(Pressure) 이벤트 데이터, 오프사이드 이벤트 포함  
**라이선스**: CC BY 4.0 (상업적 사용 가능, 출처 표기 필요)  
**데이터 용량**: 약 500MB ~ 1GB (JSON 이벤트 데이터)

**다운로드 방법**:
```bash
# GitHub에서 클론
cd ~/Downloads  # 또는 원하는 디렉토리
git clone https://github.com/statsbomb/open-data.git
cd open-data

# 구조 확인
# - data/events/ : 이벤트 데이터 (JSON)
# - data/lineups/ : 라인업 데이터
# - data/matches/ : 경기 메타데이터
```

**URL**: https://github.com/statsbomb/open-data

**데이터 구조**:
- 이벤트 데이터에 `under_pressure`, `counterpress` 속성 포함
- 오프사이드 이벤트 타입 포함
- FIFA 월드컵, 유럽 주요 리그 포함

**저장 위치 권장**: `00_data/StatsBomb/`

---

### 🟡 2순위: SkillCorner OpenData (추적 데이터)

**용도**: 선수/공 추적 좌표 + 이벤트 + 공격/수비 세그먼트  
**라이선스**: 공개 (GitHub 확인 필요)  
**데이터 용량**: 약 500MB ~ 1GB (추적 좌표 데이터 포함)

**다운로드 방법**:
```bash
cd ~/Downloads
git clone https://github.com/SkillCorner/opendata.git
cd opendata

# README 확인하여 데이터 구조 파악
cat README.md
```

**URL**: https://github.com/SkillCorner/opendata

**데이터 구조**:
- 프레임별 선수/공 좌표
- 이벤트 데이터
- 공격/수비 세그먼트(phase)

**저장 위치 권장**: `00_data/SkillCorner/`

---

### 🟡 3순위: Metrica Sports Sample Data (교육/연구용)

**용도**: 피처 설계/검증(pressure, spacing, speed) 레시피  
**라이선스**: 교육/연구용  
**데이터 용량**: 약 50MB ~ 100MB (샘플 데이터, 경기 수 적음)

**다운로드 방법**:
```bash
cd ~/Downloads
git clone https://github.com/metrica-sports/sample-data.git
cd sample-data

# 데이터 확인
ls -la
```

**URL**: https://github.com/metrica-sports/sample-data

**특징**: 경기 수가 적지만 파이프라인 프로토타입 만들기에 적합

**저장 위치 권장**: `00_data/Metrica/`

---

### 🟢 4순위: Wyscout Soccer Match Event Dataset

**용도**: Track2와 유사한 이벤트 데이터, 전이학습/사전학습  
**라이선스**: CC BY 4.0  
**데이터 용량**: 약 500MB ~ 1GB (이벤트 데이터, 다운로드 시 확인 필요)

**다운로드 방법**:
1. Figshare에서 다운로드:
   - URL: https://figshare.com/collections/Soccer_match_event_dataset/4265000
   - 브라우저에서 접속하여 다운로드
   - 또는 wget/curl 사용 (링크 확인 필요)

2. 또는 Nature 논문 페이지에서 링크 확인:
   - URL: https://www.nature.com/articles/s41597-019-0247-7

**저장 위치 권장**: `00_data/Wyscout/`

---

### 🟢 5순위: Bundesliga 통합 데이터 (7경기)

**용도**: 엘리트 경기의 이벤트 + 포지션(추적) + 메타 통합  
**라이선스**: 공개 (Nature 논문)  
**데이터 용량**: 약 2GB ~ 5GB (7경기, 이벤트+추적+메타 통합, 다운로드 시 확인 필요)

**다운로드 방법**:
1. Nature 논문 페이지 접속:
   - URL: https://www.nature.com/articles/s41597-025-04505-y
   - 논문에서 데이터 다운로드 링크 확인
   - 또는 Zenodo/Figshare 링크 확인

2. 데이터 구조:
   - 이벤트 + 포지션(추적) + 메타를 한 데이터셋으로 제공

**저장 위치 권장**: `00_data/Bundesliga/`

---

### 🔵 6순위: SoccerTrack v2 (파노라마 비디오 + 2D 좌표)

**용도**: 영상→좌표 복원/추적→전술 피처 파이프라인 R&D  
**라이선스**: 연구용 (arXiv 논문 확인)  
**데이터 용량**: 약 50GB ~ 100GB (파노라마 비디오 포함, 큰 용량, 다운로드 시 확인 필요)

**다운로드 방법**:
1. **GitHub 저장소** (권장):
   - URL: https://github.com/open-starlab/stc-2025
   - SoccerTrack Challenge 2025 공식 GitHub
   - README에서 데이터셋 다운로드 링크 확인

2. **공식 웹사이트**:
   - URL: https://sites.google.com/g.sp.m.is.nagoya-u.ac.jp/stc2025
   - "The Dataset for this challenge are SoccerTrack v2 datasets (you can download from here)"
   - 웹사이트에서 다운로드 링크 제공

3. **CodaLab 페이지**:
   - URL: https://codalab.lisn.upsaclay.fr/competitions/22532
   - 경쟁 참가자용 데이터셋 다운로드 가능

4. **논문**:
   - arXiv: https://arxiv.org/abs/2508.01802
   - 논문에서 데이터셋 정보 확인

**데이터 구조**:
- 전 경기 파노라마 비디오 (.mp4)
- 프레임별 2D 피치 좌표/역할/팀 라벨
- Bounding boxes (training set only, MOT format)
- 10개 경기, 고정 시점 비디오

**인용**:
```bibtex
@article{scott2025soccertrackv2,
  title={SoccerTrack v2: A Full-Pitch Multi-View Soccer Dataset for Game State Reconstruction}, 
  author={Atom Scott and Ikuma Uchida and Kento Kuroda and Yufi Kim and Keisuke Fujii},
  journal = {2508.01802},
  year    = {2025}
}
```

**저장 위치 권장**: `00_data/SoccerTrack/`

---

### 🔵 7순위: SoccerNet Tracking

**용도**: 방송 카메라 기반 트래킹 벤치마크  
**라이선스**: 연구용 (GitHub 확인)  
**데이터 용량**: 약 5GB ~ 10GB (12경기, 트래킹 데이터, 다운로드 시 확인 필요)

**다운로드 방법**:
```bash
cd ~/Downloads
git clone https://github.com/SoccerNet/sn-tracking.git
cd sn-tracking

# README 확인하여 데이터 다운로드 방법 확인
cat README.md
```

**URL**: https://github.com/SoccerNet/sn-tracking

**특징**: 12경기, 여러 클립 단위 트래킹 데이터

**저장 위치 권장**: `00_data/SoccerNet/`

---

### 🔴 특별: AIHub 71482 (축구 전술 데이터)

**용도**: 전술 라벨, 오프사이드 판정, 영상 데이터  
**라이선스**: AIHub 이용약관 확인 필요  
**데이터 용량**: 약 100GB ~ 200GB (330경기, MP4 영상 + JPG 이미지 + JSON 라벨, 매우 큰 용량, 다운로드 시 확인 필요)

**다운로드 방법**:
1. AIHub 로그인 필요:
   - URL: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71482
   - 회원가입/로그인 후 다운로드

2. 데이터 구성:
   - MP4 (영상) + JPG (이미지) + JSON (라벨)
   - 330경기, 5FPS, 87,838장 이미지

3. 다운로드 후 확인:
   - 샘플 JSON 1개 파싱하여 스키마 확정
   - 전술 라벨이 "클립 단위"인지 확인
   - 추적/좌표가 "프레임 단위"로 있는지 확인

**저장 위치 권장**: `00_data/AIHub_71482/`

---

## 빠른 다운로드 스크립트

```bash
#!/bin/bash
# 데이터셋 다운로드 스크립트

BASE_DIR="$HOME/Downloads/football_datasets"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

echo "=== StatsBomb Open Data ==="
if [ ! -d "open-data" ]; then
    git clone https://github.com/statsbomb/open-data.git
else
    echo "이미 다운로드됨"
fi

echo "=== SkillCorner OpenData ==="
if [ ! -d "opendata" ]; then
    git clone https://github.com/SkillCorner/opendata.git
else
    echo "이미 다운로드됨"
fi

echo "=== Metrica Sports Sample Data ==="
if [ ! -d "sample-data" ]; then
    git clone https://github.com/metrica-sports/sample-data.git
else
    echo "이미 다운로드됨"
fi

echo "=== SoccerNet Tracking ==="
if [ ! -d "sn-tracking" ]; then
    git clone https://github.com/SoccerNet/sn-tracking.git
else
    echo "이미 다운로드됨"
fi

echo ""
echo "다운로드 완료!"
echo "다음 데이터셋은 브라우저에서 수동 다운로드 필요:"
echo "  - Wyscout: https://figshare.com/collections/Soccer_match_event_dataset/4265000"
echo "  - Bundesliga: https://www.nature.com/articles/s41597-025-04505-y"
echo "  - SoccerTrack v2: https://arxiv.org/pdf/2508.01802"
echo "  - AIHub 71482: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71482 (로그인 필요)"
```

---

## 프로젝트에 통합할 디렉토리 구조

```
00_data/
├── Track2/              # 기존 데이터 (유지)
│   ├── raw_data.csv
│   └── match_info.csv
├── StatsBomb/           # 새로 추가
│   └── open-data/
├── SkillCorner/         # 새로 추가
│   └── opendata/
├── Metrica/             # 새로 추가
│   └── sample-data/
├── Wyscout/             # 새로 추가 (수동 다운로드)
├── Bundesliga/          # 새로 추가 (수동 다운로드)
├── SoccerTrack/         # 새로 추가 (수동 다운로드)
├── SoccerNet/           # 새로 추가
│   └── sn-tracking/
└── AIHub_71482/         # 새로 추가 (로그인 필요)
```

---

## 우선순위별 다운로드 순서

### 오늘 밤 다운로드 (자동 가능):
1. ✅ **StatsBomb Open Data** (GitHub 클론)
2. ✅ **SkillCorner OpenData** (GitHub 클론)
3. ✅ **Metrica Sports Sample Data** (GitHub 클론)
4. ✅ **SoccerNet Tracking** (GitHub 클론)

### 내일 아침 다운로드 (수동 필요):
5. **Wyscout** (Figshare에서 다운로드)
6. **Bundesliga** (Nature 논문에서 링크 확인)
7. **SoccerTrack v2** (arXiv 논문에서 링크 확인)
8. **AIHub 71482** (로그인 후 다운로드)

---

## 데이터 용량 요약

| 데이터셋 | 용량 | 비고 |
|---------|------|------|
| StatsBomb Open Data | 약 500MB ~ 1GB | JSON 이벤트 데이터 |
| SkillCorner OpenData | 약 500MB ~ 1GB | 추적 좌표 데이터 포함 |
| Metrica Sports Sample Data | 약 50MB ~ 100MB | 샘플 데이터, 경기 수 적음 |
| Wyscout | 약 500MB ~ 1GB | 이벤트 데이터, 다운로드 시 확인 필요 |
| Bundesliga (7경기) | 약 2GB ~ 5GB | 이벤트+추적+메타 통합 |
| SoccerTrack v2 | 약 50GB ~ 100GB | 파노라마 비디오 포함, 큰 용량 |
| SoccerNet Tracking | 약 5GB ~ 10GB | 12경기, 트래킹 데이터 |
| AIHub 71482 | 약 100GB ~ 200GB | 330경기, 영상+이미지+JSON, 매우 큰 용량 |

**예상 총 용량**: 약 159GB ~ 319GB (모든 데이터셋 다운로드 시)  
**1순위~3순위 합계**: 약 1GB ~ 2.1GB (우선 다운로드 권장)

---

## 참고 링크 정리

- **StatsBomb**: https://github.com/statsbomb/open-data
- **SkillCorner**: https://github.com/SkillCorner/opendata
- **Metrica**: https://github.com/metrica-sports/sample-data
- **SoccerNet**: https://github.com/SoccerNet/sn-tracking
- **Wyscout**: https://figshare.com/collections/Soccer_match_event_dataset/4265000
- **Bundesliga**: https://www.nature.com/articles/s41597-025-04505-y
- **SoccerTrack v2**: https://arxiv.org/pdf/2508.01802
- **AIHub 71482**: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71482

---

## 다음 단계

1. **오늘 밤**: GitHub 데이터셋 4개 자동 다운로드
2. **내일 아침**: 수동 다운로드 4개 진행
3. **데이터 검증**: 각 데이터셋의 스키마 확인 및 Track2와의 매핑 테이블 작성
4. **통합 계획**: GPT 답변 기반 통합 로드맵에 따라 단계별 통합

