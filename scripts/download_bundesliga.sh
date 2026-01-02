#!/bin/bash
# Bundesliga 통합 데이터 다운로드 스크립트

set -euo pipefail

BASE_DIR="${HOME}/Downloads/football_datasets"
PROJECT_DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/00_data"

echo "=== Bundesliga 통합 데이터 다운로드 ==="
echo ""

# 디렉토리 생성
mkdir -p "${BASE_DIR}/Bundesliga"
mkdir -p "${PROJECT_DATA_DIR}/Bundesliga"

echo "📋 다운로드 정보:"
echo "  - 용량: 2.45 GB"
echo "  - URL: https://springernature.figshare.com/articles/dataset/An_integrated_dataset_of_spatiotemporal_and_event_data_in_elite_soccer/28196177"
echo "  - DOI: 10.6084/m9.figshare.28196177"
echo ""

echo "다운로드 방법:"
echo "1. 브라우저에서 다음 URL 접속:"
echo "   https://springernature.figshare.com/articles/dataset/An_integrated_dataset_of_spatiotemporal_and_event_data_in_elite_soccer/28196177"
echo ""
echo "2. 'Download all (2.45 GB)' 버튼 클릭"
echo ""
echo "3. 다운로드한 파일을 다음 위치에 저장:"
echo "   ${BASE_DIR}/Bundesliga/"
echo ""
echo "4. 압축 해제 후 프로젝트에 통합:"
echo "   # 심볼릭 링크 생성 (권장)"
echo "   ln -s ${BASE_DIR}/Bundesliga/* ${PROJECT_DATA_DIR}/Bundesliga/"
echo ""

echo "또는 wget/curl로 직접 다운로드 (링크 확인 필요):"
echo "  # Figshare에서 직접 다운로드 링크 확인 후"
echo "  wget -O ${BASE_DIR}/Bundesliga/bundesliga_data.zip <다운로드_URL>"
echo ""

