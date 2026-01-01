#!/bin/bash
# 축구 데이터셋 자동 다운로드 스크립트
# GitHub에서 클론 가능한 데이터셋들을 자동으로 다운로드합니다.

set -euo pipefail

BASE_DIR="${HOME}/Downloads/football_datasets"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_DATA_DIR="${SCRIPT_DIR}/00_data"

echo "=== 축구 데이터셋 다운로드 스크립트 ==="
echo ""

# 다운로드 디렉토리 생성
mkdir -p "${BASE_DIR}"
cd "${BASE_DIR}"

# 1. StatsBomb Open Data
echo "[1/4] StatsBomb Open Data 다운로드 중..."
if [ ! -d "open-data" ]; then
    git clone https://github.com/statsbomb/open-data.git
    echo "  ✅ 다운로드 완료"
else
    echo "  ⏭️  이미 다운로드됨 (업데이트하려면: cd open-data && git pull)"
fi

# 2. SkillCorner OpenData
echo "[2/4] SkillCorner OpenData 다운로드 중..."
if [ ! -d "opendata" ]; then
    git clone https://github.com/SkillCorner/opendata.git
    echo "  ✅ 다운로드 완료"
else
    echo "  ⏭️  이미 다운로드됨 (업데이트하려면: cd opendata && git pull)"
fi

# 3. Metrica Sports Sample Data
echo "[3/4] Metrica Sports Sample Data 다운로드 중..."
if [ ! -d "sample-data" ]; then
    git clone https://github.com/metrica-sports/sample-data.git
    echo "  ✅ 다운로드 완료"
else
    echo "  ⏭️  이미 다운로드됨 (업데이트하려면: cd sample-data && git pull)"
fi

# 4. SoccerNet Tracking
echo "[4/4] SoccerNet Tracking 다운로드 중..."
if [ ! -d "sn-tracking" ]; then
    git clone https://github.com/SoccerNet/sn-tracking.git
    echo "  ✅ 다운로드 완료"
else
    echo "  ⏭️  이미 다운로드됨 (업데이트하려면: cd sn-tracking && git pull)"
fi

echo ""
echo "=== 자동 다운로드 완료 ==="
echo ""
echo "다운로드 위치: ${BASE_DIR}"
echo ""
echo "다음 데이터셋은 브라우저에서 수동 다운로드 필요:"
echo ""
echo "5. Wyscout Soccer Match Event Dataset"
echo "   URL: https://figshare.com/collections/Soccer_match_event_dataset/4265000"
echo "   저장 위치: ${PROJECT_DATA_DIR}/Wyscout/"
echo ""
echo "6. Bundesliga 통합 데이터 (7경기)"
echo "   URL: https://www.nature.com/articles/s41597-025-04505-y"
echo "   저장 위치: ${PROJECT_DATA_DIR}/Bundesliga/"
echo ""
echo "7. SoccerTrack v2"
echo "   URL: https://arxiv.org/pdf/2508.01802"
echo "   저장 위치: ${PROJECT_DATA_DIR}/SoccerTrack/"
echo ""
echo "8. AIHub 71482 (축구 전술 데이터)"
echo "   URL: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71482"
echo "   저장 위치: ${PROJECT_DATA_DIR}/AIHub_71482/"
echo "   ⚠️  로그인 필요"
echo ""
echo "프로젝트에 통합하려면:"
echo "  mkdir -p ${PROJECT_DATA_DIR}/{StatsBomb,SkillCorner,Metrica,Wyscout,Bundesliga,SoccerTrack,SoccerNet,AIHub_71482}"
echo "  # 필요시 심볼릭 링크 생성 또는 데이터 복사"

