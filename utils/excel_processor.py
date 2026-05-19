"""
Excel processing utilities
"""
from __future__ import annotations

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


# ── 점수 기반 기준 컬럼 자동 추정 ──────────────────────────────────

_KEY_NAME_HINTS = ("항목", "명칭", "이름", "분류", "품목", "코드", "명")


def infer_key_column(df: pd.DataFrame) -> str:
    """컬럼명·커버리지·유니크도·타입 점수로 기준 컬럼을 자동 추정."""
    cols = [str(c) for c in df.columns]
    n = max(len(df), 1)
    best, best_score = cols[0], float("-inf")
    for c in cols:
        s = df[c]
        non_null = int(s.notna().sum())
        if non_null == 0:
            continue
        name_bonus = 2.0 if any(h in c for h in _KEY_NAME_HINTS) else 0.0
        numeric_penalty = 1.0 if pd.api.types.is_numeric_dtype(s) else 0.0
        coverage = non_null / n
        uniqueness = s.nunique(dropna=True) / n
        score = name_bonus + coverage + uniqueness - numeric_penalty
        if score > best_score:
            best_score, best = score, c
    return best


# ── LLM용 파일 구조 텍스트 직렬화 ────────────────────────────────

def describe_df(df: pd.DataFrame) -> str:
    """DataFrame 구조를 LLM에 넘기기 좋은 텍스트로 직렬화."""
    lines = [f"행 수: {len(df)}, 열 수: {len(df.columns)}", "컬럼:"]
    for col in df.columns:
        dtype = "숫자" if pd.api.types.is_numeric_dtype(df[col]) else "텍스트"
        sample = df[col].dropna().head(3).tolist()
        lines.append(f"  - {col} ({dtype}): {sample}")
    return "\n".join(lines)


# ── 기준 컬럼 기반 다중 파일 통합 ────────────────────────────────

def merge_by_key(
    named_dfs: list[tuple[str, pd.DataFrame]],
    key_col: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    여러 DataFrame을 기준 컬럼 값이 같은 행끼리 통합.
    - 숫자 컬럼: 파일별 평균
    - 텍스트 컬럼: 모두 같으면 유지, 다르면 '값 상이'
    - 누락: 'N/A'
    Returns: {"통합결과": df, "파일별비교": df, "처리로그": df}
    """
    named_dfs = [(str(n), d.copy()) for n, d in named_dfs if d is not None and not d.empty]
    if not named_dfs:
        empty = pd.DataFrame()
        return {"통합결과": empty, "파일별비교": empty.copy(), "처리로그": empty.copy()}

    for i, (name, df) in enumerate(named_dfs):
        df.columns = [str(c) for c in df.columns]
        named_dfs[i] = (name, df)

    kc = key_col if key_col else infer_key_column(named_dfs[0][1])

    # 전체 키 값 수집 (순서 유지)
    all_keys: list[str] = []
    seen_keys: set[str] = set()
    for _, df in named_dfs:
        if kc not in df.columns:
            continue
        for v in df[kc].dropna():
            sv = str(v).strip()
            if sv and sv not in seen_keys:
                seen_keys.add(sv)
                all_keys.append(sv)

    # 키 제외 전체 컬럼 (순서 유지)
    all_cols: list[str] = []
    seen_cols: set[str] = set()
    for _, df in named_dfs:
        for c in df.columns:
            if c != kc and c not in seen_cols:
                seen_cols.add(c)
                all_cols.append(c)

    file_names = [n for n, _ in named_dfs]
    result_rows: list[dict] = []
    comparison_rows: list[dict] = []
    log_rows: list[dict] = [
        {"구분": "기준 컬럼", "항목": kc, "내용": "사용자 지정" if key_col else "자동 추정"}
    ]

    for key_val in all_keys:
        result_row: dict = {kc: key_val}
        comp_row: dict = {kc: key_val}

        # 파일별 해당 키 행 수집
        file_data: dict[str, dict] = {}
        for fname, df in named_dfs:
            if kc not in df.columns:
                continue
            match = df[df[kc].astype(str).str.strip() == key_val]
            if match.empty:
                file_data[fname] = {}
                log_rows.append({"구분": "누락", "항목": key_val, "내용": f"{fname}: 없음"})
            else:
                file_data[fname] = match.iloc[0].to_dict()

        for col in all_cols:
            values_by_file: dict[str, object] = {}
            for fname in file_names:
                v = file_data.get(fname, {}).get(col)
                if v is not None and pd.notna(v):
                    values_by_file[fname] = v
                comp_row[f"{col}_{Path(fname).stem[:8]}"] = v if (v is not None and pd.notna(v)) else "N/A"

            if not values_by_file:
                result_row[col] = "N/A"
                continue

            numeric_vals: list[float] = []
            for v in values_by_file.values():
                try:
                    numeric_vals.append(float(v))  # type: ignore[arg-type]
                except (ValueError, TypeError):
                    pass

            if len(numeric_vals) == len(values_by_file):
                result_row[col] = round(sum(numeric_vals) / len(numeric_vals), 2)
            else:
                str_vals = [str(v).strip() for v in values_by_file.values()]
                if len(set(str_vals)) == 1:
                    result_row[col] = str_vals[0]
                else:
                    result_row[col] = "값 상이"
                    log_rows.append({"구분": "불일치", "항목": key_val, "내용": f"{col}: {str_vals}"})

        result_rows.append(result_row)
        comparison_rows.append(comp_row)

    result_df = pd.DataFrame(result_rows) if result_rows else pd.DataFrame()
    comparison_df = pd.DataFrame(comparison_rows) if comparison_rows else pd.DataFrame()
    log_df = pd.DataFrame(log_rows) if log_rows else pd.DataFrame()

    return {"통합결과": result_df, "파일별비교": comparison_df, "처리로그": log_df}
