#!/bin/bash
# Bundesliga 및 SoccerTrack v2 다운로드 스크립트
# 수동 다운로드가 필요한 데이터셋들의 가이드

set -euo pipefail

BASE_DIR="${HOME}/Downloads/football_datasets"
PROJECT_DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/00_data"

echo "=== Bundesliga 및 SoccerTrack v2 다운로드 가이드 ==="
echo ""

# 디렉토리 생성
mkdir -p "${BASE_DIR}/Bundesliga"
mkdir -p "${BASE_DIR}/SoccerTrack"
mkdir -p "${PROJECT_DATA_DIR}/Bundesliga"
mkdir -p "${PROJECT_DATA_DIR}/SoccerTrack"

echo "📋 다운로드 디렉토리 생성 완료:"
echo "   - ${BASE_DIR}/Bundesliga"
echo "   - ${BASE_DIR}/SoccerTrack"
echo ""

echo "=== 5순위: Bundesliga 통합 데이터 (7경기) ==="
echo ""
echo "다운로드 방법:"
echo "1. Nature 논문 접속: https://www.nature.com/articles/s41597-025-04505-y"
echo "2. 논문의 'Data availability' 섹션에서 다운로드 링크 확인"
echo "3. 데이터 다운로드 (약 2GB ~ 5GB)"
echo "4. 다운로드한 파일을 다음 위치에 저장:"
echo "   ${BASE_DIR}/Bundesliga/"
echo ""
echo "데이터 구조:"
echo "  - 이벤트 데이터"
echo "  - 추적 좌표 데이터"
echo "  - 메타데이터"
echo ""

echo "=== 6순위: SoccerTrack v2 ==="
echo ""
echo "다운로드 방법:"
echo "1. arXiv 논문 접속: https://arxiv.org/pdf/2508.01802"
echo "2. 논문의 'Dataset' 또는 'Download' 섹션에서 링크 확인"
echo "3. 데이터 다운로드 (약 50GB ~ 100GB, 파노라마 비디오 포함)"
echo "4. 다운로드한 파일을 다음 위치에 저장:"
echo "   ${BASE_DIR}/SoccerTrack/"
echo ""
echo "데이터 구조:"
echo "  - 파노라마 비디오"
echo "  - 2D 좌표 데이터"
echo "  - 이벤트 데이터"
echo ""

echo "=== 통합 방법 ==="
echo ""
echo "다운로드 완료 후 프로젝트에 통합:"
echo "  # 심볼릭 링크 생성 (권장)"
echo "  ln -s ${BASE_DIR}/Bundesliga/* ${PROJECT_DATA_DIR}/Bundesliga/"
echo "  ln -s ${BASE_DIR}/SoccerTrack/* ${PROJECT_DATA_DIR}/SoccerTrack/"
echo ""
echo "또는 데이터 복사:"
echo "  cp -r ${BASE_DIR}/Bundesliga/* ${PROJECT_DATA_DIR}/Bundesliga/"
echo "  cp -r ${BASE_DIR}/SoccerTrack/* ${PROJECT_DATA_DIR}/SoccerTrack/"
echo ""

echo "⚠️  참고:"
echo "  - 두 데이터셋 모두 큰 용량이므로 다운로드 시간이 오래 걸릴 수 있습니다"
echo "  - SoccerTrack v2는 특히 용량이 크므로(50-100GB) 충분한 디스크 공간 필요"
echo "  - 다운로드 링크는 논문에서 확인해야 합니다"
echo ""

