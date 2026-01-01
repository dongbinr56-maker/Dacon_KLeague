"""
will_have_shot 예측기 모듈

서버 시작 시 모델 로드, 예측 수행
모델 파일이 없으면 비활성 상태로 동작 (예외 발생 안 함)
"""

import os
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np

from app.core.config import get_settings


class WillHaveShotPredictor:
    """10초 내 슈팅 발생 예측기"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.threshold = 0.5
        self.is_active = False
        self._load_model()
    
    def _load_model(self) -> None:
        """모델 로드 (실패해도 예외 발생 안 함)"""
        try:
            settings = get_settings()
            # 모델 경로: artifacts/will_have_shot_model.joblib 또는 ENV로 지정
            model_path = os.getenv(
                "WILL_HAVE_SHOT_MODEL_PATH",
                str(Path(__file__).resolve().parents[4] / "artifacts" / "will_have_shot_model.joblib")
            )
            
            if not os.path.exists(model_path):
                print(f"WillHaveShotPredictor: Model file not found at {model_path}, predictor disabled")
                return
            
            model_data = joblib.load(model_path)
            self.model = model_data["model"]
            self.scaler = model_data.get("scaler")
            self.feature_columns = model_data.get("feature_columns", [])
            # Precision 우선 threshold 사용
            self.threshold = model_data.get("threshold_precision", model_data.get("threshold_f1", 0.5))
            self.is_active = True
            print(f"WillHaveShotPredictor: Model loaded from {model_path}, threshold={self.threshold:.4f}")
        except Exception as e:
            print(f"WillHaveShotPredictor: Failed to load model: {e}, predictor disabled")
            self.is_active = False
    
    def predict_proba(self, features: Dict[str, float]) -> Optional[float]:
        """
        예측 확률 반환
        
        Args:
            features: 피처 딕셔너리
            
        Returns:
            확률 (0~1) 또는 None (모델 비활성 시)
        """
        if not self.is_active or self.model is None:
            return None
        
        try:
            # 피처 벡터 생성 (순서 중요)
            feature_vector = np.array([
                features.get(col, 0.0) for col in self.feature_columns
            ]).reshape(1, -1)
            
            # 결측치 처리
            feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=0.0, neginf=0.0)
            
            # 표준화
            if self.scaler:
                feature_vector = self.scaler.transform(feature_vector)
            
            # 예측
            proba = self.model.predict_proba(feature_vector)[0, 1]
            return float(proba)
        except Exception as e:
            print(f"WillHaveShotPredictor: Prediction error: {e}")
            return None
    
    def should_alert(self, proba: Optional[float]) -> bool:
        """
        Alert 발행 여부 결정
        
        Args:
            proba: 예측 확률
            
        Returns:
            True if proba >= threshold
        """
        if proba is None:
            return False
        return proba >= self.threshold


# 싱글톤 인스턴스
_predictor: Optional[WillHaveShotPredictor] = None


def get_will_have_shot_predictor() -> WillHaveShotPredictor:
    """예측기 인스턴스 반환 (싱글톤)"""
    global _predictor
    if _predictor is None:
        _predictor = WillHaveShotPredictor()
    return _predictor

