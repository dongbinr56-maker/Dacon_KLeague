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
echo "  - 경기 수: 10개 (고정 시점 비디오)"
echo "  - 데이터 형식: .mp4 비디오, MOT format bounding boxes"
echo ""

echo "다운로드 방법 (우선순위 순):"
echo ""
echo "1. GitHub 저장소 (권장):"
echo "   https://github.com/open-starlab/stc-2025"
echo "   - README 파일에서 데이터셋 다운로드 링크 확인"
echo "   - 샘플 코드 및 사용법 제공"
echo ""
echo "2. 공식 웹사이트:"
echo "   https://sites.google.com/g.sp.m.is.nagoya-u.ac.jp/stc2025"
echo "   - 'The Dataset for this challenge are SoccerTrack v2 datasets (you can download from here)'"
echo "   - 웹사이트에서 직접 다운로드 링크 제공"
echo ""
echo "3. CodaLab 페이지:"
echo "   https://codalab.lisn.upsaclay.fr/competitions/22532"
echo "   - 경쟁 참가자용 데이터셋 다운로드"
echo ""
echo "4. 논문:"
echo "   https://arxiv.org/abs/2508.01802"
echo "   - 데이터셋 상세 정보 확인"
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

