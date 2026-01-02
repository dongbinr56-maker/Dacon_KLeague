#!/bin/bash
# SoccerTrack v2 다운로드 스크립트

set -euo pipefail

BASE_DIR="${HOME}/Downloads/football_datasets"
PROJECT_DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/00_data"

echo "=== SoccerTrack v2 다운로드 ==="
echo ""

# 디렉토리 생성
mkdir -p "${BASE_DIR}/SoccerTrack"
mkdir -p "${PROJECT_DATA_DIR}/SoccerTrack"

echo "📋 다운로드 정보:"
echo "  - 용량: 약 50-100GB (파노라마 비디오 포함)"
echo "  - 논문: https://arxiv.org/abs/2508.01802"
echo "  - 공식 웹사이트: https://sites.google.com/g.sp.m.is.nagoya-u.ac.jp/stc2025"
echo ""

echo "다운로드 방법:"
echo "1. SoccerTrack Challenge 2025 공식 웹사이트 접속:"
echo "   https://sites.google.com/g.sp.m.is.nagoya-u.ac.jp/stc2025"
echo ""
echo "2. 웹사이트에서 'Dataset' 또는 'Download' 섹션 확인"
echo ""
echo "3. 다운로드 링크 클릭하여 데이터 다운로드"
echo ""
echo "4. 다운로드한 파일을 다음 위치에 저장:"
echo "   ${BASE_DIR}/SoccerTrack/"
echo ""
echo "5. 압축 해제 후 프로젝트에 통합:"
echo "   # 심볼릭 링크 생성 (권장)"
echo "   ln -s ${BASE_DIR}/SoccerTrack/* ${PROJECT_DATA_DIR}/SoccerTrack/"
echo ""

echo "⚠️  참고:"
echo "  - 매우 큰 용량(50-100GB)이므로 충분한 디스크 공간 필요"
echo "  - 다운로드 시간이 오래 걸릴 수 있습니다"
echo "  - 공식 웹사이트에서 정확한 다운로드 링크 확인 필요"
echo ""

