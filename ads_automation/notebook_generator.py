import re
from typing import Optional, List, Tuple
import pandas as pd

PREMIER_CATALOG = "rhealth_premier_phd.bronze_native_premier_phd"
CELL_SEP = "\n-- COMMAND ----------\n"
NOTEBOOK_HEADER = "-- Databricks notebook source"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_temp_table_name(condition: str, coding_system: str) -> str:
    c = re.sub(r"[^a-z0-9]+", "_", condition.lower()).strip("_")
    s = re.sub(r"[^a-z0-9]+", "_", coding_system.lower()).strip("_")
    return f"tmp__{c}__{s}"


def _step_table_name(n: int, description: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")[:35].rstrip("_")
    return f"step{n}_{clean}"


def _md_cell(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join(f"-- MAGIC {ln}" if ln.strip() else "-- MAGIC " for ln in lines)


# ─────────────────────────────────────────────────────────────────────────────
# Code-list cells
# ─────────────────────────────────────────────────────────────────────────────

def _codelist_sql(condition: str, coding_system: str, codes: List[str]) -> str:
    tbl = make_temp_table_name(condition, coding_system)
    vals = ",\n  ".join(f"('{c.strip()}')" for c in codes if c.strip())
    return (
        f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
        f"SELECT code FROM (\n"
        f"  VALUES\n"
        f"  {vals}\n"
        f") t(code);"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — index admission
# ─────────────────────────────────────────────────────────────────────────────

def _index_admission_sql(
    codelists_df: Optional[pd.DataFrame],
    step_table: str,
    premier_catalog: str,
) -> str:
    if codelists_df is None or codelists_df.empty:
        return (
            f"CREATE OR REPLACE TEMPORARY TABLE {step_table} AS\n"
            f"-- TODO: No code lists provided — add procedure/diagnosis code matching logic\n"
            f"SELECT\n"
            f"    pat_key, medrec_key, prov_id,\n"
            f"    admit_date AS index_date, discharge_date,\n"
            f"    age, gender, publish_type, i_o_ind, pat_type, ms_drg, los,\n"
            f"    pat_cost, pat_charges, pat_fix_cost, pat_var_cost, disc_status,\n"
            f"    CAST(NULL AS STRING) AS surgery_category\n"
            f"FROM {premier_catalog}.pat\n"
            f"WHERE 1=1  -- TODO: Add study window filter (e.g. admit_date BETWEEN ... AND ...)\n"
            f"LIMIT 0;"
        )

    icd_proc = []   # (condition, coding_system, tmp_tbl, version)
    icd_diag = []
    cpt_list = []
    drg_list = []

    for _, row in codelists_df.drop_duplicates(["condition", "coding_system"]).iterrows():
        cond = row["condition"]
        sys  = row["coding_system"]
        tmp  = make_temp_table_name(cond, sys)
        norm = sys.upper().replace(" ", "-")

        if "PCS" in norm:
            icd_proc.append((cond, sys, tmp, 10 if "10" in norm else 9))
        elif "CM" in norm:
            icd_diag.append((cond, sys, tmp, 10 if "10" in norm else 9))
        elif "CPT" in norm or "HCPCS" in norm:
            cpt_list.append((cond, sys, tmp))
        elif "DRG" in norm:
            drg_list.append((cond, sys, tmp))

    cte_blocks: List[str] = []
    union_parts: List[str] = []

    # ── ICD Procedure ─────────────────────────────────────────────────────────
    if icd_proc:
        joins = "\n".join(
            f"    LEFT JOIN {tmp} a{i} ON ip.icd_code = a{i}.code"
            for i, (c, s, tmp, v) in enumerate(icd_proc)
        )
        cases = "\n".join(
            f"            WHEN a{i}.code IS NOT NULL THEN '{c}'"
            for i, (c, s, tmp, v) in enumerate(icd_proc)
        )
        coalesce = ", ".join(f"a{i}.code" for i in range(len(icd_proc)))
        vers = list(dict.fromkeys(v for _, _, _, v in icd_proc))
        ver_clause = (
            f"ip.icd_version = {vers[0]}"
            if len(vers) == 1
            else f"ip.icd_version IN ({', '.join(str(v) for v in vers)})"
        )
        cte_blocks.append(
            f"icd_proc_match AS (\n"
            f"    SELECT ip.pat_key,\n"
            f"        CASE\n"
            f"{cases}\n"
            f"        END AS surgery_category\n"
            f"    FROM {premier_catalog}.paticd_proc ip\n"
            f"{joins}\n"
            f"    WHERE {ver_clause}\n"
            f"      AND ip.icd_pri_sec = 'P'\n"
            f"      AND COALESCE({coalesce}) IS NOT NULL\n"
            f")"
        )
        union_parts.append("    SELECT pat_key, surgery_category FROM icd_proc_match")

    # ── ICD Diagnosis ─────────────────────────────────────────────────────────
    if icd_diag:
        joins = "\n".join(
            f"    LEFT JOIN {tmp} b{i} ON id.icd_code = b{i}.code"
            for i, (c, s, tmp, v) in enumerate(icd_diag)
        )
        cases = "\n".join(
            f"            WHEN b{i}.code IS NOT NULL THEN '{c}'"
            for i, (c, s, tmp, v) in enumerate(icd_diag)
        )
        coalesce = ", ".join(f"b{i}.code" for i in range(len(icd_diag)))
        vers = list(dict.fromkeys(v for _, _, _, v in icd_diag))
        ver_clause = (
            f"id.icd_version = {vers[0]}"
            if len(vers) == 1
            else f"id.icd_version IN ({', '.join(str(v) for v in vers)})"
        )
        cte_blocks.append(
            f"icd_diag_match AS (\n"
            f"    SELECT id.pat_key,\n"
            f"        CASE\n"
            f"{cases}\n"
            f"        END AS surgery_category\n"
            f"    FROM {premier_catalog}.paticd_diag id\n"
            f"{joins}\n"
            f"    WHERE {ver_clause}\n"
            f"      AND COALESCE({coalesce}) IS NOT NULL\n"
            f")"
        )
        union_parts.append("    SELECT pat_key, surgery_category FROM icd_diag_match")

    # ── CPT / HCPCS ───────────────────────────────────────────────────────────
    if cpt_list:
        selects = "\n    UNION\n".join(
            f"    SELECT DISTINCT cp.pat_key, '{c}' AS surgery_category\n"
            f"    FROM {premier_catalog}.patcpt cp\n"
            f"    INNER JOIN {tmp} cl{i} ON cp.cpt_code = cl{i}.code"
            for i, (c, s, tmp) in enumerate(cpt_list)
        )
        cte_blocks.append(f"cpt_match AS (\n{selects}\n)")
        union_parts.append("    SELECT pat_key, surgery_category FROM cpt_match")

    # ── DRG ───────────────────────────────────────────────────────────────────
    if drg_list:
        selects = "\n    UNION\n".join(
            f"    SELECT DISTINCT p2.pat_key, '{c}' AS surgery_category\n"
            f"    FROM {premier_catalog}.pat p2\n"
            f"    INNER JOIN {tmp} dl{i} ON p2.ms_drg = dl{i}.code"
            for i, (c, s, tmp) in enumerate(drg_list)
        )
        cte_blocks.append(f"drg_match AS (\n{selects}\n)")
        union_parts.append("    SELECT pat_key, surgery_category FROM drg_match")

    if not cte_blocks:
        return (
            f"CREATE OR REPLACE TEMPORARY TABLE {step_table} AS\n"
            f"-- TODO: Unrecognized coding systems — add matching logic\n"
            f"SELECT * FROM {premier_catalog}.pat WHERE 1=0;"
        )

    ctes = ",\n\n".join(cte_blocks)
    unions = "\n    UNION\n".join(union_parts)

    return (
        f"CREATE OR REPLACE TEMPORARY TABLE {step_table} AS\n\n"
        f"WITH\n\n"
        f"{ctes},\n\n"
        f"all_matches AS (\n"
        f"{unions}\n"
        f"),\n\n"
        f"ranked AS (\n"
        f"    SELECT\n"
        f"        p.pat_key, p.medrec_key, p.prov_id,\n"
        f"        p.admit_date AS index_date, p.discharge_date,\n"
        f"        p.age, p.gender, p.publish_type, p.i_o_ind,\n"
        f"        p.pat_type, p.ms_drg, p.los,\n"
        f"        p.pat_cost, p.pat_charges, p.pat_fix_cost, p.pat_var_cost,\n"
        f"        p.disc_status, m.surgery_category,\n"
        f"        ROW_NUMBER() OVER (\n"
        f"            PARTITION BY p.medrec_key, m.surgery_category\n"
        f"            ORDER BY p.admit_date ASC, p.pat_key ASC\n"
        f"        ) AS rn\n"
        f"    FROM {premier_catalog}.pat p\n"
        f"    INNER JOIN all_matches m ON p.pat_key = m.pat_key\n"
        f"    -- TODO: Add study window filter: WHERE p.admit_date BETWEEN ... AND ...\n"
        f")\n\n"
        f"SELECT\n"
        f"    pat_key, medrec_key, prov_id, index_date, discharge_date,\n"
        f"    age, gender, publish_type, i_o_ind, pat_type, ms_drg, los,\n"
        f"    pat_cost, pat_charges, pat_fix_cost, pat_var_cost,\n"
        f"    disc_status, surgery_category\n"
        f"FROM ranked\n"
        f"WHERE rn = 1;"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Steps 2+ — sequential filters
# ─────────────────────────────────────────────────────────────────────────────

def _filter_step_sql(
    step_num: int,
    description: str,
    step_type: str,
    prev_table: str,
    premier_catalog: str,
) -> Tuple[str, str]:
    """Returns (step_table_name, sql_string)."""
    tbl = _step_table_name(step_num, description)
    d = description.lower()

    # ── Age ──────────────────────────────────────────────────────────────────
    if "age" in d:
        m = re.search(r"(\d+)", d)
        thresh = int(m.group(1)) if m else 18
        op = ">=" if step_type == "inclusion" else "<"
        return tbl, (
            f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
            f"SELECT * FROM {prev_table}\n"
            f"WHERE age {op} {thresh};"
        )

    # ── Known gender ─────────────────────────────────────────────────────────
    if "gender" in d or "sex" in d:
        if step_type == "inclusion":
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE gender IN ('M', 'F');"
            )
        else:
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE gender NOT IN ('M', 'F');"
            )

    # ── Hospital 90-day data contribution ────────────────────────────────────
    if any(kw in d for kw in ["90", "hospital contribution", "data contribution", "enrollment"]):
        if step_type == "inclusion":
            sql = (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n\n"
                f"WITH hospital_last_data AS (\n"
                f"    SELECT prov_id, MAX(ip_max_dx_date) AS max_data_date\n"
                f"    FROM {premier_catalog}.prov_enrollment\n"
                f"    GROUP BY prov_id\n"
                f")\n\n"
                f"SELECT s.*\n"
                f"FROM {prev_table} s\n"
                f"INNER JOIN hospital_last_data h ON s.prov_id = h.prov_id\n"
                f"WHERE h.max_data_date >= DATE_ADD(s.discharge_date, 90);"
            )
        else:
            sql = (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n\n"
                f"WITH hospital_last_data AS (\n"
                f"    SELECT prov_id, MAX(ip_max_dx_date) AS max_data_date\n"
                f"    FROM {premier_catalog}.prov_enrollment\n"
                f"    GROUP BY prov_id\n"
                f")\n\n"
                f"SELECT s.*\n"
                f"FROM {prev_table} s\n"
                f"LEFT JOIN hospital_last_data h ON s.prov_id = h.prov_id\n"
                f"WHERE h.max_data_date < DATE_ADD(s.discharge_date, 90)\n"
                f"   OR h.prov_id IS NULL;"
            )
        return tbl, sql

    # ── Publish type / Comparative Valid ─────────────────────────────────────
    if any(kw in d for kw in ["publish", "comparative valid", " cv"]):
        if step_type == "inclusion":
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE publish_type = 'CV';"
            )
        else:
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE publish_type <> 'CV';"
            )

    # ── Inpatient ─────────────────────────────────────────────────────────────
    if "inpatient" in d:
        if step_type == "inclusion":
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE i_o_ind = 'I';"
            )
        else:
            return tbl, (
                f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
                f"SELECT * FROM {prev_table}\n"
                f"WHERE i_o_ind <> 'I';"
            )

    # ── Cost > 0 ──────────────────────────────────────────────────────────────
    if "cost" in d:
        return tbl, (
            f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
            f"SELECT * FROM {prev_table}\n"
            f"WHERE pat_cost > 0\n"
            f"  AND pat_fix_cost > 0\n"
            f"  AND pat_var_cost > 0;"
        )

    # ── Null / complete data ──────────────────────────────────────────────────
    if any(kw in d for kw in ["null", "missing", "complete", "not null"]):
        return tbl, (
            f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
            f"SELECT * FROM {prev_table}\n"
            f"WHERE pat_key IS NOT NULL\n"
            f"  AND medrec_key IS NOT NULL\n"
            f"  AND index_date IS NOT NULL\n"
            f"  AND surgery_category IS NOT NULL;"
        )

    # ── LOS ───────────────────────────────────────────────────────────────────
    if "los" in d or "length of stay" in d:
        m = re.search(r"(\d+)", d)
        thresh = int(m.group(1)) if m else 1
        op = ">=" if step_type == "inclusion" else "<"
        return tbl, (
            f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
            f"SELECT * FROM {prev_table}\n"
            f"WHERE los {op} {thresh};"
        )

    # ── DRG filter ────────────────────────────────────────────────────────────
    if "drg" in d:
        return tbl, (
            f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
            f"SELECT * FROM {prev_table}\n"
            f"WHERE ms_drg IS NOT NULL;  -- TODO: Specify DRG range for: {description}"
        )

    # ── Fallback placeholder ─────────────────────────────────────────────────
    inc_note = "met" if step_type == "inclusion" else "NOT met"
    return tbl, (
        f"CREATE OR REPLACE TEMPORARY TABLE {tbl} AS\n"
        f"-- {step_type.upper()}: keep records where this criterion is {inc_note}\n"
        f"-- TODO: Implement filter for: {description}\n"
        f"SELECT * FROM {prev_table}\n"
        f"WHERE 1=1;  -- REPLACE with actual criterion"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Attrition waterfall
# ─────────────────────────────────────────────────────────────────────────────

def _waterfall_sql(step_records: List[Tuple[int, str, str, str]]) -> str:
    """step_records: list of (n, step_type, description, table_name)"""
    rows = []
    for n, stype, desc, tbl in step_records:
        label = stype.upper()[:3]
        safe_desc = desc.replace("'", "\\'")[:80]
        rows.append(
            f"    SELECT {n} AS n, '{label}' AS step_type, '{safe_desc}' AS step_description,\n"
            f"           COUNT(*) AS enc_after, COUNT(DISTINCT medrec_key) AS pts_after\n"
            f"    FROM {tbl}"
        )

    union_all = "\n    UNION ALL\n".join(rows)

    return (
        f"WITH counts AS (\n"
        f"{union_all}\n"
        f")\n\n"
        f"SELECT\n"
        f"    n AS step_num,\n"
        f"    step_type,\n"
        f"    step_description,\n"
        f"    enc_after,\n"
        f"    pts_after,\n"
        f"    LAG(enc_after) OVER (ORDER BY n) - enc_after AS enc_dropped,\n"
        f"    LAG(pts_after) OVER (ORDER BY n) - pts_after AS pts_dropped\n"
        f"FROM counts\n"
        f"ORDER BY n;"
    )


def _final_cohort_sql(last_table: str) -> str:
    return (
        f"SELECT\n"
        f"    surgery_category,\n"
        f"    COUNT(*)                   AS encounters,\n"
        f"    COUNT(DISTINCT medrec_key) AS patients,\n"
        f"    COUNT(DISTINCT prov_id)    AS hospitals,\n"
        f"    ROUND(AVG(los), 1)         AS avg_los,\n"
        f"    ROUND(AVG(age), 1)         AS avg_age,\n"
        f"    ROUND(AVG(pat_cost), 0)    AS avg_total_cost\n"
        f"FROM {last_table}\n"
        f"GROUP BY surgery_category\n"
        f"ORDER BY encounters DESC;"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_databricks_notebook(
    title: str,
    steps_df: pd.DataFrame,
    codelists_df: Optional[pd.DataFrame] = None,
    premier_catalog: str = PREMIER_CATALOG,
) -> str:
    """
    Generate a Databricks SOURCE-format SQL notebook.
    Returns the notebook content as a string.
    """
    cells: List[str] = []

    # ── Header ────────────────────────────────────────────────────────────────
    cells.append(_md_cell(
        f"%md\n"
        f"# {title}\n\n"
        f"**Attrition Cohort Notebook** | Generated by ADS Automation Platform  \n"
        f"Premier PHD · Catalog: `{premier_catalog}`\n\n"
        f"---\n\n"
        f"**Run All Cells** to execute the full attrition pipeline.  \n"
        f"Each cell creates a `TEMPORARY TABLE` scoped to this session."
    ))

    # ── Code list temp tables ─────────────────────────────────────────────────
    if codelists_df is not None and not codelists_df.empty:
        cells.append(_md_cell("%md\n## Code Lists\nTemporary tables for each condition × coding system."))

        for (cond, sys), grp in codelists_df.groupby(["condition", "coding_system"]):
            codes = grp["code"].dropna().astype(str).str.strip().tolist()
            if codes:
                cells.append(_codelist_sql(cond, sys, codes))

    # ── Attrition steps ───────────────────────────────────────────────────────
    cells.append(_md_cell("%md\n## Attrition Steps\nEach step filters from the prior step's cohort."))

    clean_steps = (
        steps_df
        .dropna(subset=["description"])
        .pipe(lambda d: d[d["description"].str.strip() != ""])
        .reset_index(drop=True)
    )

    step_records: List[Tuple[int, str, str, str]] = []
    prev_table = ""

    for idx, row in clean_steps.iterrows():
        n    = idx + 1
        stype = str(row["step_type"])
        desc  = str(row["description"]).strip()

        if n == 1:
            tbl = "step1_surgery_index"
            sql = _index_admission_sql(codelists_df, tbl, premier_catalog)
        else:
            tbl, sql = _filter_step_sql(n, desc, stype, prev_table, premier_catalog)

        cells.append(_md_cell(f"%md\n### Step {n} — {'INC' if stype == 'inclusion' else 'EXC'}: {desc}"))
        cells.append(sql)
        step_records.append((n, stype, desc, tbl))
        prev_table = tbl

    # ── Attrition waterfall ───────────────────────────────────────────────────
    if step_records:
        cells.append(_md_cell("%md\n## Attrition Waterfall\nEncounters and patients at each step, with drop counts."))
        cells.append(_waterfall_sql(step_records))

    # ── Final cohort summary ──────────────────────────────────────────────────
    if prev_table:
        cells.append(_md_cell("%md\n## Final Cohort Summary\nBy surgery category."))
        cells.append(_final_cohort_sql(prev_table))

    return NOTEBOOK_HEADER + "\n" + CELL_SEP.join(cells)
