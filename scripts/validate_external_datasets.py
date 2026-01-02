#!/usr/bin/env python3
"""
외부 데이터셋 검증 스크립트

다운로드된 데이터셋들의 스키마를 확인하고 Track2와의 매핑 가능성을 분석합니다.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


def validate_statsbomb(data_dir: Path) -> Dict:
    """StatsBomb 데이터 검증"""
    result = {
        "dataset": "StatsBomb Open Data",
        "status": "not_found",
        "structure": {},
        "sample_schema": {},
        "track2_mapping": {},
    }
    
    events_dir = data_dir / "data" / "events"
    if not events_dir.exists():
        return result
    
    # 샘플 파일 찾기
    sample_files = list(events_dir.glob("*.json"))
    if not sample_files:
        return result
    
    result["status"] = "found"
    result["structure"]["events_dir"] = str(events_dir)
    result["structure"]["sample_files_count"] = len(sample_files)
    
    # 샘플 파일 하나 읽기
    try:
        with open(sample_files[0], "r") as f:
            sample_data = json.load(f)
        
        if isinstance(sample_data, list) and len(sample_data) > 0:
            first_event = sample_data[0]
            result["sample_schema"] = {
                "keys": list(first_event.keys()),
                "has_under_pressure": "under_pressure" in first_event,
                "has_counterpress": "counterpress" in first_event,
                "has_offside": any("offside" in str(k).lower() for k in first_event.keys()),
                "event_type": first_event.get("type", {}).get("name", "unknown"),
            }
            
            # Track2 매핑 가능성
            result["track2_mapping"] = {
                "time_mapping": "timestamp" in first_event or "minute" in first_event,
                "coordinates_mapping": "location" in first_event,
                "event_type_mapping": "type" in first_event,
                "team_mapping": "team" in first_event,
            }
    except Exception as e:
        result["error"] = str(e)
    
    return result


def validate_skillcorner(data_dir: Path) -> Dict:
    """SkillCorner 데이터 검증"""
    result = {
        "dataset": "SkillCorner OpenData",
        "status": "not_found",
        "structure": {},
        "sample_schema": {},
        "track2_mapping": {},
    }
    
    if not data_dir.exists():
        return result
    
    # README 확인
    readme_path = data_dir / "README.md"
    if readme_path.exists():
        result["structure"]["has_readme"] = True
    
    # 데이터 파일 찾기
    data_files = list(data_dir.rglob("*.json")) + list(data_dir.rglob("*.csv"))
    if data_files:
        result["status"] = "found"
        result["structure"]["data_files_count"] = len(data_files)
        result["structure"]["sample_file"] = str(data_files[0])
        
        # 샘플 파일 읽기
        try:
            if data_files[0].suffix == ".json":
                with open(data_files[0], "r") as f:
                    sample_data = json.load(f)
                    if isinstance(sample_data, dict):
                        result["sample_schema"]["keys"] = list(sample_data.keys())
            elif data_files[0].suffix == ".csv":
                df = pd.read_csv(data_files[0], nrows=5)
                result["sample_schema"]["columns"] = df.columns.tolist()
                result["sample_schema"]["shape"] = df.shape
        except Exception as e:
            result["error"] = str(e)
    
    return result


def validate_metrica(data_dir: Path) -> Dict:
    """Metrica 데이터 검증"""
    result = {
        "dataset": "Metrica Sports Sample Data",
        "status": "not_found",
        "structure": {},
        "sample_schema": {},
        "track2_mapping": {},
    }
    
    if not data_dir.exists():
        return result
    
    # 데이터 파일 찾기
    data_files = list(data_dir.rglob("*.csv")) + list(data_dir.rglob("*.json"))
    if data_files:
        result["status"] = "found"
        result["structure"]["data_files_count"] = len(data_files)
        result["structure"]["sample_file"] = str(data_files[0])
        
        # 샘플 파일 읽기
        try:
            if data_files[0].suffix == ".csv":
                df = pd.read_csv(data_files[0], nrows=5)
                result["sample_schema"]["columns"] = df.columns.tolist()
                result["sample_schema"]["has_tracking"] = any("x" in col.lower() or "y" in col.lower() for col in df.columns)
                result["sample_schema"]["has_events"] = any("event" in col.lower() for col in df.columns)
        except Exception as e:
            result["error"] = str(e)
    
    return result


def validate_soccernet(data_dir: Path) -> Dict:
    """SoccerNet 데이터 검증"""
    result = {
        "dataset": "SoccerNet Tracking",
        "status": "not_found",
        "structure": {},
        "sample_schema": {},
        "track2_mapping": {},
    }
    
    if not data_dir.exists():
        return result
    
    # README 확인
    readme_path = data_dir / "README.md"
    if readme_path.exists():
        result["structure"]["has_readme"] = True
    
    # 데이터 파일 찾기
    data_files = list(data_dir.rglob("*.json")) + list(data_dir.rglob("*.csv"))
    if data_files:
        result["status"] = "found"
        result["structure"]["data_files_count"] = len(data_files)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="외부 데이터셋 검증")
    parser.add_argument(
        "--download-dir",
        type=str,
        default=os.path.expanduser("~/Downloads/football_datasets"),
        help="다운로드된 데이터셋 디렉토리",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/external_datasets_validation.json",
        help="검증 결과 출력 파일",
    )
    args = parser.parse_args()
    
    download_dir = Path(args.download_dir)
    results = {}
    
    print("=== 외부 데이터셋 검증 ===\n")
    
    # 1. StatsBomb
    print("[1/4] StatsBomb Open Data 검증 중...")
    statsbomb_dir = download_dir / "open-data"
    results["statsbomb"] = validate_statsbomb(statsbomb_dir)
    print(f"  상태: {results['statsbomb']['status']}")
    if results["statsbomb"]["status"] == "found":
        print(f"  샘플 파일 수: {results['statsbomb']['structure'].get('sample_files_count', 0)}")
        if "sample_schema" in results["statsbomb"] and results["statsbomb"]["sample_schema"]:
            print(f"  압박 이벤트: {results['statsbomb']['sample_schema'].get('has_under_pressure', False)}")
    
    # 2. SkillCorner
    print("\n[2/4] SkillCorner OpenData 검증 중...")
    skillcorner_dir = download_dir / "opendata"
    results["skillcorner"] = validate_skillcorner(skillcorner_dir)
    print(f"  상태: {results['skillcorner']['status']}")
    if results["skillcorner"]["status"] == "found":
        print(f"  데이터 파일 수: {results['skillcorner']['structure'].get('data_files_count', 0)}")
    
    # 3. Metrica
    print("\n[3/4] Metrica Sports Sample Data 검증 중...")
    metrica_dir = download_dir / "sample-data"
    results["metrica"] = validate_metrica(metrica_dir)
    print(f"  상태: {results['metrica']['status']}")
    if results["metrica"]["status"] == "found":
        print(f"  데이터 파일 수: {results['metrica']['structure'].get('data_files_count', 0)}")
        if "sample_schema" in results["metrica"] and results["metrica"]["sample_schema"]:
            print(f"  추적 데이터: {results['metrica']['sample_schema'].get('has_tracking', False)}")
    
    # 4. SoccerNet
    print("\n[4/4] SoccerNet Tracking 검증 중...")
    soccernet_dir = download_dir / "sn-tracking"
    results["soccernet"] = validate_soccernet(soccernet_dir)
    print(f"  상태: {results['soccernet']['status']}")
    if results["soccernet"]["status"] == "found":
        print(f"  데이터 파일 수: {results['soccernet']['structure'].get('data_files_count', 0)}")
    
    # 결과 저장
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n검증 결과 저장: {output_path}")
    
    # 요약
    print("\n=== 검증 요약 ===")
    found_count = sum(1 for r in results.values() if r.get("status") == "found")
    print(f"발견된 데이터셋: {found_count}/4")
    for name, result in results.items():
        status_icon = "✅" if result.get("status") == "found" else "❌"
        print(f"  {status_icon} {result['dataset']}: {result.get('status', 'unknown')}")


if __name__ == "__main__":
    main()

