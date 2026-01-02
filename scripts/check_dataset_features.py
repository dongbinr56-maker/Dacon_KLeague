#!/usr/bin/env python3
"""데이터셋 피처 확인 스크립트"""

import pandas as pd
from pathlib import Path

dataset_path = Path("artifacts/will_have_shot_dataset.parquet")

if not dataset_path.exists():
    print(f"데이터셋 파일이 없습니다: {dataset_path}")
    exit(1)

df = pd.read_parquet(dataset_path)
cols = list(df.columns)

print(f"전체 피처 수: {len(cols)}")
print(f"샘플 수: {len(df)}")

# 다층화 피처 확인 (past_1s_, past_5s_, past_10s_, past_20s_)
multilayer = [c for c in cols if any(f"past_{w}s_" in c for w in [1, 5, 10, 20])]
print(f"\n다층화 피처: {len(multilayer)}개")
if multilayer:
    print("예시:", sorted(multilayer)[:10])

# 상호작용 피처 확인
interaction = [c for c in cols if "interaction" in c or "density" in c or "penetration_depth" in c]
print(f"\n상호작용 피처: {len(interaction)}개")
if interaction:
    print("예시:", sorted(interaction))

# 최근 N개 이벤트 피처
recent = [c for c in cols if "recent_" in c]
print(f"\n최근 N개 이벤트 피처: {len(recent)}개")
if recent:
    print("예시:", sorted(recent)[:10])

# 전체 피처 목록 저장
with open("artifacts/dataset_features_list.txt", "w") as f:
    f.write("\n".join(sorted(cols)))

print(f"\n전체 피처 목록 저장: artifacts/dataset_features_list.txt")

