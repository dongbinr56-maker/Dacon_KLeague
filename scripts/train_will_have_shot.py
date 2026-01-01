#!/usr/bin/env python3
"""
will_have_shot 모델 학습/평가 스크립트

Split: game_id 홀드아웃 (시간 누수 방지)
모델: LogisticRegression, GradientBoostingClassifier
평가: PR-AUC, ROC-AUC, F1, Precision/Recall
"""

import argparse
import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """데이터셋 로드"""
    print(f"Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    if dataset_path.endswith(".parquet"):
        df = pd.read_parquet(dataset_path)
    else:
        df = pd.read_csv(dataset_path)
    
    print(f"Loaded {len(df):,} samples")
    return df


def load_feature_columns(feature_columns_path: str) -> list:
    """피처 컬럼 로드"""
    with open(feature_columns_path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_by_game_id(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> tuple:
    """game_id 기반 홀드아웃 split"""
    splitter = GroupShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    train_idx, test_idx = next(splitter.split(df, groups=df["game_id"]))
    
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    
    train_games = sorted(train_df["game_id"].unique().tolist())
    test_games = sorted(test_df["game_id"].unique().tolist())
    
    print(f"\nSplit results:")
    print(f"  Train: {len(train_df):,} samples from {len(train_games)} games")
    print(f"  Test: {len(test_df):,} samples from {len(test_games)} games")
    
    return train_df, test_df, train_games, test_games


def prepare_features(df: pd.DataFrame, feature_columns: list) -> tuple:
    """피처와 라벨 준비"""
    X = df[feature_columns].values
    y = df["will_have_shot"].astype(int).values
    
    # 결측치 처리 (0으로 채우기)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    return X, y


def train_models(X_train: np.ndarray, y_train: np.ndarray) -> dict:
    """여러 모델 학습"""
    models = {}
    
    # 1. LogisticRegression (표준화 필요)
    print("\nTraining LogisticRegression...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    lr = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
    )
    lr.fit(X_train_scaled, y_train)
    models["logistic_regression"] = {
        "model": lr,
        "scaler": scaler,
        "name": "LogisticRegression",
    }
    
    # 2. HistGradientBoostingClassifier (더 빠르고 효율적)
    print("Training HistGradientBoostingClassifier...")
    hgb = HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
    )
    hgb.fit(X_train, y_train)
    models["hist_gradient_boosting"] = {
        "model": hgb,
        "scaler": None,
        "name": "HistGradientBoostingClassifier",
    }
    
    return models


def evaluate_model(
    model_dict: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> dict:
    """모델 평가"""
    model = model_dict["model"]
    scaler = model_dict["scaler"]
    
    # 예측
    if scaler:
        X_train_scaled = scaler.transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        y_train_pred_proba = model.predict_proba(X_train_scaled)[:, 1]
        y_val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
    else:
        y_train_pred_proba = model.predict_proba(X_train)[:, 1]
        y_val_pred_proba = model.predict_proba(X_val)[:, 1]
    
    # 평가 지표
    train_auc = roc_auc_score(y_train, y_train_pred_proba)
    val_auc = roc_auc_score(y_val, y_val_pred_proba)
    
    train_pr_auc = average_precision_score(y_train, y_train_pred_proba)
    val_pr_auc = average_precision_score(y_val, y_val_pred_proba)
    
    # Threshold 선택 (val에서 F1 최대화)
    precision, recall, thresholds = precision_recall_curve(y_val, y_val_pred_proba)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    best_f1_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_f1_idx] if len(thresholds) > best_f1_idx else 0.5
    
    # Precision 우선 threshold (P >= 0.6)
    precision_target = 0.6
    precision_above_target = precision >= precision_target
    if precision_above_target.any():
        precision_threshold_idx = np.where(precision_above_target)[0][0]
        precision_threshold = (
            thresholds[precision_threshold_idx]
            if precision_threshold_idx < len(thresholds)
            else 0.5
        )
    else:
        precision_threshold = best_threshold
    
    # 선택된 threshold로 평가
    y_val_pred_f1 = (y_val_pred_proba >= best_threshold).astype(int)
    y_val_pred_precision = (y_val_pred_proba >= precision_threshold).astype(int)
    
    metrics = {
        "train_roc_auc": float(train_roc_auc),
        "val_roc_auc": float(val_roc_auc),
        "train_pr_auc": float(train_pr_auc),
        "val_pr_auc": float(val_pr_auc),  # 1순위 지표
        "best_threshold_f1": float(best_threshold),
        "best_threshold_precision": float(precision_threshold),
        "val_f1_at_best": float(f1_score(y_val, y_val_pred_f1)),
        "val_precision_at_best": float(precision_score(y_val, y_val_pred_f1)),
        "val_recall_at_best": float(recall_score(y_val, y_val_pred_f1)),
        "val_f1_at_precision": float(f1_score(y_val, y_val_pred_precision)),
        "val_precision_at_precision": float(precision_score(y_val, y_val_pred_precision)),
        "val_recall_at_precision": float(recall_score(y_val, y_val_pred_precision)),
    }
    
    return metrics, best_threshold, precision_threshold


def main():
    parser = argparse.ArgumentParser(description="will_have_shot 모델 학습")
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="artifacts/will_have_shot_dataset.parquet",
        help="데이터셋 파일 경로",
    )
    parser.add_argument(
        "--feature-columns-path",
        type=str,
        default="artifacts/feature_columns.json",
        help="피처 컬럼 파일 경로",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="테스트 세트 비율",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        choices=["logistic_regression", "hist_gradient_boosting"],
        default="hist_gradient_boosting",
        help="사용할 모델 (1차 베이스라인: 2개 모델만)",
    )
    args = parser.parse_args()
    
    # 데이터 로드
    df = load_dataset(args.dataset_path)
    feature_columns = load_feature_columns(args.feature_columns_path)
    
    # Split
    train_df, test_df, train_games, test_games = split_by_game_id(
        df, test_size=args.test_size
    )
    
    # 피처 준비
    X_train, y_train = prepare_features(train_df, feature_columns)
    X_test, y_test = prepare_features(test_df, feature_columns)
    
    # Validation split (train에서)
    train_train_df, train_val_df, _, _ = split_by_game_id(
        train_df, test_size=0.2, random_state=42
    )
    X_train_train, y_train_train = prepare_features(train_train_df, feature_columns)
    X_train_val, y_train_val = prepare_features(train_val_df, feature_columns)
    
    # 모델 학습
    models = train_models(X_train_train, y_train_train)
    
    # 모델 평가 및 선택 (PR-AUC 우선)
    print(f"\nEvaluating models (PR-AUC priority)...")
    best_model_name = None
    best_val_pr_auc = -1
    all_metrics = {}
    
    for model_name, model_dict in models.items():
        metrics, f1_threshold, precision_threshold = evaluate_model(
            model_dict,
            X_train_train,
            y_train_train,
            X_train_val,
            y_train_val,
        )
        all_metrics[model_name] = metrics
        
        print(f"\n{model_dict['name']}:")
        print(f"  Val PR-AUC (1순위): {metrics['val_pr_auc']:.4f}")
        print(f"  Val ROC-AUC: {metrics['val_roc_auc']:.4f}")
        print(f"  Val F1 (F1 최대 threshold): {metrics['val_f1_at_best']:.4f}")
        print(f"  Val Precision (F1 최대 threshold): {metrics['val_precision_at_best']:.4f}")
        print(f"  Val Recall (F1 최대 threshold): {metrics['val_recall_at_best']:.4f}")
        print(f"  Val F1 (Precision≥0.6 threshold): {metrics['val_f1_at_precision']:.4f}")
        print(f"  Val Precision (Precision≥0.6 threshold): {metrics['val_precision_at_precision']:.4f}")
        print(f"  Val Recall (Precision≥0.6 threshold): {metrics['val_recall_at_precision']:.4f}")
        
        if metrics["val_pr_auc"] > best_val_pr_auc:
            best_val_pr_auc = metrics["val_pr_auc"]
            best_model_name = model_name
    
    # 선택된 모델로 전체 train 학습
    print(f"\nRetraining best model ({models[best_model_name]['name']}) on full train set...")
    best_model_dict = models[best_model_name]
    
    if best_model_dict["scaler"]:
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        best_model_dict["model"].fit(X_train_scaled, y_train)
        best_model_dict["scaler"] = scaler
    else:
        best_model_dict["model"].fit(X_train, y_train)
    
    # Test 평가
    test_metrics, test_f1_threshold, test_precision_threshold = evaluate_model(
        best_model_dict,
        X_train,
        y_train,
        X_test,
        y_test,
    )
    
    print(f"\nTest set performance:")
    print(f"  Test PR-AUC (1순위): {test_metrics['val_pr_auc']:.4f}")
    print(f"  Test ROC-AUC: {test_metrics['val_roc_auc']:.4f}")
    print(f"  Test F1 (F1 최대 threshold): {test_metrics['val_f1_at_best']:.4f}")
    print(f"  Test Precision (F1 최대 threshold): {test_metrics['val_precision_at_best']:.4f}")
    print(f"  Test Recall (F1 최대 threshold): {test_metrics['val_recall_at_best']:.4f}")
    print(f"  Test F1 (Precision≥0.6 threshold): {test_metrics['val_f1_at_precision']:.4f}")
    print(f"  Test Precision (Precision≥0.6 threshold): {test_metrics['val_precision_at_precision']:.4f}")
    print(f"  Test Recall (Precision≥0.6 threshold): {test_metrics['val_recall_at_precision']:.4f}")
    
    # 모델 저장
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    
    model_data = {
        "model": best_model_dict["model"],
        "scaler": best_model_dict["scaler"],
        "feature_columns": feature_columns,
        "threshold_f1": float(test_f1_threshold),
        "threshold_precision": float(test_precision_threshold),
        "window_sec": 45.0,
        "lookahead_sec": 10.0,
        "stride_sec": 5.0,
        "train_games": train_games,
        "test_games": test_games,
        "metrics": {
            "all_models": all_metrics,
            "best_model": test_metrics,
            "test_pr_auc": float(test_metrics["val_pr_auc"]),
            "test_roc_auc": float(test_metrics["val_roc_auc"]),
            "test_precision_at_precision_threshold": float(test_metrics["val_precision_at_precision"]),
            "test_recall_at_precision_threshold": float(test_metrics["val_recall_at_precision"]),
            "test_f1_at_precision_threshold": float(test_metrics["val_f1_at_precision"]),
        },
    }
    
    model_path = artifacts_dir / "will_have_shot_model.joblib"
    joblib.dump(model_data, model_path)
    print(f"\nSaved model to: {model_path}")
    
    # 메트릭 저장
    metrics_path = artifacts_dir / "will_have_shot_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_model": best_model_name,
                "all_models": all_metrics,
                "test_metrics": test_metrics,
                "positive_ratio": float(y_test.mean()),
            },
            f,
            indent=2,
        )
    print(f"Saved metrics to: {metrics_path}")
    
    print("\nTraining complete!")


if __name__ == "__main__":
    from sklearn.metrics import recall_score  # noqa: F401
    
    main()

