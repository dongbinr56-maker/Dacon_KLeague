#!/usr/bin/env python3
"""
StatsBomb 압박 이벤트를 Track2 데이터에 통합하는 스크립트

StatsBomb의 under_pressure, counterpress 이벤트를 Track2 이벤트 로그에 매핑하여
압박 관련 피처를 생성합니다.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm


def load_statsbomb_events(statsbomb_dir: Path) -> Dict[str, List[Dict]]:
    """StatsBomb 이벤트 데이터 로드"""
    events_dir = statsbomb_dir / "data" / "events"
    if not events_dir.exists():
        raise FileNotFoundError(f"StatsBomb events directory not found: {events_dir}")
    
    event_files = list(events_dir.glob("*.json"))
    print(f"Found {len(event_files)} StatsBomb event files")
    
    all_events = {}
    for event_file in tqdm(event_files, desc="Loading StatsBomb events"):
        match_id = event_file.stem
        try:
            with open(event_file, "r") as f:
                events = json.load(f)
                # 실제 이벤트만 필터링
                actual_events = [
                    e for e in events
                    if isinstance(e, dict) and e.get("type", {}).get("name") not in [
                        "Starting XI", "Half Start", "Half End", "Formation Change"
                    ]
                ]
                all_events[match_id] = actual_events
        except Exception as e:
            print(f"Error loading {event_file}: {e}")
            continue
    
    return all_events


def extract_pressure_features(events: List[Dict], time_window: float = 10.0) -> Dict[str, float]:
    """이벤트 리스트에서 압박 관련 피처 추출"""
    features = {
        "pressure_event_count": 0.0,
        "under_pressure_count": 0.0,
        "counterpress_count": 0.0,
        "pressure_rate": 0.0,
        "recent_pressure_count": 0.0,
        "pressure_intensity": 0.0,
    }
    
    if not events:
        return features
    
    # 시간 기반 정렬 (timestamp 또는 minute+second)
    sorted_events = sorted(
        events,
        key=lambda e: (
            e.get("minute", 0) * 60 + e.get("second", 0)
            if "minute" in e
            else float(e.get("timestamp", "0:0").split(":")[0]) * 60 + float(e.get("timestamp", "0:0").split(":")[1])
            if "timestamp" in e and isinstance(e["timestamp"], str)
            else 0
        )
    )
    
    # 압박 이벤트 카운트
    pressure_events = [
        e for e in sorted_events
        if e.get("under_pressure") is True or e.get("counterpress") is True
    ]
    
    features["pressure_event_count"] = float(len(pressure_events))
    features["under_pressure_count"] = float(sum(1 for e in sorted_events if e.get("under_pressure") is True))
    features["counterpress_count"] = float(sum(1 for e in sorted_events if e.get("counterpress") is True))
    features["pressure_rate"] = features["pressure_event_count"] / len(sorted_events) if sorted_events else 0.0
    
    # 최근 시간 윈도우 내 압박 이벤트
    if sorted_events:
        last_time = (
            sorted_events[-1].get("minute", 0) * 60 + sorted_events[-1].get("second", 0)
            if "minute" in sorted_events[-1]
            else float(sorted_events[-1].get("timestamp", "0:0").split(":")[0]) * 60 + float(sorted_events[-1].get("timestamp", "0:0").split(":")[1])
            if "timestamp" in sorted_events[-1] and isinstance(sorted_events[-1]["timestamp"], str)
            else 0
        )
        
        recent_pressure = [
            e for e in pressure_events
            if (
                (e.get("minute", 0) * 60 + e.get("second", 0)) >= (last_time - time_window)
                if "minute" in e
                else True  # timestamp 형식이 다를 수 있으므로 일단 포함
            )
        ]
        features["recent_pressure_count"] = float(len(recent_pressure))
    
    # 압박 강도 (연속 압박 이벤트 수)
    if len(pressure_events) > 1:
        # 연속 압박 이벤트 그룹 찾기
        consecutive_groups = []
        current_group = [pressure_events[0]]
        for i in range(1, len(pressure_events)):
            prev_time = pressure_events[i-1].get("minute", 0) * 60 + pressure_events[i-1].get("second", 0)
            curr_time = pressure_events[i].get("minute", 0) * 60 + pressure_events[i].get("second", 0)
            if curr_time - prev_time <= 5.0:  # 5초 이내면 연속으로 간주
                current_group.append(pressure_events[i])
            else:
                if len(current_group) > 1:
                    consecutive_groups.append(len(current_group))
                current_group = [pressure_events[i]]
        if len(current_group) > 1:
            consecutive_groups.append(len(current_group))
        
        features["pressure_intensity"] = float(max(consecutive_groups)) if consecutive_groups else 0.0
    
    return features


def match_track2_to_statsbomb(track2_df: pd.DataFrame, statsbomb_events: Dict[str, List[Dict]]) -> pd.DataFrame:
    """Track2 데이터와 StatsBomb 이벤트 매칭"""
    # 매칭 전략:
    # 1. game_id 직접 매칭 (가능하면)
    # 2. 시간 기반 윈도우 매칭
    # 3. 압박 피처 생성
    
    print("Matching Track2 to StatsBomb events...")
    
    # Track2의 game_id 목록
    track2_games = track2_df["game_id"].unique()
    print(f"Track2 games: {len(track2_games)}")
    print(f"StatsBomb matches: {len(statsbomb_events)}")
    
    # 매칭 결과 저장
    pressure_features_list = []
    
    for game_id in tqdm(track2_games, desc="Processing games"):
        game_events = track2_df[track2_df["game_id"] == game_id].copy()
        
        # StatsBomb 매칭 시도 (game_id 직접 매칭 또는 첫 번째 매치 사용)
        matched_statsbomb = None
        for match_id, events in statsbomb_events.items():
            # 간단한 매칭: game_id가 포함되어 있거나 첫 번째 매치 사용
            if str(game_id) in match_id or match_id.startswith(str(game_id)):
                matched_statsbomb = events
                break
        
        # 매칭되지 않으면 첫 번째 매치 사용 (프로토타입)
        if matched_statsbomb is None and statsbomb_events:
            matched_statsbomb = list(statsbomb_events.values())[0]
        
        if matched_statsbomb:
            # 시간 윈도우별로 압박 피처 추출
            for idx, row in game_events.iterrows():
                # 현재 시간 기준으로 윈도우 설정
                current_time = row["time_seconds"]
                window_start = max(0, current_time - 45)  # 45초 윈도우
                window_end = current_time
                
                # StatsBomb 이벤트를 시간 윈도우로 필터링
                window_events = [
                    e for e in matched_statsbomb
                    if window_start <= (e.get("minute", 0) * 60 + e.get("second", 0)) <= window_end
                ]
                
                # 압박 피처 추출
                pressure_features = extract_pressure_features(window_events)
                pressure_features["game_id"] = game_id
                pressure_features["action_id"] = row["action_id"]
                pressure_features_list.append(pressure_features)
        else:
            # 매칭되지 않으면 기본값
            for idx, row in game_events.iterrows():
                pressure_features = {
                    "game_id": game_id,
                    "action_id": row["action_id"],
                    "pressure_event_count": 0.0,
                    "under_pressure_count": 0.0,
                    "counterpress_count": 0.0,
                    "pressure_rate": 0.0,
                    "recent_pressure_count": 0.0,
                    "pressure_intensity": 0.0,
                }
                pressure_features_list.append(pressure_features)
    
    pressure_df = pd.DataFrame(pressure_features_list)
    return pressure_df


def main():
    parser = argparse.ArgumentParser(description="StatsBomb 압박 이벤트 통합")
    parser.add_argument(
        "--statsbomb-dir",
        type=str,
        default=os.path.expanduser("~/Downloads/football_datasets/open-data"),
        help="StatsBomb 데이터 디렉토리",
    )
    parser.add_argument(
        "--track2-csv",
        type=str,
        default="00_data/Track2/raw_data.csv",
        help="Track2 CSV 파일 경로",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/track2_with_pressure.parquet",
        help="출력 파일 경로",
    )
    args = parser.parse_args()
    
    # StatsBomb 이벤트 로드
    print("=== StatsBomb 압박 이벤트 통합 ===")
    statsbomb_dir = Path(args.statsbomb_dir)
    statsbomb_events = load_statsbomb_events(statsbomb_dir)
    
    # Track2 데이터 로드
    print(f"\nLoading Track2 data from: {args.track2_csv}")
    track2_df = pd.read_csv(args.track2_csv, low_memory=False)
    print(f"Loaded {len(track2_df):,} Track2 events")
    
    # 매칭 및 압박 피처 생성
    pressure_df = match_track2_to_statsbomb(track2_df, statsbomb_events)
    
    # Track2와 병합
    merged_df = track2_df.merge(
        pressure_df[["game_id", "action_id", "pressure_event_count", "under_pressure_count", 
                     "counterpress_count", "pressure_rate", "recent_pressure_count", "pressure_intensity"]],
        on=["game_id", "action_id"],
        how="left"
    )
    
    # NaN 값 처리
    pressure_cols = ["pressure_event_count", "under_pressure_count", "counterpress_count", 
                     "pressure_rate", "recent_pressure_count", "pressure_intensity"]
    for col in pressure_cols:
        merged_df[col] = merged_df[col].fillna(0.0)
    
    # 저장
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_parquet(output_path, index=False)
    print(f"\nSaved merged data to: {output_path}")
    print(f"Total rows: {len(merged_df):,}")
    print(f"Pressure features added: {len(pressure_cols)}")
    print(f"Rows with pressure events: {(merged_df['pressure_event_count'] > 0).sum():,}")


if __name__ == "__main__":
    main()

