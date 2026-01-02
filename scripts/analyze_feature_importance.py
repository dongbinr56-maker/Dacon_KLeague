#!/usr/bin/env python3
"""
피처 중요도 분석 스크립트

학습된 모델에서 피처 중요도를 추출하고 분석합니다.
- LogisticRegression: coefficients 절댓값
- HistGradientBoostingClassifier: feature_importances_
- 상관관계 분석
- 중요도 기반 피처 선택
"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def load_model(model_path: str) -> dict:
    """모델 로드"""
    return joblib.load(model_path)


def extract_feature_importance(model_dict: dict, feature_columns: list) -> pd.DataFrame:
    """모델에서 피처 중요도 추출"""
    model = model_dict["model"]
    scaler = model_dict.get("scaler")
    
    # 모델 타입에 따라 중요도 추출
    if hasattr(model, "feature_importances_"):
        # Tree-based 모델 (HistGradientBoostingClassifier)
        importances = model.feature_importances_
        method = "feature_importances_"
    elif hasattr(model, "coef_"):
        # Linear 모델 (LogisticRegression)
        # coefficients의 절댓값 사용
        coef = model.coef_[0] if model.coef_.ndim > 1 else model.coef_
        importances = np.abs(coef)
        method = "coef_abs"
    elif hasattr(model, "named_estimators_"):
        # Ensemble 모델 (VotingClassifier, StackingClassifier)
        # 각 base estimator의 중요도를 평균
        importances_list = []
        for name, estimator in model.named_estimators_.items():
            # Pipeline인 경우 실제 estimator 추출
            if hasattr(estimator, "named_steps"):
                # Pipeline에서 마지막 step이 실제 모델
                actual_estimator = estimator.named_steps.get(list(estimator.named_steps.keys())[-1])
                if actual_estimator is None:
                    continue
            else:
                actual_estimator = estimator
            
            if hasattr(actual_estimator, "feature_importances_"):
                importances_list.append(actual_estimator.feature_importances_)
            elif hasattr(actual_estimator, "coef_"):
                coef = actual_estimator.coef_[0] if actual_estimator.coef_.ndim > 1 else actual_estimator.coef_
                importances_list.append(np.abs(coef))
        
        if importances_list:
            # 모든 중요도가 같은 길이인지 확인
            lengths = [len(imp) for imp in importances_list]
            if len(set(lengths)) == 1 and lengths[0] == len(feature_columns):
                importances = np.mean(importances_list, axis=0)
                method = "ensemble_avg"
            else:
                # 길이가 다르면 uniform 사용
                importances = np.ones(len(feature_columns)) / len(feature_columns)
                method = "uniform_fallback"
        else:
            # StackingClassifier의 final_estimator 사용
            if hasattr(model, "final_estimator_"):
                final_model = model.final_estimator_
                if hasattr(final_model, "coef_"):
                    coef = final_model.coef_[0] if final_model.coef_.ndim > 1 else final_model.coef_
                    importances = np.abs(coef)
                    method = "final_estimator_coef"
                else:
                    importances = np.ones(len(feature_columns)) / len(feature_columns)
                    method = "uniform"
            else:
                importances = np.ones(len(feature_columns)) / len(feature_columns)
                method = "uniform"
    else:
        # 알 수 없는 모델 타입
        importances = np.ones(len(feature_columns)) / len(feature_columns)
        method = "uniform"
    
    # 길이 확인 및 조정
    if len(importances) != len(feature_columns):
        print(f"Warning: Importance length ({len(importances)}) != feature columns length ({len(feature_columns)})")
        print(f"Using uniform importance as fallback")
        importances = np.ones(len(feature_columns)) / len(feature_columns)
        method = "uniform_fallback"
    
    # 정규화 (0-1 범위)
    if importances.sum() > 0:
        importances = importances / importances.sum()
    
    # DataFrame 생성
    df = pd.DataFrame({
        "feature": feature_columns,
        "importance": importances,
        "method": method,
    })
    
    # 중요도 내림차순 정렬
    df = df.sort_values("importance", ascending=False).reset_index(drop=True)
    
    return df


def analyze_feature_correlation(df: pd.DataFrame, feature_columns: list) -> pd.DataFrame:
    """피처 간 상관관계 분석"""
    # 상관관계 행렬 계산
    corr_matrix = df[feature_columns].corr().abs()
    
    # 상위 상관관계 쌍 추출 (중복 제거)
    corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            corr_pairs.append({
                "feature1": corr_matrix.columns[i],
                "feature2": corr_matrix.columns[j],
                "correlation": corr_matrix.iloc[i, j],
            })
    
    corr_df = pd.DataFrame(corr_pairs)
    corr_df = corr_df.sort_values("correlation", ascending=False).reset_index(drop=True)
    
    return corr_df


def select_features_by_importance(
    importance_df: pd.DataFrame,
    top_k: int = None,
    threshold: float = None,
    cumulative_ratio: float = None,
) -> list:
    """중요도 기반 피처 선택"""
    if top_k:
        selected = importance_df.head(top_k)["feature"].tolist()
    elif threshold:
        selected = importance_df[importance_df["importance"] >= threshold]["feature"].tolist()
    elif cumulative_ratio:
        importance_df["cumulative"] = importance_df["importance"].cumsum()
        selected = importance_df[importance_df["cumulative"] <= cumulative_ratio]["feature"].tolist()
    else:
        # 기본값: 상위 80% 누적 중요도
        importance_df["cumulative"] = importance_df["importance"].cumsum()
        selected = importance_df[importance_df["cumulative"] <= 0.8]["feature"].tolist()
    
    return selected


def main():
    parser = argparse.ArgumentParser(description="피처 중요도 분석")
    parser.add_argument(
        "--model-path",
        type=str,
        default="artifacts/will_have_shot_model.joblib",
        help="학습된 모델 파일 경로",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="artifacts/will_have_shot_dataset.parquet",
        help="데이터셋 파일 경로 (상관관계 분석용)",
    )
    parser.add_argument(
        "--feature-columns-path",
        type=str,
        default="artifacts/feature_columns.json",
        help="피처 컬럼 파일 경로",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="artifacts/feature_importance_analysis.json",
        help="분석 결과 출력 경로",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="상위 K개 피처 선택",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="중요도 임계값 (이상인 피처 선택)",
    )
    parser.add_argument(
        "--cumulative-ratio",
        type=float,
        default=0.8,
        help="누적 중요도 비율 (기본값: 0.8 = 80%%)",
    )
    args = parser.parse_args()
    
    # 파일 로드
    print("Loading model and data...")
    model_dict = load_model(args.model_path)
    feature_columns = json.load(open(args.feature_columns_path))
    
    # 피처 중요도 추출
    print("Extracting feature importance...")
    importance_df = extract_feature_importance(model_dict, feature_columns)
    
    print(f"\nTop 20 features by importance:")
    print(importance_df.head(20).to_string(index=False))
    
    # 피처 선택
    selected_features = select_features_by_importance(
        importance_df,
        top_k=args.top_k,
        threshold=args.threshold,
        cumulative_ratio=args.cumulative_ratio,
    )
    
    print(f"\nSelected {len(selected_features)} features (out of {len(feature_columns)})")
    print(f"Selection criteria: top_k={args.top_k}, threshold={args.threshold}, cumulative_ratio={args.cumulative_ratio}")
    
    # 상관관계 분석 (옵션)
    correlation_df = None
    if args.dataset_path and Path(args.dataset_path).exists():
        print("\nAnalyzing feature correlations...")
        df = pd.read_parquet(args.dataset_path)
        correlation_df = analyze_feature_correlation(df, feature_columns)
        
        print(f"\nTop 20 feature pairs by correlation:")
        print(correlation_df.head(20).to_string(index=False))
    
    # 결과 저장
    result = {
        "total_features": len(feature_columns),
        "selected_features": selected_features,
        "selection_criteria": {
            "top_k": args.top_k,
            "threshold": args.threshold,
            "cumulative_ratio": args.cumulative_ratio,
        },
        "importance_ranking": importance_df.to_dict("records"),
        "top_20_features": importance_df.head(20).to_dict("records"),
    }
    
    if correlation_df is not None:
        result["correlation_analysis"] = {
            "top_20_pairs": correlation_df.head(20).to_dict("records"),
            "high_correlation_pairs": correlation_df[correlation_df["correlation"] > 0.8].to_dict("records"),
        }
    
    # JSON 저장
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {output_path}")
    
    # 선택된 피처 목록 저장
    selected_output_path = output_path.parent / "selected_features.json"
    with open(selected_output_path, "w") as f:
        json.dump(selected_features, f, indent=2)
    
    print(f"Selected features saved to: {selected_output_path}")


if __name__ == "__main__":
    main()

