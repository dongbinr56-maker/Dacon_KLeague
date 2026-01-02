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
    
    # 5. 침투 지표 (x축 0~105 기준)
    # final_third: 70 (=105×2/3)
    # penalty_area: 88.5 (=105-16.5), 실무적으로 >88 사용
    features["final_third_entries"] = float(
        (events["end_x"].notna() & (events["end_x"] > 70)).sum()
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
    
    # 7. 시퀀스 피처 다층화 (1초/5초/10초/20초 윈도우)
    # GPT 답변: 여러 시간 범위를 동시에 반영하여 짧은 순간의 패턴 + 긴 관점의 흐름을 동시에 학습
    if len(events) > 0:
        current_time = events["time_seconds"].max()
        
        # 시간 기반 윈도우 (1초, 5초, 10초, 20초)
        for window_sec in [1, 5, 10, 20]:
            window_events = events[events["time_seconds"] >= current_time - window_sec]
            
            if len(window_events) > 0:
                window_types = window_events["type_name"].value_counts()
                # 주요 타입들의 빈도
                for t in ["Pass", "Carry", "Shot", "Duel"]:
                    features[f"past_{window_sec}s_{t.lower()}_count"] = float(window_types.get(t, 0))
                
                # 윈도우 내 이벤트 수
                features[f"past_{window_sec}s_event_count"] = float(len(window_events))
                
                # 윈도우 내 성공률
                window_successful = (window_events["result_name"] == "Successful").sum()
                features[f"past_{window_sec}s_success_rate"] = float(window_successful / len(window_events))
                
                # 윈도우 내 평균 x 좌표 (공격 방향)
                if window_events["end_x"].notna().any():
                    features[f"past_{window_sec}s_mean_end_x"] = float(window_events["end_x"].mean())
                    features[f"past_{window_sec}s_max_end_x"] = float(window_events["end_x"].max())
                else:
                    features[f"past_{window_sec}s_mean_end_x"] = 0.0
                    features[f"past_{window_sec}s_max_end_x"] = 0.0
                
                # 윈도우 내 이벤트 간격 통계
                if len(window_events) > 1:
                    window_time_diffs = window_events["time_seconds"].diff().dropna()
                    if len(window_time_diffs) > 0:
                        features[f"past_{window_sec}s_interval_mean"] = float(window_time_diffs.mean())
                        features[f"past_{window_sec}s_interval_std"] = float(window_time_diffs.std() if len(window_time_diffs) > 1 else 0.0)
                    else:
                        features[f"past_{window_sec}s_interval_mean"] = 0.0
                        features[f"past_{window_sec}s_interval_std"] = 0.0
                else:
                    features[f"past_{window_sec}s_interval_mean"] = 0.0
                    features[f"past_{window_sec}s_interval_std"] = 0.0
            else:
                for t in ["Pass", "Carry", "Shot", "Duel"]:
                    features[f"past_{window_sec}s_{t.lower()}_count"] = 0.0
                features[f"past_{window_sec}s_event_count"] = 0.0
                features[f"past_{window_sec}s_success_rate"] = 0.0
                features[f"past_{window_sec}s_mean_end_x"] = 0.0
                features[f"past_{window_sec}s_max_end_x"] = 0.0
                features[f"past_{window_sec}s_interval_mean"] = 0.0
                features[f"past_{window_sec}s_interval_std"] = 0.0
        
        # 최근 N개 이벤트 (기존 유지, 호환성)
        for n in [5, 10]:
            recent_events = events.tail(n)
            if len(recent_events) > 0:
                recent_types = recent_events["type_name"].value_counts()
                for t in ["Pass", "Carry", "Shot", "Duel"]:
                    features[f"recent_{n}_{t.lower()}_count"] = float(recent_types.get(t, 0))
                recent_successful = (recent_events["result_name"] == "Successful").sum()
                features[f"recent_{n}_success_rate"] = float(recent_successful / len(recent_events))
                if recent_events["end_x"].notna().any():
                    features[f"recent_{n}_mean_end_x"] = float(recent_events["end_x"].mean())
                else:
                    features[f"recent_{n}_mean_end_x"] = 0.0
            else:
                for t in ["Pass", "Carry", "Shot", "Duel"]:
                    features[f"recent_{n}_{t.lower()}_count"] = 0.0
                features[f"recent_{n}_success_rate"] = 0.0
                features[f"recent_{n}_mean_end_x"] = 0.0
    else:
        # 빈 윈도우 처리
        for window_sec in [1, 5, 10, 20]:
            for t in ["Pass", "Carry", "Shot", "Duel"]:
                features[f"past_{window_sec}s_{t.lower()}_count"] = 0.0
            features[f"past_{window_sec}s_event_count"] = 0.0
            features[f"past_{window_sec}s_success_rate"] = 0.0
            features[f"past_{window_sec}s_mean_end_x"] = 0.0
            features[f"past_{window_sec}s_max_end_x"] = 0.0
            features[f"past_{window_sec}s_interval_mean"] = 0.0
            features[f"past_{window_sec}s_interval_std"] = 0.0
        for n in [5, 10]:
            for t in ["Pass", "Carry", "Shot", "Duel"]:
                features[f"recent_{n}_{t.lower()}_count"] = 0.0
            features[f"recent_{n}_success_rate"] = 0.0
            features[f"recent_{n}_mean_end_x"] = 0.0
    
    # 8. 이벤트 간격 통계 (mean/std)
    if len(events) > 1:
        time_diffs = events["time_seconds"].diff().dropna()
        if len(time_diffs) > 0:
            features["event_interval_mean"] = float(time_diffs.mean())
            features["event_interval_std"] = float(time_diffs.std() if len(time_diffs) > 1 else 0.0)
            features["event_interval_min"] = float(time_diffs.min())
            features["event_interval_max"] = float(time_diffs.max())
        else:
            features["event_interval_mean"] = 0.0
            features["event_interval_std"] = 0.0
            features["event_interval_min"] = 0.0
            features["event_interval_max"] = 0.0
    else:
        features["event_interval_mean"] = 0.0
        features["event_interval_std"] = 0.0
        features["event_interval_min"] = 0.0
        features["event_interval_max"] = 0.0
    
    # 9. 최근 10초 vs 이전 10초 비교 피처 (공격 강도 변화)
    if len(events) > 0:
        current_time = events["time_seconds"].max()
        recent_10s = events[events["time_seconds"] >= current_time - 10]
        previous_10s = events[
            (events["time_seconds"] >= current_time - 20) & 
            (events["time_seconds"] < current_time - 10)
        ]
        
        # 이벤트 수 비교
        features["recent_10s_event_count"] = float(len(recent_10s))
        features["previous_10s_event_count"] = float(len(previous_10s))
        features["event_count_change"] = features["recent_10s_event_count"] - features["previous_10s_event_count"]
        
        # 공격 진입 비교 (x 좌표)
        if recent_10s["end_x"].notna().any():
            features["recent_10s_mean_end_x"] = float(recent_10s["end_x"].mean())
        else:
            features["recent_10s_mean_end_x"] = 0.0
        
        if previous_10s["end_x"].notna().any():
            features["previous_10s_mean_end_x"] = float(previous_10s["end_x"].mean())
        else:
            features["previous_10s_mean_end_x"] = 0.0
        
        features["end_x_change"] = features["recent_10s_mean_end_x"] - features["previous_10s_mean_end_x"]
        
        # 성공률 비교
        if len(recent_10s) > 0:
            features["recent_10s_success_rate"] = float((recent_10s["result_name"] == "Successful").sum() / len(recent_10s))
        else:
            features["recent_10s_success_rate"] = 0.0
        
        if len(previous_10s) > 0:
            features["previous_10s_success_rate"] = float((previous_10s["result_name"] == "Successful").sum() / len(previous_10s))
        else:
            features["previous_10s_success_rate"] = 0.0
        
        features["success_rate_change"] = features["recent_10s_success_rate"] - features["previous_10s_success_rate"]
    else:
        features["recent_10s_event_count"] = 0.0
        features["previous_10s_event_count"] = 0.0
        features["event_count_change"] = 0.0
        features["recent_10s_mean_end_x"] = 0.0
        features["previous_10s_mean_end_x"] = 0.0
        features["end_x_change"] = 0.0
        features["recent_10s_success_rate"] = 0.0
        features["previous_10s_success_rate"] = 0.0
        features["success_rate_change"] = 0.0
    
    # 10. 통계적 피처 (분산, 왜도, 첨도 등)
    if len(events) > 1:
        # x 좌표 분산 (공격 분산도)
        if events["end_x"].notna().any():
            end_x_values = events["end_x"].dropna()
            if len(end_x_values) > 1:
                features["end_x_variance"] = float(end_x_values.var())
                features["end_x_std"] = float(end_x_values.std())
            else:
                features["end_x_variance"] = 0.0
                features["end_x_std"] = 0.0
        else:
            features["end_x_variance"] = 0.0
            features["end_x_std"] = 0.0
        
        # y 좌표 분산 (측면 분산도)
        if events["end_y"].notna().any():
            end_y_values = events["end_y"].dropna()
            if len(end_y_values) > 1:
                features["end_y_variance"] = float(end_y_values.var())
                features["end_y_std"] = float(end_y_values.std())
            else:
                features["end_y_variance"] = 0.0
                features["end_y_std"] = 0.0
        else:
            features["end_y_variance"] = 0.0
            features["end_y_std"] = 0.0
        
        # 시간 기반 트렌드 (최근 이벤트가 더 공격적인지)
        if len(events) >= 3:
            sorted_events = events.sort_values("time_seconds")
            first_third = sorted_events.iloc[:len(sorted_events)//3]
            last_third = sorted_events.iloc[-len(sorted_events)//3:]
            
            if first_third["end_x"].notna().any() and last_third["end_x"].notna().any():
                first_mean_x = float(first_third["end_x"].mean())
                last_mean_x = float(last_third["end_x"].mean())
                features["attack_trend"] = last_mean_x - first_mean_x
            else:
                features["attack_trend"] = 0.0
        else:
            features["attack_trend"] = 0.0
    else:
        features["end_x_variance"] = 0.0
        features["end_x_std"] = 0.0
        features["end_y_variance"] = 0.0
        features["end_y_std"] = 0.0
        features["attack_trend"] = 0.0
    
    # 11. 압박 프록시 피처 개선 (이벤트 로그만으로 가능한 압박 추정)
    if features["event_count"] > 0:
        # 실패 이벤트 밀도 (높을수록 압박 가능성)
        failure_rate = features["unsuccessful_count"] / features["event_count"]
        features["pressure_proxy_failure_rate"] = failure_rate
        
        # 짧은 시간 내 실패 이벤트 집중도
        if len(events) >= 3:
            sorted_events = events.sort_values("time_seconds")
            time_windows = []
            for i in range(len(sorted_events) - 2):
                window = sorted_events.iloc[i:i+3]
                window_time = float(window["time_seconds"].max() - window["time_seconds"].min())
                if window_time <= 5.0:  # 5초 이내
                    failures = (window["result_name"] == "Unsuccessful").sum()
                    time_windows.append(failures / window_time if window_time > 0 else 0)
            features["pressure_proxy_failure_density"] = float(max(time_windows)) if time_windows else 0.0
        else:
            features["pressure_proxy_failure_density"] = 0.0
        
        # 턴오버 직후 재턴오버 (압박 지표)
        if "team_id" in events.columns and events["team_id"].notna().any():
            team_changes = events[events["team_id"].diff() != 0]
            if len(team_changes) >= 2:
                # 턴오버 후 5초 내 재턴오버
                turnover_after_turnover = 0
                for i in range(len(team_changes) - 1):
                    time_diff = float(team_changes.iloc[i+1]["time_seconds"] - team_changes.iloc[i]["time_seconds"])
                    if time_diff <= 5.0:
                        turnover_after_turnover += 1
                features["pressure_proxy_rapid_turnover"] = float(turnover_after_turnover)
            else:
                features["pressure_proxy_rapid_turnover"] = 0.0
        else:
            features["pressure_proxy_rapid_turnover"] = 0.0
    else:
        features["pressure_proxy_failure_rate"] = 0.0
        features["pressure_proxy_failure_density"] = 0.0
        features["pressure_proxy_rapid_turnover"] = 0.0
    
    # 12. 상호작용 피처 생성 (GPT 답변: 피처 쌍의 곱/비율/차이)
    # 주요 피처 쌍의 상호작용을 반영하여 모델이 피처 간 관계를 학습할 수 있도록 함
    if features["event_count"] > 0:
        # 패스-성공률 상호작용
        if features["pass_count"] > 0:
            features["pass_success_interaction"] = features["pass_count"] * features["success_rate"]
            features["pass_success_ratio"] = features["successful_count"] / features["pass_count"] if features["pass_count"] > 0 else 0.0
        else:
            features["pass_success_interaction"] = 0.0
            features["pass_success_ratio"] = 0.0
        
        # 공격 진입-이벤트 밀도 상호작용
        features["final_third_event_density"] = features["final_third_entries"] / features["event_count"] if features["event_count"] > 0 else 0.0
        features["penalty_area_event_density"] = features["penalty_area_entries"] / features["event_count"] if features["event_count"] > 0 else 0.0
        
        # 전진 비율-공격 진입 상호작용
        if features["forward_ratio"] > 0:
            features["forward_final_third_interaction"] = features["forward_ratio"] * features["final_third_entries"]
        else:
            features["forward_final_third_interaction"] = 0.0
        
        # 이벤트 밀도-성공률 상호작용
        features["event_rate_success_interaction"] = features["event_rate"] * features["success_rate"]
        
        # 침투 지표 차이 (final_third - penalty_area)
        features["penetration_depth"] = features["final_third_entries"] - features["penalty_area_entries"]
        
        # 채널 분포 상호작용 (중앙 집중도)
        features["center_attack_interaction"] = features["center_ratio"] * features["final_third_entries"]
        
        # 압박 프록시 상호작용
        features["pressure_attack_interaction"] = features["pressure_proxy_failure_rate"] * features["final_third_entries"]
        features["pressure_trend_interaction"] = features["pressure_proxy_failure_density"] * features["attack_trend"]
        
        # 분산 기반 상호작용
        features["variance_attack_interaction"] = features["end_x_std"] * features["final_third_entries"]
        features["variance_trend_interaction"] = features["end_x_std"] * abs(features["attack_trend"])
    else:
        features["pass_success_interaction"] = 0.0
        features["pass_success_ratio"] = 0.0
        features["final_third_event_density"] = 0.0
        features["penalty_area_event_density"] = 0.0
        features["forward_final_third_interaction"] = 0.0
        features["event_rate_success_interaction"] = 0.0
        features["penetration_depth"] = 0.0
        features["center_attack_interaction"] = 0.0
        features["pressure_attack_interaction"] = 0.0
        features["pressure_trend_interaction"] = 0.0
        features["variance_attack_interaction"] = 0.0
        features["variance_trend_interaction"] = 0.0
    
    return features


def _empty_features() -> Dict[str, float]:
    """빈 윈도우용 기본 피처"""
    features = {
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
    
    # 시퀀스 피처 다층화 (1초/5초/10초/20초 윈도우)
    for window_sec in [1, 5, 10, 20]:
        for t in ["pass", "carry", "shot", "duel"]:
            features[f"past_{window_sec}s_{t}_count"] = 0.0
        features[f"past_{window_sec}s_event_count"] = 0.0
        features[f"past_{window_sec}s_success_rate"] = 0.0
        features[f"past_{window_sec}s_mean_end_x"] = 0.0
        features[f"past_{window_sec}s_max_end_x"] = 0.0
        features[f"past_{window_sec}s_interval_mean"] = 0.0
        features[f"past_{window_sec}s_interval_std"] = 0.0
    
    # 최근 N개 이벤트 (기존 호환성)
    for n in [5, 10]:
        for t in ["pass", "carry", "shot", "duel"]:
            features[f"recent_{n}_{t}_count"] = 0.0
        features[f"recent_{n}_success_rate"] = 0.0
        features[f"recent_{n}_mean_end_x"] = 0.0
    
    # 이벤트 간격 통계
    features["event_interval_mean"] = 0.0
    features["event_interval_std"] = 0.0
    features["event_interval_min"] = 0.0
    features["event_interval_max"] = 0.0
    
    # 최근 10초 vs 이전 10초 비교
    features["recent_10s_event_count"] = 0.0
    features["previous_10s_event_count"] = 0.0
    features["event_count_change"] = 0.0
    features["recent_10s_mean_end_x"] = 0.0
    features["previous_10s_mean_end_x"] = 0.0
    features["end_x_change"] = 0.0
    features["recent_10s_success_rate"] = 0.0
    features["previous_10s_success_rate"] = 0.0
    features["success_rate_change"] = 0.0
    
    # 통계적 피처
    features["end_x_variance"] = 0.0
    features["end_x_std"] = 0.0
    features["end_y_variance"] = 0.0
    features["end_y_std"] = 0.0
    features["attack_trend"] = 0.0
    
    # 압박 프록시 피처
    features["pressure_proxy_failure_rate"] = 0.0
    features["pressure_proxy_failure_density"] = 0.0
    features["pressure_proxy_rapid_turnover"] = 0.0
    
    # 상호작용 피처
    features["pass_success_interaction"] = 0.0
    features["pass_success_ratio"] = 0.0
    features["final_third_event_density"] = 0.0
    features["penalty_area_event_density"] = 0.0
    features["forward_final_third_interaction"] = 0.0
    features["event_rate_success_interaction"] = 0.0
    features["penetration_depth"] = 0.0
    features["center_attack_interaction"] = 0.0
    features["pressure_attack_interaction"] = 0.0
    features["pressure_trend_interaction"] = 0.0
    features["variance_attack_interaction"] = 0.0
    features["variance_trend_interaction"] = 0.0
    
    return features


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

