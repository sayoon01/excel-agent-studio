"""
Excel processing utilities
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional


def read_file(filepath):
    fp = Path(filepath)
    return pd.read_csv(fp) if fp.suffix.lower() == ".csv" else pd.read_excel(fp)


def find_common_columns(dfs):
    if not dfs:
        return []
    common = set(dfs[0].columns)
    for df in dfs[1:]:
        common &= set(df.columns)
    return sorted(common)


def merge(dfs, strategy="mean", group_cols=None):
    if len(dfs) <= 1:
        return dfs[0].copy() if dfs else pd.DataFrame()
    combined = pd.concat(dfs, ignore_index=True)
    numeric = combined.select_dtypes(include="number").columns.tolist()
    if group_cols is None:
        group_cols = [c for c in combined.columns if c not in numeric]
    if not group_cols:
        return combined[numeric].agg(strategy).to_frame().T
    agg = {c: strategy for c in numeric if c not in group_cols}
    return combined.groupby(group_cols, as_index=False).agg(agg) if agg else combined.drop_duplicates(subset=group_cols)


def summary(dfs, names):
    return pd.DataFrame([{
        "file": n, "rows": len(d), "cols": len(d.columns),
        "columns": ", ".join(d.columns), "nulls": int(d.isnull().sum().sum())
    } for n, d in zip(names, dfs)])
