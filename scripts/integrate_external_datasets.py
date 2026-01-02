#!/usr/bin/env python3
"""
외부 데이터셋 통합 스크립트

다운로드된 데이터셋들을 프로젝트 디렉토리 구조에 통합하고 심볼릭 링크를 생성합니다.
"""

import argparse
import os
from pathlib import Path


def create_symlinks(download_dir: Path, project_data_dir: Path):
    """다운로드된 데이터셋을 프로젝트 디렉토리에 심볼릭 링크로 연결"""
    mappings = {
        "open-data": "StatsBomb",
        "opendata": "SkillCorner",
        "sample-data": "Metrica",
        "sn-tracking": "SoccerNet",
    }
    
    print("=== 외부 데이터셋 통합 ===\n")
    
    for source_name, target_name in mappings.items():
        source_path = download_dir / source_name
        target_path = project_data_dir / target_name
        
        if not source_path.exists():
            print(f"[{target_name}] 소스 디렉토리 없음: {source_path}")
            continue
        
        # 타겟 디렉토리 생성
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 심볼릭 링크 생성
        link_path = target_path / source_name
        if link_path.exists():
            if link_path.is_symlink():
                print(f"[{target_name}] 이미 링크됨: {link_path}")
            else:
                print(f"[{target_name}] 경로가 이미 존재함 (심볼릭 링크 아님): {link_path}")
        else:
            try:
                link_path.symlink_to(source_path)
                print(f"[{target_name}] ✅ 심볼릭 링크 생성: {link_path} -> {source_path}")
            except Exception as e:
                print(f"[{target_name}] ❌ 링크 생성 실패: {e}")
                # 대안: 디렉토리 정보 파일 생성
                info_file = target_path / "SOURCE_LOCATION.txt"
                with open(info_file, "w") as f:
                    f.write(f"Source location: {source_path}\n")
                    f.write(f"To create symlink manually:\n")
                    f.write(f"  ln -s {source_path} {link_path}\n")
                print(f"[{target_name}] 소스 위치 정보 저장: {info_file}")


def main():
    parser = argparse.ArgumentParser(description="외부 데이터셋 통합")
    parser.add_argument(
        "--download-dir",
        type=str,
        default=os.path.expanduser("~/Downloads/football_datasets"),
        help="다운로드된 데이터셋 디렉토리",
    )
    parser.add_argument(
        "--project-data-dir",
        type=str,
        default=None,
        help="프로젝트 데이터 디렉토리 (기본값: 프로젝트 루트/00_data)",
    )
    args = parser.parse_args()
    
    download_dir = Path(args.download_dir)
    if args.project_data_dir:
        project_data_dir = Path(args.project_data_dir)
    else:
        # 프로젝트 루트 찾기
        script_dir = Path(__file__).resolve().parent
        project_data_dir = script_dir.parent / "00_data"
    
    if not download_dir.exists():
        print(f"다운로드 디렉토리가 없습니다: {download_dir}")
        print(f"먼저 ./scripts/download_datasets.sh를 실행하세요.")
        return
    
    create_symlinks(download_dir, project_data_dir)
    
    print("\n=== 통합 완료 ===")
    print(f"프로젝트 데이터 디렉토리: {project_data_dir}")
    print("\n다음 단계:")
    print("  1. python scripts/validate_external_datasets.py")
    print("  2. 각 데이터셋의 스키마 확인 및 Track2 매핑 테이블 작성")


if __name__ == "__main__":
    main()

