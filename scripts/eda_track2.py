#!/usr/bin/env python3
"""
Track2 데이터 EDA 스크립트

입력: 00_data/Track2/raw_data.csv (경로는 인자로 override 가능)
출력: artifacts/eda_track2_report.md, artifacts/eda_track2_summary.json
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def load_track2_data(csv_path: str) -> pd.DataFrame:
    """Track2 CSV 파일 로드"""
    print(f"Loading Track2 data from: {csv_path}")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Track2 data file not found: {csv_path}")
    
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def analyze_type_name(df: pd.DataFrame) -> dict:
    """type_name 고유값 및 빈도 분석"""
    type_counts = df["type_name"].value_counts()
    top_30_dict = type_counts.head(30).to_dict()
    # numpy 타입을 Python 기본 타입으로 변환
    top_30_dict = {k: int(v) for k, v in top_30_dict.items()}
    return {
        "unique_count": int(df["type_name"].nunique()),
        "top_30": top_30_dict,
        "total_events": int(len(df)),
    }


def analyze_result_name(df: pd.DataFrame) -> dict:
    """result_name 분포 및 type_name별 교차표"""
    result_dist = df["result_name"].value_counts()
    result_dict = {k: int(v) for k, v in result_dist.to_dict().items()}
    
    # type_name별 result_name 교차표 (Top 10 type_name만)
    top_types = df["type_name"].value_counts().head(10).index
    cross_tab = {}
    for t in top_types:
        subset = df[df["type_name"] == t]
        cross_dict = subset["result_name"].value_counts().to_dict()
        cross_tab[t] = {k: int(v) for k, v in cross_dict.items()}
    
    return {
        "distribution": result_dict,
        "empty_string_count": int((df["result_name"] == "").sum()),
        "null_count": int(df["result_name"].isna().sum()),
        "top_10_type_cross_tab": cross_tab,
    }


def analyze_coordinates(df: pd.DataFrame) -> dict:
    """좌표 분석 (min/max/quantile/결측률)"""
    coord_cols = ["start_x", "start_y", "end_x", "end_y"]
    result = {}
    
    for col in coord_cols:
        if col not in df.columns:
            result[col] = {"error": "column not found"}
            continue
        
        series = pd.to_numeric(df[col], errors="coerce")
        result[col] = {
            "min": float(series.min()) if not series.isna().all() else None,
            "max": float(series.max()) if not series.isna().all() else None,
            "mean": float(series.mean()) if not series.isna().all() else None,
            "quantiles": {
                "1%": float(series.quantile(0.01)) if not series.isna().all() else None,
                "5%": float(series.quantile(0.05)) if not series.isna().all() else None,
                "50%": float(series.quantile(0.50)) if not series.isna().all() else None,
                "95%": float(series.quantile(0.95)) if not series.isna().all() else None,
                "99%": float(series.quantile(0.99)) if not series.isna().all() else None,
            },
            "missing_rate": float(series.isna().sum() / len(df)),
            "zero_count": int((series == 0).sum()),
        }
    
    return result


def analyze_team_id(df: pd.DataFrame) -> dict:
    """team_id 결측률 및 game_id별 팀 개수"""
    missing_rate = df["team_id"].isna().sum() / len(df) if "team_id" in df.columns else 1.0
    
    # game_id별 team_id 고유 개수
    if "team_id" in df.columns and "game_id" in df.columns:
        game_teams = df.groupby("game_id")["team_id"].nunique()
        team_dist_dict = game_teams.value_counts().to_dict()
        team_dist_dict = {int(k): int(v) for k, v in team_dist_dict.items()}
        result = {
            "missing_rate": float(missing_rate),
            "games_with_2_teams": int((game_teams == 2).sum()),
            "games_with_1_team": int((game_teams == 1).sum()),
            "games_with_other": int((game_teams > 2).sum()),
            "total_games": int(game_teams.count()),
            "team_id_distribution": team_dist_dict,
        }
    else:
        result = {
            "missing_rate": float(missing_rate),
            "error": "team_id or game_id column not found",
        }
    
    return result


def analyze_shots(df: pd.DataFrame) -> dict:
    """Shot 이벤트 분석"""
    shots = df[df["type_name"].str.lower() == "shot"].copy()
    
    if len(shots) == 0:
        return {
            "total_shots": 0,
            "error": "No Shot events found",
        }
    
    # 게임당/분당 Shot 빈도
    if "game_id" in df.columns:
        shots_per_game = shots.groupby("game_id").size()
        total_games = df["game_id"].nunique()
        avg_shots_per_game = shots_per_game.mean() if len(shots_per_game) > 0 else 0
    else:
        total_games = 1
        avg_shots_per_game = len(shots)
    
    # period_id별 Shot 분포
    period_dist = {}
    if "period_id" in shots.columns:
        period_dict = shots["period_id"].value_counts().to_dict()
        period_dist = {int(k): int(v) for k, v in period_dict.items()}
    
    # 시간 분포 (time_seconds)
    if "time_seconds" in shots.columns:
        time_stats = {
            "min": float(shots["time_seconds"].min()),
            "max": float(shots["time_seconds"].max()),
            "mean": float(shots["time_seconds"].mean()),
        }
    else:
        time_stats = {}
    
    return {
        "total_shots": int(len(shots)),
        "total_games": int(total_games),
        "avg_shots_per_game": float(avg_shots_per_game) if isinstance(avg_shots_per_game, (int, float)) else 0.0,
        "period_distribution": period_dist,
        "time_statistics": time_stats,
    }


def generate_report(summary: dict, output_path: str) -> None:
    """마크다운 리포트 생성"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Track2 데이터 EDA 리포트\n\n")
        f.write(f"생성일시: {pd.Timestamp.now()}\n\n")
        
        # 1. type_name 분석
        f.write("## 1. type_name 분석\n\n")
        type_info = summary["type_name"]
        f.write(f"- 고유값 개수: {type_info['unique_count']}\n")
        f.write(f"- 전체 이벤트 수: {type_info['total_events']:,}\n\n")
        f.write("### Top 30 type_name 빈도\n\n")
        f.write("| type_name | count |\n")
        f.write("|-----------|-------|\n")
        for t, count in list(type_info["top_30"].items())[:30]:
            f.write(f"| {t} | {count:,} |\n")
        f.write("\n")
        
        # 2. result_name 분석
        f.write("## 2. result_name 분석\n\n")
        result_info = summary["result_name"]
        f.write("### 분포\n\n")
        f.write("| result_name | count |\n")
        f.write("|-------------|-------|\n")
        for r, count in result_info["distribution"].items():
            f.write(f"| {r} | {count:,} |\n")
        f.write(f"\n- 빈 문자열: {result_info['empty_string_count']:,}\n")
        f.write(f"- NULL: {result_info['null_count']:,}\n\n")
        
        f.write("### Top 10 type_name별 result_name 교차표\n\n")
        for t, cross in result_info["top_10_type_cross_tab"].items():
            f.write(f"#### {t}\n\n")
            f.write("| result_name | count |\n")
            f.write("|-------------|-------|\n")
            for r, count in cross.items():
                f.write(f"| {r} | {count:,} |\n")
            f.write("\n")
        
        # 3. 좌표 분석
        f.write("## 3. 좌표 분석\n\n")
        coord_info = summary["coordinates"]
        for col, info in coord_info.items():
            if "error" in info:
                f.write(f"### {col}: {info['error']}\n\n")
                continue
            f.write(f"### {col}\n\n")
            f.write(f"- Min: {info['min']}\n")
            f.write(f"- Max: {info['max']}\n")
            f.write(f"- Mean: {info['mean']:.2f}\n")
            f.write(f"- 결측률: {info['missing_rate']*100:.2f}%\n")
            f.write(f"- 0 값 개수: {info['zero_count']:,}\n")
            f.write("\n#### Quantiles\n\n")
            for q, val in info["quantiles"].items():
                f.write(f"- {q}: {val}\n")
            f.write("\n")
        
        # 좌표 스케일 확정 근거
        f.write("### 좌표 스케일 확정 근거\n\n")
        if "end_x" in coord_info and "error" not in coord_info["end_x"]:
            x_info = coord_info["end_x"]
            f.write(f"- end_x 최대값: {x_info['max']}\n")
            f.write(f"- end_x 99% quantile: {x_info['quantiles']['99%']}\n")
            if x_info["max"] is not None and x_info["max"] <= 105:
                f.write("- **결론: 0~100 스케일로 보임 (피치 길이 105m 기준)**\n")
            elif x_info["max"] is not None and x_info["max"] <= 110:
                f.write("- **결론: 0~100 스케일 가능성 높음**\n")
            else:
                f.write("- **주의: 스케일 확인 필요**\n")
        f.write("\n")
        
        # 4. team_id 분석
        f.write("## 4. team_id 분석\n\n")
        team_info = summary["team_id"]
        if "error" not in team_info:
            f.write(f"- 결측률: {team_info['missing_rate']*100:.2f}%\n")
            f.write(f"- 2팀 게임: {team_info['games_with_2_teams']:,}\n")
            f.write(f"- 1팀 게임: {team_info['games_with_1_team']:,}\n")
            f.write(f"- 기타: {team_info['games_with_other']:,}\n")
            f.write(f"- 전체 게임 수: {team_info['total_games']:,}\n\n")
        else:
            f.write(f"- 오류: {team_info['error']}\n\n")
        
        # 5. Shot 분석
        f.write("## 5. Shot 이벤트 분석\n\n")
        shot_info = summary["shots"]
        if "error" not in shot_info:
            f.write(f"- 전체 Shot 수: {shot_info['total_shots']:,}\n")
            f.write(f"- 전체 게임 수: {shot_info['total_games']:,}\n")
            f.write(f"- 게임당 평균 Shot: {shot_info['avg_shots_per_game']:.2f}\n\n")
            if shot_info["period_distribution"]:
                f.write("### period_id별 분포\n\n")
                f.write("| period_id | count |\n")
                f.write("|-----------|-------|\n")
                for p, count in shot_info["period_distribution"].items():
                    f.write(f"| {p} | {count:,} |\n")
                f.write("\n")
        else:
            f.write(f"- 오류: {shot_info['error']}\n\n")


def main():
    parser = argparse.ArgumentParser(description="Track2 데이터 EDA")
    parser.add_argument(
        "--csv-path",
        type=str,
        default="00_data/Track2/raw_data.csv",
        help="Track2 CSV 파일 경로",
    )
    args = parser.parse_args()
    
    # 데이터 로드
    df = load_track2_data(args.csv_path)
    
    # 분석 수행
    print("Analyzing type_name...")
    type_info = analyze_type_name(df)
    
    print("Analyzing result_name...")
    result_info = analyze_result_name(df)
    
    print("Analyzing coordinates...")
    coord_info = analyze_coordinates(df)
    
    print("Analyzing team_id...")
    team_info = analyze_team_id(df)
    
    print("Analyzing shots...")
    shot_info = analyze_shots(df)
    
    # 결과 통합
    summary = {
        "type_name": type_info,
        "result_name": result_info,
        "coordinates": coord_info,
        "team_id": team_info,
        "shots": shot_info,
    }
    
    # 출력 디렉토리 생성
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    # JSON 저장
    json_path = artifacts_dir / "eda_track2_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSaved summary to: {json_path}")
    
    # 리포트 생성
    report_path = artifacts_dir / "eda_track2_report.md"
    generate_report(summary, str(report_path))
    print(f"Saved report to: {report_path}")
    
    print("\nEDA 완료!")


if __name__ == "__main__":
    main()

