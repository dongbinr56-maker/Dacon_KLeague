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
from tqdm import tqdm
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    make_scorer,
    precision_recall_curve,
    precision_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    GridSearchCV,
    GroupShuffleSplit,
    RandomizedSearchCV,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def load_dataset(dataset_path: str) -> pd.DataFrame:
    """데이터셋 로드"""
    print(f"Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    with tqdm(total=1, desc="Loading dataset", unit="file") as pbar:
        if dataset_path.endswith(".parquet"):
            df = pd.read_parquet(dataset_path)
        else:
            df = pd.read_csv(dataset_path)
        pbar.update(1)
    
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


def train_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    groups: np.ndarray = None,
    tune_hyperparams: bool = False,
) -> dict:
    """여러 모델 학습 (하이퍼파라미터 튜닝 옵션 포함)"""
    models = {}
    
    # 1. LogisticRegression (표준화 필요)
    print("\nTraining LogisticRegression...")
    scaler = StandardScaler()
    with tqdm(total=1, desc="  Scaling features", unit="step") as pbar:
        X_train_scaled = scaler.fit_transform(X_train)
        pbar.update(1)
    
    if tune_hyperparams and groups is not None:
        print("  Tuning hyperparameters...")
        param_grid = {
            "C": [0.01, 0.1, 1.0, 10.0, 100.0],
            "solver": ["lbfgs", "liblinear"],
            "class_weight": ["balanced", None],
        }
        # PR-AUC를 최대화하는 하이퍼파라미터 찾기
        pr_auc_scorer = make_scorer(average_precision_score, needs_proba=True)
        cv = GroupShuffleSplit(n_splits=3, test_size=0.2, random_state=42)
        grid_search = GridSearchCV(
            LogisticRegression(max_iter=1000, random_state=42),
            param_grid,
            cv=cv,
            scoring=pr_auc_scorer,
            n_jobs=-1,
            verbose=0,  # tqdm과 충돌 방지
        )
        # GridSearchCV 진행 표시
        total_combinations = len(param_grid["C"]) * len(param_grid["solver"]) * len(param_grid["class_weight"])
        with tqdm(total=total_combinations * 3, desc="  GridSearchCV", unit="fold") as pbar:
            grid_search.fit(X_train_scaled, y_train, groups=groups)
            pbar.update(total_combinations * 3)
        lr = grid_search.best_estimator_
        print(f"  Best params: {grid_search.best_params_}")
        print(f"  Best CV score (PR-AUC): {grid_search.best_score_:.4f}")
    else:
        lr = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )
        with tqdm(total=1, desc="  Training", unit="model") as pbar:
            lr.fit(X_train_scaled, y_train)
            pbar.update(1)
    
    models["logistic_regression"] = {
        "model": lr,
        "scaler": scaler,
        "name": "LogisticRegression",
    }
    
    # 2. HistGradientBoostingClassifier (더 빠르고 효율적)
    print("Training HistGradientBoostingClassifier...")
    if tune_hyperparams and groups is not None:
        print("  Tuning hyperparameters...")
        param_grid = {
            "max_iter": [50, 100, 200],
            "learning_rate": [0.05, 0.1, 0.2],
            "max_depth": [3, 5, 7],
            "min_samples_leaf": [10, 20, 30],
        }
        pr_auc_scorer = make_scorer(average_precision_score, needs_proba=True)
        cv = GroupShuffleSplit(n_splits=3, test_size=0.2, random_state=42)
        # RandomizedSearchCV 사용 (GridSearchCV보다 빠름)
        random_search = RandomizedSearchCV(
            HistGradientBoostingClassifier(random_state=42),
            param_grid,
            n_iter=20,  # 20개 조합만 시도
            cv=cv,
            scoring=pr_auc_scorer,
            n_jobs=-1,
            random_state=42,
            verbose=0,  # tqdm과 충돌 방지
        )
        # RandomizedSearchCV 진행 표시
        with tqdm(total=20 * 3, desc="  RandomizedSearchCV", unit="fold") as pbar:
            random_search.fit(X_train, y_train, groups=groups)
            pbar.update(20 * 3)
        hgb = random_search.best_estimator_
        print(f"  Best params: {random_search.best_params_}")
        print(f"  Best CV score (PR-AUC): {random_search.best_score_:.4f}")
    else:
        hgb = HistGradientBoostingClassifier(
            max_iter=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
        )
        with tqdm(total=1, desc="  Training", unit="model") as pbar:
            hgb.fit(X_train, y_train)
            pbar.update(1)
    
    models["hist_gradient_boosting"] = {
        "model": hgb,
        "scaler": None,
        "name": "HistGradientBoostingClassifier",
    }
    
    return models


def train_ensemble_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    base_models: dict,
) -> dict:
    """앙상블 모델 학습"""
    models = {}
    
    # Base 모델 준비 (scaled 버전)
    scaler = StandardScaler()
    with tqdm(total=1, desc="  Scaling features", unit="step") as pbar:
        X_train_scaled = scaler.fit_transform(X_train)
        pbar.update(1)
    
    # LR은 scaled 데이터 필요, HGB는 원본 데이터 사용
    lr_scaled = LogisticRegression(
        class_weight="balanced", max_iter=1000, random_state=42
    )
    with tqdm(total=1, desc="  Training LR", unit="model") as pbar:
        lr_scaled.fit(X_train_scaled, y_train)
        pbar.update(1)
    
    hgb = HistGradientBoostingClassifier(
        max_iter=100, learning_rate=0.1, max_depth=5, random_state=42
    )
    with tqdm(total=1, desc="  Training HGB", unit="model") as pbar:
        hgb.fit(X_train, y_train)
        pbar.update(1)
    
    # 1. Voting Classifier (Soft)
    # Voting은 원본 데이터를 사용하므로, LR을 Pipeline으로 래핑
    print("\nTraining VotingClassifier (soft)...")
    lr_pipeline = Pipeline([("scaler", scaler), ("lr", lr_scaled)])
    voting_soft = VotingClassifier(
        estimators=[
            ("lr", lr_pipeline),
            ("hgb", hgb),
        ],
        voting="soft",
    )
    with tqdm(total=1, desc="  Training Voting", unit="model") as pbar:
        voting_soft.fit(X_train, y_train)
        pbar.update(1)
    models["voting_soft"] = {
        "model": voting_soft,
        "scaler": None,  # Voting 내부에서 처리
        "name": "VotingClassifier (soft)",
    }
    
    # 2. Stacking Classifier
    print("Training StackingClassifier...")
    stacking = StackingClassifier(
        estimators=[
            ("lr", lr_pipeline),
            ("hgb", hgb),
        ],
        final_estimator=LogisticRegression(class_weight="balanced", random_state=42),
        cv=3,
        n_jobs=-1,
    )
    with tqdm(total=3, desc="  Stacking CV", unit="fold") as pbar:
        stacking.fit(X_train, y_train)
        pbar.update(3)
    models["stacking"] = {
        "model": stacking,
        "scaler": None,  # Stacking 내부에서 처리
        "name": "StackingClassifier",
    }
    
    return models


def evaluate_model(
    model_dict: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    val_games: list = None,
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
    train_roc_auc = roc_auc_score(y_train, y_train_pred_proba)
    val_roc_auc = roc_auc_score(y_val, y_val_pred_proba)
    
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
    
    # Precision@K 계산 (K=10, 20)
    sorted_indices = np.argsort(y_val_pred_proba)[::-1]
    precision_at_10 = float(y_val[sorted_indices[:10]].sum() / 10) if len(y_val) >= 10 else 0.0
    precision_at_20 = float(y_val[sorted_indices[:20]].sum() / 20) if len(y_val) >= 20 else 0.0
    
    # 경기당 알림 수 계산 (val_games가 제공된 경우)
    alerts_per_game_at_best = None
    if val_games is not None and len(val_games) > 0:
        total_alerts = y_val_pred_f1.sum()
        alerts_per_game_at_best = float(total_alerts / len(val_games))
    
    # Threshold sweep (0.1 ~ 0.9, 0.05 간격)
    threshold_sweep = []
    thresholds = np.arange(0.1, 0.95, 0.05)
    for thresh in tqdm(thresholds, desc="  Threshold sweep", unit="threshold"):
        y_pred = (y_val_pred_proba >= thresh).astype(int)
        if y_pred.sum() > 0:  # 최소 1개 이상 예측이 있을 때만
            sweep_metrics = {
                "threshold": float(thresh),
                "precision": float(precision_score(y_val, y_pred, zero_division=0)),
                "recall": float(recall_score(y_val, y_pred, zero_division=0)),
                "f1": float(f1_score(y_val, y_pred, zero_division=0)),
            }
            if val_games is not None and len(val_games) > 0:
                sweep_metrics["alerts_per_game"] = float(y_pred.sum() / len(val_games))
            threshold_sweep.append(sweep_metrics)
    
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
        "precision_at_10": precision_at_10,
        "precision_at_20": precision_at_20,
        "threshold_sweep": threshold_sweep,
    }
    
    if alerts_per_game_at_best is not None:
        metrics["alerts_per_game_at_best_threshold"] = alerts_per_game_at_best
    
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
        choices=[
            "logistic_regression",
            "hist_gradient_boosting",
            "voting_soft",
            "stacking",
        ],
        default="hist_gradient_boosting",
        help="사용할 모델",
    )
    parser.add_argument(
        "--tune-hyperparams",
        action="store_true",
        help="하이퍼파라미터 튜닝 수행 (GridSearchCV/RandomizedSearchCV)",
    )
    parser.add_argument(
        "--include-ensemble",
        action="store_true",
        help="앙상블 모델도 학습 및 평가",
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
    
    # 그룹 정보 (하이퍼파라미터 튜닝용)
    train_train_groups = train_train_df["game_id"].values if args.tune_hyperparams else None
    
    # 모델 학습
    models = train_models(
        X_train_train,
        y_train_train,
        groups=train_train_groups,
        tune_hyperparams=args.tune_hyperparams,
    )
    
    # 앙상블 모델 학습 (옵션)
    if args.include_ensemble:
        print("\n" + "=" * 60)
        print("Training ensemble models...")
        print("=" * 60)
        # Base 모델을 앙상블용으로 준비
        base_models_for_ensemble = {
            "logistic_regression": models["logistic_regression"],
            "hist_gradient_boosting": models["hist_gradient_boosting"],
        }
        ensemble_models = train_ensemble_models(
            X_train_train, y_train_train, base_models_for_ensemble
        )
        models.update(ensemble_models)
    
    # 모델 평가 및 선택 (PR-AUC 우선)
    print(f"\nEvaluating models (PR-AUC priority)...")
    best_model_name = None
    best_val_pr_auc = -1
    all_metrics = {}
    
    for model_name, model_dict in tqdm(models.items(), desc="Evaluating models", unit="model"):
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
        with tqdm(total=2, desc="  Scaling & Training", unit="step") as pbar:
            X_train_scaled = scaler.fit_transform(X_train)
            pbar.update(1)
            best_model_dict["model"].fit(X_train_scaled, y_train)
            pbar.update(1)
        best_model_dict["scaler"] = scaler
    else:
        with tqdm(total=1, desc="  Training", unit="model") as pbar:
            best_model_dict["model"].fit(X_train, y_train)
            pbar.update(1)
    
    # Test 평가
    test_metrics, test_f1_threshold, test_precision_threshold = evaluate_model(
        best_model_dict,
        X_train,
        y_train,
        X_test,
        y_test,
        val_games=test_games,
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
    print(f"  Test Precision@10: {test_metrics['precision_at_10']:.4f}")
    print(f"  Test Precision@20: {test_metrics['precision_at_20']:.4f}")
    if 'alerts_per_game_at_best_threshold' in test_metrics:
        print(f"  Test Alerts per game (F1 최대 threshold): {test_metrics['alerts_per_game_at_best_threshold']:.2f}")
    
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
    
    # 메트릭 저장 (운영 지표 포함)
    metrics_path = artifacts_dir / "will_have_shot_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "best_model": best_model_name,
                "all_models": all_metrics,
                "test_metrics": test_metrics,
                "positive_ratio": float(y_test.mean()),
                # 운영 지표 (발표용)
                "operational_metrics": {
                    "threshold_sweep": test_metrics.get("threshold_sweep", []),
                    "precision_at_10": test_metrics.get("precision_at_10", 0.0),
                    "precision_at_20": test_metrics.get("precision_at_20", 0.0),
                    "alerts_per_game_at_best_threshold": test_metrics.get("alerts_per_game_at_best_threshold"),
                },
            },
            f,
            indent=2,
        )
    print(f"Saved metrics to: {metrics_path}")
    
    print("\nTraining complete!")


if __name__ == "__main__":
    from sklearn.metrics import recall_score  # noqa: F401
    
    main()

