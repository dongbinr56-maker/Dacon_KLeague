# External data & licensing

현재 데모는 제공된 Track2 이벤트 로그만을 사용하며 **외부 데이터/모델을 추가로 사용하지 않았습니다.**

외부 데이터를 추가할 경우 반드시 다음을 기록합니다.
- 출처와 라이선스(재배포/재현 가능 여부)
- 무료/공개 여부
- 수집/캐시 스크립트와 실행 방법
- 저장 위치(상대 경로)

---

## 무료 축구 경기 데이터셋 목록

### 1. StatsBomb Open Data
- **출처**: StatsBomb (https://github.com/statsbomb/open-data)
- **라이선스**: CC BY 4.0 (상업적 사용 가능, 출처 표기 필요)
- **내용**: 
  - 이벤트 데이터 (패스, 슛, 드리블 등)
  - 경기 메타데이터
  - 선수 및 팀 정보
  - FIFA 월드컵, 유럽 주요 리그 포함
- **형식**: JSON
- **용도**: 전술 분석, 이벤트 기반 분석
- **통합 방법**: JSON → CSV 변환 스크립트 필요

### 2. Wyscout Open Dataset
- **출처**: Wyscout (https://figshare.com/collections/Soccer_match_event_dataset/4265000)
- **라이선스**: 연구/교육용 무료
- **내용**:
  - 이벤트 데이터 (위치, 시간, 타입)
  - 경기 통계
  - 유럽 주요 리그 데이터
- **형식**: JSON
- **용도**: 이벤트 로그 분석, 패턴 탐지

### 3. Kaggle Datasets
- **출처**: Kaggle 커뮤니티
- **라이선스**: 데이터셋별 상이 (각 데이터셋 확인 필요)
- **인기 데이터셋**:
  - European Soccer Database
  - FIFA World Cup 데이터
  - Premier League 데이터
- **URL**: https://www.kaggle.com/datasets?search=football+soccer
- **형식**: CSV, SQLite 등 다양
- **용도**: 통계 분석, 머신러닝

### 4. Football-Data.co.uk
- **출처**: Football-Data.co.uk
- **라이선스**: 무료 (비상업적 용도)
- **내용**:
  - 경기 결과
  - 배당률 데이터
  - 기본 통계
- **URL**: https://www.football-data.co.uk/
- **형식**: CSV
- **용도**: 경기 결과 분석, 통계

### 5. API Football (Free Tier)
- **출처**: API-Football (RapidAPI)
- **라이선스**: 무료 티어 (월 100회 요청)
- **내용**:
  - 실시간 경기 데이터
  - 선수 통계
  - 팀 정보
  - 다양한 리그 지원
- **URL**: https://www.api-football.com/
- **형식**: REST API (JSON)
- **용도**: 실시간 데이터 수집, API 통합

### 6. OpenLigaDB (독일 리그)
- **출처**: OpenLigaDB
- **라이선스**: 무료, 오픈소스
- **내용**: 독일 분데스리가, 2. 분데스리가 데이터
- **URL**: https://www.openligadb.de/
- **형식**: REST API, JSON
- **용도**: 독일 리그 분석

### 7. 공공데이터포털 (한국)
- **출처**: 공공데이터포털 (data.go.kr)
- **라이선스**: 공공데이터 (출처 표기 필요)
- **내용**: K리그 관련 공공 데이터 (있는 경우)
- **URL**: https://www.data.go.kr/
- **검색어**: "축구", "K리그", "스포츠"
- **용도**: 한국 리그 데이터

---

## 데이터 통합 가이드

### StatsBomb 데이터 사용 예시

1. **데이터 다운로드**:
```bash
# StatsBomb Open Data 클론
git clone https://github.com/statsbomb/open-data.git
cd open-data/data/events
```

2. **JSON → CSV 변환 스크립트** (예시):
```python
# scripts/convert_statsbomb.py
import json
import csv
from pathlib import Path

def convert_statsbomb_to_track2_format(input_json, output_csv):
    # StatsBomb JSON을 Track2 CSV 형식으로 변환
    # game_id, time_seconds, type_name, start_x, start_y, end_x, end_y 등
    pass
```

3. **데이터 경로 설정**:
```bash
# .env 파일에 추가
EVENTS_DATA_PATH=./00_data/StatsBomb/events.csv
MATCH_INFO_PATH=./00_data/StatsBomb/matches.csv
```

### API Football 통합 예시

1. **API 키 발급**: RapidAPI에서 무료 계정 생성
2. **데이터 수집 스크립트**:
```python
# scripts/fetch_api_football.py
import requests
import json

API_KEY = "your_api_key"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def fetch_match_events(match_id):
    # API 호출하여 이벤트 데이터 수집
    pass
```

---

## 라이선스 주의사항

1. **출처 표기**: 모든 외부 데이터 사용 시 출처 명시 필수
2. **상업적 사용**: 라이선스 확인 후 사용
3. **재배포**: 일부 데이터셋은 재배포 불가 (원본 링크 제공)
4. **API 제한**: 무료 티어의 요청 제한 확인

---

## 추천 데이터셋 (프로젝트 용도)

**가장 추천**: **StatsBomb Open Data**
- ✅ 완전 무료
- ✅ 상업적 사용 가능 (CC BY 4.0)
- ✅ 풍부한 이벤트 데이터
- ✅ Track2와 유사한 형식
- ✅ 전술 분석에 적합

**대안**: **Wyscout Open Dataset**
- ✅ 연구/교육용 무료
- ✅ 유럽 리그 데이터
- ✅ 이벤트 로그 형식

---

## 데이터 수집 스크립트 템플릿

새로운 데이터 소스를 추가할 때는 다음 형식으로 스크립트를 작성하세요:

```python
# scripts/collect_[source_name].py
"""
[데이터 소스명] 데이터 수집 스크립트

출처: [URL]
라이선스: [라이선스 정보]
용도: [사용 목적]
"""

def collect_data():
    """데이터 수집 및 변환"""
    pass

def convert_to_track2_format():
    """Track2 형식으로 변환"""
    pass

if __name__ == "__main__":
    collect_data()
    convert_to_track2_format()
```
