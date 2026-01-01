#!/usr/bin/env python3
"""
will_have_shot 데이터셋 빌더

feature window: 과거 45초 (현재 포함) = [t-45, t]
label lookahead: 미래 10초 = (t, t+10]
label: will_have_shot = any(type_name == "Shot" for future events)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List

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
    print(f"Loaded {len(df):,} rows")
    return df


def extract_features(events: pd.DataFrame) -> Dict[str, float]:
    """이벤트 윈도우에서 피처 추출"""
    features = {}
    
    if len(events) == 0:
        return _empty_features()
    
    # 1. 기본 통계
    features["event_count"] = float(len(events))
    time_span = float(events["time_seconds"].max() - events["time_seconds"].min())
    features["time_span"] = time_span if time_span > 0 else 0.0
    features["event_rate"] = features["event_count"] / features["time_span"] if features["time_span"] > 0 else 0.0
    
    # 2. 이벤트 타입별 카운트
    type_counts = events["type_name"].value_counts()
    features["pass_count"] = float(type_counts.get("Pass", 0))
    features["carry_count"] = float(type_counts.get("Carry", 0))
    features["shot_count"] = float(type_counts.get("Shot", 0))
    features["duel_count"] = float(type_counts.get("Duel", 0))
    features["interception_count"] = float(type_counts.get("Interception", 0))
    
    # EDA 상위 타입들도 자동 추가 (최대 10개)
    top_types = type_counts.head(10).index.tolist()
    for t in top_types:
        if t not in ["Pass", "Carry", "Shot", "Duel", "Interception"]:
            features[f"type_{t.lower().replace(' ', '_')}_count"] = float(type_counts.get(t, 0))
    
    # 3. result_name 기반
    result_counts = events["result_name"].value_counts()
    features["successful_count"] = float(result_counts.get("Successful", 0))
    features["unsuccessful_count"] = float(result_counts.get("Unsuccessful", 0))
    features["unknown_result_count"] = float(
        (events["result_name"].isna() | (events["result_name"] == "")).sum()
    )
    total_with_result = features["successful_count"] + features["unsuccessful_count"]
    features["success_rate"] = (
        features["successful_count"] / total_with_result if total_with_result > 0 else 0.0
    )
    features["success_rate_with_unknown"] = (
        features["successful_count"] / features["event_count"] if features["event_count"] > 0 else 0.0
    )
    
    # 4. 패스/이동 공간 피처
    passes = events[
        (events["type_name"] == "Pass")
        & events["start_x"].notna()
        & events["end_x"].notna()
    ].copy()
    
    if len(passes) > 0:
        # dx, dy 계산 (컬럼에 있으면 사용, 없으면 계산)
        if "dx" in passes.columns and passes["dx"].notna().any():
            dx_list = passes["dx"].dropna().tolist()
        else:
            dx_list = (passes["end_x"] - passes["start_x"]).dropna().tolist()
        
        if "dy" in passes.columns and passes["dy"].notna().any():
            dy_list = passes["dy"].dropna().tolist()
        else:
            dy_list = (
                passes["end_y"] - passes["start_y"]
            ).dropna().tolist()
        
        features["mean_dx"] = float(np.mean(dx_list)) if dx_list else 0.0
        features["mean_dy"] = float(np.mean(dy_list)) if dy_list else 0.0
        features["std_dx"] = float(np.std(dx_list)) if dx_list else 0.0
        features["std_dy"] = float(np.std(dy_list)) if dy_list else 0.0
        features["forward_ratio"] = (
            sum(1 for d in dx_list if d > 0) / len(dx_list) if dx_list else 0.0
        )
        
        # 채널 분포 (y 좌표 기준, 0~68 스케일)
        # left: <22.7 (=68/3), right: >45.3 (=68×2/3)
        if passes["start_y"].notna().any():
            right = (passes["start_y"] > 45.3).sum()
            left = (passes["start_y"] < 22.7).sum()
            total = len(passes)
            features["right_ratio"] = right / total if total > 0 else 0.0
            features["left_ratio"] = left / total if total > 0 else 0.0
            features["center_ratio"] = 1.0 - features["right_ratio"] - features["left_ratio"]
        else:
            features["right_ratio"] = 0.0
            features["left_ratio"] = 0.0
            features["center_ratio"] = 0.0
    else:
        features["mean_dx"] = 0.0
        features["mean_dy"] = 0.0
        features["std_dx"] = 0.0
        features["std_dy"] = 0.0
        features["forward_ratio"] = 0.0
        features["right_ratio"] = 0.0
        features["left_ratio"] = 0.0
        features["center_ratio"] = 0.0
    
    # 5. 침투 지표
    features["final_third_entries"] = float(
        (events["end_x"].notna() & (events["end_x"] > 70)).sum())
    )
    features["penalty_area_entries"] = float(
        (events["end_x"].notna() & (events["end_x"] > 88)).sum()
    )
    
    # 6. 볼 소유 변화
    if "team_id" in events.columns and events["team_id"].notna().any():
        team_changes = (events["team_id"].diff() != 0).sum() - 1  # 첫 행 제외
        features["possession_changes"] = float(max(0, team_changes))
    else:
        features["possession_changes"] = 0.0
    
    return features


def _empty_features() -> Dict[str, float]:
    """빈 윈도우용 기본 피처"""
    return {
        "event_count": 0.0,
        "time_span": 0.0,
        "event_rate": 0.0,
        "pass_count": 0.0,
        "carry_count": 0.0,
        "shot_count": 0.0,
        "duel_count": 0.0,
        "interception_count": 0.0,
        "successful_count": 0.0,
        "unsuccessful_count": 0.0,
        "unknown_result_count": 0.0,
        "success_rate": 0.0,
        "success_rate_with_unknown": 0.0,
        "mean_dx": 0.0,
        "mean_dy": 0.0,
        "std_dx": 0.0,
        "std_dy": 0.0,
        "forward_ratio": 0.0,
        "right_ratio": 0.0,
        "left_ratio": 0.0,
        "center_ratio": 0.0,
        "final_third_entries": 0.0,
        "penalty_area_entries": 0.0,
        "possession_changes": 0.0,
    }


def generate_samples(
    df: pd.DataFrame,
    window_seconds: float = 45.0,
    lookahead_seconds: float = 10.0,
    stride_seconds: float = 5.0,
) -> pd.DataFrame:
    """윈도우 기반 샘플 생성"""
    samples = []
    feature_columns = None
    
    game_ids = df["game_id"].unique()
    print(f"Processing {len(game_ids)} games...")
    
    for game_id in game_ids:
        game_df = df[df["game_id"] == game_id].copy()
        game_df = game_df.sort_values("time_seconds")
        
        if len(game_df) == 0:
            continue
        
        min_time = game_df["time_seconds"].min()
        max_time = game_df["time_seconds"].max()
        
        # stride로 시간 포인트 생성
        current_time = min_time + window_seconds
        while current_time <= max_time - lookahead_seconds:
            # Feature window: [current_time - window_seconds, current_time]
            window_events = game_df[
                (game_df["time_seconds"] >= current_time - window_seconds)
                & (game_df["time_seconds"] <= current_time)
            ]
            
            # Label window: (current_time, current_time + lookahead_seconds]
            future_events = game_df[
                (game_df["time_seconds"] > current_time)
                & (game_df["time_seconds"] <= current_time + lookahead_seconds)
            ]
            
            # Label: will_have_shot (팀 기준)
            # 현재 시점 t에서 마지막 이벤트의 team_id(=공격 주체) 기준으로,
            # 미래 10초 내 그 팀의 Shot 발생 여부
            will_have_shot = False
            if len(window_events) > 0 and "team_id" in window_events.columns:
                # 마지막 이벤트의 team_id (현재 공격 주체)
                last_event = window_events.iloc[-1]
                attacking_team_id = last_event.get("team_id")
                
                if pd.notna(attacking_team_id) and len(future_events) > 0:
                    # 미래 10초 내 해당 팀의 Shot 발생 여부
                    team_shots = future_events[
                        (future_events["team_id"] == attacking_team_id)
                        & (future_events["type_name"].str.lower() == "shot")
                    ]
                    will_have_shot = len(team_shots) > 0
            else:
                # team_id가 없으면 기존 방식 (어떤 팀이든 Shot 발생)
                will_have_shot = (future_events["type_name"].str.lower() == "shot").any()
            
            # 피처 추출
            features = extract_features(window_events)
            
            # 첫 샘플에서 피처 컬럼 저장
            if feature_columns is None:
                feature_columns = list(features.keys())
            
            # 샘플 생성
            sample = {
                "game_id": game_id,
                "current_time": current_time,
                "will_have_shot": bool(will_have_shot),
                **features,
            }
            samples.append(sample)
            
            current_time += stride_seconds
    
    print(f"Generated {len(samples):,} samples")
    return pd.DataFrame(samples), feature_columns


def main():
    parser = argparse.ArgumentParser(description="will_have_shot 데이터셋 빌더")
    parser.add_argument(
        "--csv-path",
        type=str,
        default="00_data/Track2/raw_data.csv",
        help="Track2 CSV 파일 경로",
    )
    parser.add_argument(
        "--window-seconds",
        type=float,
        default=45.0,
        help="Feature window 크기 (초)",
    )
    parser.add_argument(
        "--lookahead-seconds",
        type=float,
        default=10.0,
        help="Label lookahead 크기 (초)",
    )
    parser.add_argument(
        "--stride-seconds",
        type=float,
        default=5.0,
        help="시간 stride (초)",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["parquet", "csv"],
        default="parquet",
        help="출력 형식",
    )
    args = parser.parse_args()
    
    # 데이터 로드
    df = load_track2_data(args.csv_path)
    
    # 샘플 생성
    dataset_df, feature_columns = generate_samples(
        df,
        window_seconds=args.window_seconds,
        lookahead_seconds=args.lookahead_seconds,
        stride_seconds=args.stride_seconds,
    )
    
    # 라벨 분포 확인
    label_counts = dataset_df["will_have_shot"].value_counts()
    positive_count = label_counts.get(True, 0)
    negative_count = label_counts.get(False, 0)
    total_count = len(dataset_df)
    positive_ratio = positive_count / total_count if total_count > 0 else 0.0
    
    print(f"\nLabel distribution:")
    print(f"  Positive (will_have_shot=True): {positive_count:,} ({positive_ratio*100:.2f}%)")
    print(f"  Negative (will_have_shot=False): {negative_count:,} ({(1-positive_ratio)*100:.2f}%)")
    print(f"  Total: {total_count:,}")
    
    # game_id별 양성 비율 분포
    if "game_id" in dataset_df.columns:
        game_stats = dataset_df.groupby("game_id")["will_have_shot"].agg(["sum", "count"])
        game_stats["positive_ratio"] = game_stats["sum"] / game_stats["count"]
        print(f"\nGame-level positive ratio:")
        print(f"  Mean: {game_stats['positive_ratio'].mean()*100:.2f}%")
        print(f"  Max: {game_stats['positive_ratio'].max()*100:.2f}%")
        print(f"  Min: {game_stats['positive_ratio'].min()*100:.2f}%")
        print(f"  Games with 0% positive: {(game_stats['positive_ratio'] == 0).sum()}")
        print(f"  Games with >10% positive: {(game_stats['positive_ratio'] > 0.1).sum()}")
    
    # 출력 디렉토리 생성
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    # 데이터셋 저장
    if args.output_format == "parquet":
        output_path = artifacts_dir / "will_have_shot_dataset.parquet"
        dataset_df.to_parquet(output_path, index=False)
    else:
        output_path = artifacts_dir / "will_have_shot_dataset.csv"
        dataset_df.to_csv(output_path, index=False)
    print(f"\nSaved dataset to: {output_path}")
    
    # 피처 컬럼 저장
    feature_columns_path = artifacts_dir / "feature_columns.json"
    with open(feature_columns_path, "w", encoding="utf-8") as f:
        json.dump(feature_columns, f, indent=2)
    print(f"Saved feature columns to: {feature_columns_path}")
    
    print("\nDataset build complete!")


if __name__ == "__main__":
    main()

