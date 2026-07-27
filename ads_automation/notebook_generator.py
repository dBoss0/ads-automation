import re
from typing import Optional, List, Tuple, Dict
import pandas as pd

from ads_automation.model_serving import (
    generate_step_sql as _llm_step,
    generate_waterfall_sql as _llm_waterfall,
    generate_final_summary_sql as _llm_final,
    is_configured as _llm_ready,
)

PREMIER_CATALOG = "rhealth_premier_phd.bronze_native_premier_phd"
CELL_SEP        = "\n-- COMMAND ----------\n"
NOTEBOOK_HEADER = "-- Databricks notebook source"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_temp_table_name(condition: str, coding_system: str) -> str:
    c = re.sub(r"[^a-z0-9]+", "_", condition.lower()).strip("_")
    s = re.sub(r"[^a-z0-9]+", "_", coding_system.lower()).strip("_")
    return f"tmp__{c}__{s}"


# Short semantic table names — matches mock style (step2_age_18_plus etc.)
_SHORT_NAME_PATTERNS = [
    (["age", "18"],                       "age_18_plus"),
    (["age", "21"],                       "age_21_plus"),
    (["age", "65"],                       "age_65_plus"),
    (["90",  "hospital"],                 "hosp_90d"),
    (["90",  "contribut"],                "hosp_90d"),
    (["90",  "data"],                     "hosp_90d"),
    (["180", "hospital"],                 "hosp_180d"),
    (["180", "contribut"],                "hosp_180d"),
    (["gender"],                          "known_gender"),
    (["sex"],                             "known_gender"),
    (["publish", "cv"],                   "publish_cv"),
    (["comparative", "valid"],            "publish_cv"),
    (["publish", "type"],                 "publish_cv"),
    (["cost", "zero"],                    "positive_cost"),
    (["cost", "negative"],                "positive_cost"),
    (["zero", "negative"],                "positive_cost"),
    (["missing"],                         "complete_data"),
    (["null", "key"],                     "complete_data"),
    (["complete", "data"],                "complete_data"),
    (["inpatient"],                       "inpatient_only"),
    (["outpatient"],                      "outpatient_only"),
    (["los"],                             "los_filter"),
    (["length", "stay"],                  "los_filter"),
    (["drg"],                             "drg_filter"),
]

_STOP = {"the", "a", "an", "is", "are", "of", "for", "or", "and", "at", "as",
         "to", "in", "with", "by", "on", "per", "from", "be", "that", "this",
         "have", "has", "been", "such", "its", "it", "not", "do", "does"}


def _step_table_name(n: int, description: str) -> str:
    d = description.lower()
    for keywords, short_name in _SHORT_NAME_PATTERNS:
        if all(kw in d for kw in keywords):
            return f"step{n}_{short_name}"
    words = re.findall(r"[a-z]+", d)
    meaningful = [w for w in words if w not in _STOP and len(w) > 2][:3]
    slug = "_".join(meaningful)[:30].rstrip("_")
    return f"step{n}_{slug or 'filter'}"


def _md_cell(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join(f"-- MAGIC {ln}" if ln.strip() else "-- MAGIC " for ln in lines)


def _escape(s: str) -> str:
    return s.replace("'", "''")


def _extract_study_window(description: str) -> str:
    years = re.findall(r"\b(20\d{2})\b", description)
    if len(years) >= 2:
        return f"{years[0]}-01-01 to {years[-1]}-12-31"
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Code-list cells
# ─────────────────────────────────────────────────────────────────────────────

def _codelist_sql(condition: str, coding_system: str, rows: List[Tuple[str, str]]) -> str:
    tbl      = make_temp_table_name(condition, coding_system)
    has_desc = any(d.strip() for _, d in rows)

    if has_desc:
        vals   = ",\n  ".join(f"('{_escape(c)}', '{_escape(d)}')" for c, d in rows if c.strip())
        schema = "AS t(code, description)"
    else:
        vals   = ",\n  ".join(f"('{_escape(c)}')" for c, _ in rows if c.strip())
        schema = "AS t(code)"

    return (
        f"-- Condition: {condition} | System: {coding_system}\n"
        f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
        f"SELECT * FROM VALUES\n"
        f"  {vals}\n"
        f"{schema};\n\n"
        f"SELECT COUNT(*) AS codes FROM {tbl};"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Build structured code-table mapping for Step 1
# ─────────────────────────────────────────────────────────────────────────────

def _build_code_table_mapping(codelists_df: pd.DataFrame) -> Dict:
    """
    Returns {condition: {sys_type: [table_name, ...]}} where
    sys_type is one of: icd_proc, icd_diag, cpt, drg
    """
    mapping: Dict = {}
    for (cond, sys), _ in codelists_df.groupby(["condition", "coding_system"]):
        tbl  = make_temp_table_name(str(cond), str(sys))
        norm = str(sys).upper().replace(" ", "-")
        if "PCS" in norm or ("ICD" in norm and "CM" not in norm):
            t = "icd_proc"
        elif "CM" in norm:
            t = "icd_diag"
        elif "CPT" in norm or "HCPCS" in norm:
            t = "cpt"
        elif "DRG" in norm:
            t = "drg"
        else:
            t = "other"
        mapping.setdefault(str(cond), {}).setdefault(t, []).append(tbl)
    return mapping


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_databricks_notebook(
    title: str,
    steps_df: pd.DataFrame,
    codelists_df: Optional[pd.DataFrame] = None,
    premier_catalog: str = PREMIER_CATALOG,
    token: str = "",
    study_window: str = "",
) -> str:
    cells: List[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    cells.append(_md_cell(
        f"%md\n"
        f"# {title}\n\n"
        f"**Attrition Cohort Notebook** | J&J MedTech ADS Automation Platform  \n"
        f"Data Source: Premier PHD (PINC AI™ Healthcare Database)  \n"
        f"Catalog: `{premier_catalog}`\n\n"
        f"---\n\n"
        f"**Run All Cells** to execute the full attrition pipeline.  \n"
        f"Each cell creates a `TEMPORARY TABLE` — session-scoped, auto-dropped when session ends.  \n"
        f"Each step reads from the previous step's temp table — counts can be checked at any step."
    ))

    # ── Code list temp tables ─────────────────────────────────────────────────
    if codelists_df is not None and not codelists_df.empty:
        cells.append(_md_cell(
            "%md\n---\n"
            "## Code List Temp Tables\n"
            "One table per condition × coding system. Each cell ends with a row count."
        ))
        for (cond, sys), grp in codelists_df.groupby(["condition", "coding_system"]):
            desc_col = "description" if "description" in grp.columns else None
            pairs = list(zip(
                grp["code"].fillna("").astype(str).str.strip(),
                grp[desc_col].fillna("").astype(str).str.strip() if desc_col else [""] * len(grp),
            ))
            pairs = [(c, d) for c, d in pairs if c]
            if pairs:
                cells.append(_codelist_sql(str(cond), str(sys), pairs))

    # ── Build code table mapping for Step 1 ──────────────────────────────────
    code_table_mapping: Dict = {}
    code_table_names:   List = []
    if codelists_df is not None and not codelists_df.empty:
        code_table_mapping = _build_code_table_mapping(codelists_df)
        for cond_map in code_table_mapping.values():
            for tbls in cond_map.values():
                code_table_names.extend(tbls)

    # ── Attrition steps ───────────────────────────────────────────────────────
    cells.append(_md_cell(
        "%md\n---\n"
        "## Attrition Steps\n"
        "Each step filters from the prior step's cohort. Each cell ends with a count check."
    ))

    clean_steps = (
        steps_df
        .dropna(subset=["description"])
        .pipe(lambda d: d[d["description"].str.strip() != ""])
        .reset_index(drop=True)
    )

    step_records: List[Tuple[int, str, str, str]] = []
    prev_table = ""
    use_llm    = _llm_ready() and bool(token)

    for idx, row in clean_steps.iterrows():
        n     = idx + 1
        stype = str(row["step_type"])
        desc  = str(row["description"]).strip()
        tbl   = "step1_surgery_index" if n == 1 else _step_table_name(n, desc)

        # Extract study window from Step 1 description if not provided
        win = study_window or (_extract_study_window(desc) if n == 1 else "")

        if use_llm:
            sql = _llm_step(
                step_num=n,
                step_type=stype,
                description=desc,
                prev_table=prev_table,
                target_table=tbl,
                token=token,
                code_table_mapping=code_table_mapping if n == 1 else None,
                code_table_names=code_table_names,
                study_window=win,
            )
        else:
            sql = (
                f"-- ════════════════════════════════════════════════════════════════════════════\n"
                f"-- STEP {n} ({'INCLUSION' if stype == 'inclusion' else 'EXCLUSION'}): {desc}\n"
                f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"-- TODO: Implement filter for: {desc}\n"
                f"SELECT * FROM {prev_table or premier_catalog + '.pat'}\n"
                f"WHERE 1=1;\n\n"
                f"SELECT COUNT(*) AS index_admissions, COUNT(DISTINCT medrec_key) AS unique_patients\n"
                f"FROM {tbl};"
            )

        cells.append(_md_cell(
            f"%md\n---\n"
            f"## Cell {n + (len(code_table_names) > 0)} "
            f"— STEP {n} ({'INC' if stype == 'inclusion' else 'EXC'}): {desc}"
        ))
        cells.append(sql)
        step_records.append((n, stype, desc, tbl))
        prev_table = tbl

    # ── Attrition waterfall ───────────────────────────────────────────────────
    # Always Python-generated: LLM cannot reliably produce this template and
    # tends to hallucinate a new Step 1 SQL instead.
    if step_records:
        cells.append(_md_cell(
            "%md\n---\n"
            "## Attrition Waterfall\n"
            "Encounters and patients retained at each step, with drop counts."
        ))
        cells.append(_fallback_waterfall(step_records))

    # ── Final cohort summary ──────────────────────────────────────────────────
    # Always Python-generated: fixed 14-column template, no LLM needed.
    if prev_table:
        cells.append(_md_cell(
            "%md\n---\n"
            "## Final Cohort Summary\n"
            "Demographics, utilization, and cost by surgery category."
        ))
        cells.append(_fallback_final(prev_table))

    return NOTEBOOK_HEADER + "\n" + CELL_SEP.join(cells)


# ─────────────────────────────────────────────────────────────────────────────
# Fallback (no token) — kept for local dev / offline mode
# ─────────────────────────────────────────────────────────────────────────────

def _fallback_waterfall(step_records):
    """
    Generates the attrition waterfall CTE.
    First row: expanded SELECT with named columns (matches mock notebook style).
    Subsequent rows: compact positional form.
    Exclusion steps get an 'EXCLUDE: ' prefix on the description.
    """
    rows = []
    for i, (n, stype, desc, tbl) in enumerate(step_records):
        is_exc    = str(stype).lower() != "inclusion"
        label     = "EXC" if is_exc else "INC"
        prefix    = "EXCLUDE: " if is_exc else ""
        safe_desc = _escape(f"{n}. {prefix}{str(desc)[:70]}")

        if i == 0:
            # First row: full named-column form
            rows.append(
                f"    SELECT {n} AS n, '{label}' AS type,\n"
                f"           '{safe_desc}' AS step,\n"
                f"           COUNT(*) AS enc, COUNT(DISTINCT medrec_key) AS pts\n"
                f"    FROM {tbl}"
            )
        else:
            # Subsequent rows: compact positional form
            rows.append(
                f"    SELECT {n}, '{label}', '{safe_desc}',\n"
                f"           COUNT(*), COUNT(DISTINCT medrec_key)\n"
                f"    FROM {tbl}"
            )

    union_all = "\n\n    UNION ALL\n".join(rows)
    return (
        f"-- ════════════════════════════════════════════════════════════════════════════\n"
        f"-- ATTRITION WATERFALL\n"
        f"-- enc_dropped / pts_dropped = difference from previous step\n"
        f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
        f"WITH counts AS (\n\n"
        f"{union_all}\n\n"
        f")\n\n"
        f"SELECT\n"
        f"    n                                        AS step_num,\n"
        f"    type                                     AS step_type,\n"
        f"    step                                     AS step_description,\n"
        f"    enc                                      AS enc_after,\n"
        f"    pts                                      AS pts_after,\n"
        f"    LAG(enc) OVER (ORDER BY n) - enc         AS enc_dropped,\n"
        f"    LAG(pts) OVER (ORDER BY n) - pts         AS pts_dropped\n"
        f"FROM counts\n"
        f"ORDER BY n;"
    )


def _fallback_final(last_table):
    return (
        f"-- ════════════════════════════════════════════════════════════════════════════\n"
        f"-- FINAL COHORT SUMMARY — demographics, utilization, cost by surgery category\n"
        f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
        f"SELECT\n"
        f"    surgery_category,\n"
        f"    COUNT(*)                                             AS index_admissions,\n"
        f"    COUNT(DISTINCT medrec_key)                           AS unique_patients,\n"
        f"    COUNT(DISTINCT prov_id)                              AS hospitals,\n"
        f"    ROUND(AVG(age),          1)                          AS mean_age,\n"
        f"    SUM(CASE WHEN gender  = 'F' THEN 1 ELSE 0 END)       AS female_n,\n"
        f"    SUM(CASE WHEN gender  = 'M' THEN 1 ELSE 0 END)       AS male_n,\n"
        f"    SUM(CASE WHEN i_o_ind = 'I' THEN 1 ELSE 0 END)       AS inpatient_n,\n"
        f"    SUM(CASE WHEN i_o_ind = 'O' THEN 1 ELSE 0 END)       AS outpatient_n,\n"
        f"    ROUND(AVG(los),          1)                          AS mean_los_days,\n"
        f"    ROUND(AVG(pat_cost),     0)                          AS mean_total_cost_usd,\n"
        f"    ROUND(AVG(pat_fix_cost), 0)                          AS mean_room_board_cost_usd,\n"
        f"    ROUND(AVG(pat_var_cost), 0)                          AS mean_variable_cost_usd,\n"
        f"    ROUND(AVG(pat_charges),  0)                          AS mean_billed_charges_usd\n"
        f"FROM {last_table}\n"
        f"GROUP BY surgery_category\n"
        f"ORDER BY surgery_category;"
    )
