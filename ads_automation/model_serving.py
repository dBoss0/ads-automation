"""
Databricks Model Serving — Claude Opus 5 SQL generation.
Endpoint: databricks-claude-opus-5 on dbc-db3d8a4e-f2cf.cloud.databricks.com

Catalog : rhealth_premier_phd
Schema  : bronze_native_premier_phd
NOTE    : PHD doc calls it PATDEMO — actual Databricks table is `pat`
"""

import requests
from typing import Dict, List, Optional

CLAUDE_ENDPOINT_URL = (
    "https://dbc-db3d8a4e-f2cf.cloud.databricks.com"
    "/serving-endpoints/databricks-claude-opus-5/invocations"
)

PREMIER_CATALOG = "rhealth_premier_phd.bronze_native_premier_phd"

# ─────────────────────────────────────────────────────────────────────────────
# Style reference — injected as system prompt for every call
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM = """You are a Databricks SQL expert writing attrition cohort notebooks for
Premier PHD (PINC AI™ Healthcare Database v2.2).
SQL runs on Databricks SQL Warehouse — use ANSI SQL only (no Spark-specific syntax).

═══════════════════════════ INFRASTRUCTURE ═══════════════════════════════════
Catalog / Schema : rhealth_premier_phd.bronze_native_premier_phd
IMPORTANT        : PHD documentation calls it PATDEMO — the actual Databricks
                   table is named `pat` (NOT `patdemo`).

KEY TABLES AND EXACT FIELD NAMES:
  pat            : pat_key, medrec_key, prov_id, admit_date, discharge_date,
                   age (integer years), gender (M/F/U), i_o_ind (I=Inpatient/O=Outpatient),
                   pat_type, ms_drg, los, pat_cost, pat_charges,
                   pat_fix_cost (room & board), pat_var_cost (pharmacy/supplies/imaging),
                   disc_status, publish_type (CP/CV)
  paticd_proc    : pat_key, icd_version (9 or 10), icd_code,
                   icd_pri_sec (P=Principal / S=Secondary)
  paticd_diag    : pat_key, icd_version (9 or 10), icd_code,
                   icd_pri_sec (A=Admitting / P=Principal / S=Secondary), icd_poa
  patcpt         : pat_key, cpt_code
  prov_enrollment: prov_id, ip_max_dx_date
  providers      : prov_id, urban_rural, teaching, beds_grp, prov_region

═══════════════════════════ MANDATORY STYLE RULES ════════════════════════════
1.  Banner comment at top of every cell:
    -- ════════════════════════════════════════════════════════════════════════════
    -- STEP N (INCLUSION/EXCLUSION) — <description>
    -- ════════════════════════════════════════════════════════════════════════════

2.  Every step: CREATE OR REPLACE TEMPORARY TABLE <name> AS ... ;

3.  Step 1 table name MUST be: step1_surgery_index
    Steps 2+ use short semantic names: step2_age_18_plus, step3_hosp_90d,
    step4_known_gender, step5_publish_cv, step6_positive_cost, step7_final_cohort
    (name comes from the instruction, match it exactly)

4.  Step 1 MUST use this exact 4-CTE pattern:
      icd_proc_match  →  cpt_match  →  all_matches  →  ranked
    Use UNION (not UNION ALL) in all_matches to deduplicate.
    ranked CTE uses ROW_NUMBER() OVER (PARTITION BY medrec_key, surgery_category
                                        ORDER BY admit_date ASC, pat_key ASC) AS rn
    Final SELECT: WHERE rn = 1

5.  Steps 2+ always: SELECT * FROM <prev_table> WHERE <condition>
    Never re-join to source tables in steps 2+.

6.  Each cell MUST end with an appropriate count-check SELECT (see examples).

7.  Date arithmetic: DATE_ADD(col, N)  — not DATEADD, not interval syntax.

8.  Use COALESCE() not IFNULL().

9.  Use paticd_proc for ICD procedure codes (icd_pri_sec = 'P' for principal).
    Use patcpt for CPT-4 codes (any position — no principal flag in Premier CPT).
    Use paticd_diag for ICD diagnosis codes.

10. Return ONLY the SQL. No markdown fences, no explanations, no comments
    outside the SQL itself.

═══════════════════════════ STEP EXAMPLES ════════════════════════════════════

EXAMPLE — Step 2 (age >= 18):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 2 (INCLUSION) — Age >= 18 at index admission
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step2_age_18_plus AS
SELECT *
FROM step1_surgery_index
WHERE age >= 18;

-- Count check
SELECT
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients,
    MIN(age)                   AS min_age,
    MAX(age)                   AS max_age,
    ROUND(AVG(age), 1)         AS mean_age
FROM step2_age_18_plus;

EXAMPLE — Step 3 (hospital 90-day data contribution):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 3 (INCLUSION) — Hospital contributes data >= 90 days post-discharge
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step3_hosp_90d AS

WITH hospital_last_data AS (
    SELECT prov_id, MAX(ip_max_dx_date) AS max_data_date
    FROM rhealth_premier_phd.bronze_native_premier_phd.prov_enrollment
    GROUP BY prov_id
)

SELECT s.*
FROM step2_age_18_plus s
INNER JOIN hospital_last_data h ON s.prov_id = h.prov_id
WHERE h.max_data_date >= DATE_ADD(s.discharge_date, 90);

-- Count check
SELECT
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients,
    COUNT(DISTINCT prov_id)    AS qualifying_hospitals
FROM step3_hosp_90d;

EXAMPLE — Step 4 (known gender):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 4 (INCLUSION) — Known gender: M or F (drop U = Unknown)
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step4_known_gender AS
SELECT *
FROM step3_hosp_90d
WHERE gender IN ('M', 'F');

-- Count check
SELECT
    gender,
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients
FROM step4_known_gender
GROUP BY gender
ORDER BY gender;

EXAMPLE — Step 5 (publish type CV):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 5 (INCLUSION) — Publish type = Comparative Valid (CV)
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step5_publish_cv AS
SELECT *
FROM step4_known_gender
WHERE publish_type = 'CV';

-- Count check
SELECT
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients,
    COUNT(DISTINCT prov_id)    AS cv_hospitals
FROM step5_publish_cv;

EXAMPLE — Step 6 (exclusion: zero/negative costs):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 6 (EXCLUSION) — Remove patients with zero or negative costs
-- Exclusion: pat_cost <= 0 OR pat_fix_cost <= 0 OR pat_var_cost <= 0
-- SQL keeps complement: all three must be > 0
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step6_positive_cost AS
SELECT *
FROM step5_publish_cv
WHERE pat_cost     > 0
  AND pat_fix_cost > 0
  AND pat_var_cost > 0;

-- Count check
SELECT
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients,
    ROUND(MIN(pat_cost), 2)    AS min_total_cost,
    ROUND(AVG(pat_cost), 0)    AS avg_total_cost,
    ROUND(MAX(pat_cost), 0)    AS max_total_cost
FROM step6_positive_cost;

EXAMPLE — Step 7 (exclusion: missing key data):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 7 (EXCLUSION) — Remove patients with missing key data
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step7_final_cohort AS
SELECT *
FROM step6_positive_cost
WHERE age            IS NOT NULL
  AND gender         IS NOT NULL
  AND prov_id        IS NOT NULL
  AND index_date     IS NOT NULL
  AND discharge_date IS NOT NULL
  AND pat_cost       IS NOT NULL
  AND los            IS NOT NULL;

-- Count check
SELECT
    COUNT(*)                   AS final_index_admissions,
    COUNT(DISTINCT medrec_key) AS final_unique_patients,
    COUNT(DISTINCT prov_id)    AS hospitals
FROM step7_final_cohort;

EXAMPLE — Attrition Waterfall:
-- ════════════════════════════════════════════════════════════════════════════
-- ATTRITION WATERFALL
-- enc_dropped / pts_dropped = difference vs previous step
-- ════════════════════════════════════════════════════════════════════════════

WITH counts AS (

    SELECT 1 AS n, 'INC' AS type,
           '1. Primary surgery procedure code (Index)' AS step,
           COUNT(*) AS enc, COUNT(DISTINCT medrec_key) AS pts
    FROM step1_surgery_index

    UNION ALL
    SELECT 2, 'INC', '2. Age >= 18',
           COUNT(*), COUNT(DISTINCT medrec_key)
    FROM step2_age_18_plus

    UNION ALL
    SELECT 3, 'INC', '3. Hospital >= 90 days post-discharge',
           COUNT(*), COUNT(DISTINCT medrec_key)
    FROM step3_hosp_90d

)

SELECT
    n                                        AS step_num,
    type                                     AS step_type,
    step                                     AS step_description,
    enc                                      AS enc_after,
    pts                                      AS pts_after,
    LAG(enc) OVER (ORDER BY n) - enc         AS enc_dropped,
    LAG(pts) OVER (ORDER BY n) - pts         AS pts_dropped
FROM counts
ORDER BY n;

EXAMPLE — Final Cohort Summary:
SELECT
    surgery_category,
    COUNT(*)                                             AS index_admissions,
    COUNT(DISTINCT medrec_key)                           AS unique_patients,
    COUNT(DISTINCT prov_id)                              AS hospitals,
    ROUND(AVG(age),          1)                          AS mean_age,
    SUM(CASE WHEN gender  = 'F' THEN 1 ELSE 0 END)       AS female_n,
    SUM(CASE WHEN gender  = 'M' THEN 1 ELSE 0 END)       AS male_n,
    SUM(CASE WHEN i_o_ind = 'I' THEN 1 ELSE 0 END)       AS inpatient_n,
    SUM(CASE WHEN i_o_ind = 'O' THEN 1 ELSE 0 END)       AS outpatient_n,
    ROUND(AVG(los),          1)                          AS mean_los_days,
    ROUND(AVG(pat_cost),     0)                          AS mean_total_cost_usd,
    ROUND(AVG(pat_fix_cost), 0)                          AS mean_room_board_cost_usd,
    ROUND(AVG(pat_var_cost), 0)                          AS mean_variable_cost_usd,
    ROUND(AVG(pat_charges),  0)                          AS mean_billed_charges_usd
FROM <last_step_table>
GROUP BY surgery_category
ORDER BY surgery_category;
"""


# ─────────────────────────────────────────────────────────────────────────────
# HTTP client
# ─────────────────────────────────────────────────────────────────────────────

def _call_claude(token: str, user_message: str, max_tokens: int = 8000) -> str:
    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
    }
    resp = requests.post(
        CLAUDE_ENDPOINT_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _clean_sql(raw: str) -> str:
    """Strip accidental markdown fences."""
    if "```" in raw:
        lines = [l for l in raw.splitlines() if not l.strip().startswith("```")]
        return "\n".join(lines).strip()
    return raw


# ─────────────────────────────────────────────────────────────────────────────
# SQL completeness validation
# ─────────────────────────────────────────────────────────────────────────────

def _is_complete(sql: str, step_num: int) -> bool:
    """Returns True if the SQL looks complete (not truncated)."""
    s = sql.upper()
    # Must always end with a semicolon (count check)
    if not sql.rstrip().endswith(";"):
        return False
    # Must have CREATE OR REPLACE TEMPORARY TABLE
    if "CREATE OR REPLACE TEMPORARY TABLE" not in s:
        return False
    # Step 1 must have the full CTE chain
    if step_num == 1:
        required = ["ALL_MATCHES", "RANKED", "WHERE RN = 1", "COUNT(*)"]
        return all(r in s for r in required)
    # All steps must have a count check
    return "COUNT(*)" in s


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — structured prompt
# ─────────────────────────────────────────────────────────────────────────────

def _build_step1_prompt(
    description: str,
    target_table: str,
    code_table_mapping: Dict,
    study_window: str,
) -> str:
    """Build a highly structured prompt for Step 1 so Claude fills in a known template."""

    # Separate by system type
    icd_entries  = []  # (condition, table_name)
    cpt_entries  = []
    diag_entries = []

    for cond, type_map in code_table_mapping.items():
        for sys_type, tables in type_map.items():
            for tbl in tables:
                if sys_type == "icd_proc":
                    icd_entries.append((cond, tbl))
                elif sys_type == "cpt":
                    cpt_entries.append((cond, tbl))
                elif sys_type == "icd_diag":
                    diag_entries.append((cond, tbl))

    # Generate short aliases
    def _alias(i, prefix): return f"{prefix}{i:02d}"

    icd_alias_lines = "\n".join(
        f"  {_alias(i, 'i')} → {tbl}  (condition = '{cond}')"
        for i, (cond, tbl) in enumerate(icd_entries)
    )
    cpt_alias_lines = "\n".join(
        f"  {_alias(i, 'c')} → {tbl}  (condition = '{cond}')"
        for i, (cond, tbl) in enumerate(cpt_entries)
    )
    diag_alias_lines = "\n".join(
        f"  {_alias(i, 'd')} → {tbl}  (condition = '{cond}')"
        for i, (cond, tbl) in enumerate(diag_entries)
    )

    win_filter = (
        f"WHERE p.admit_date BETWEEN '{study_window.split(' to ')[0]}' AND '{study_window.split(' to ')[1]}'"
        if " to " in study_window
        else "-- TODO: Add study window date filter (e.g. WHERE p.admit_date BETWEEN '...' AND '...')"
    )

    sections = []

    if icd_entries:
        sections.append(f"""
ICD-10 PCS PROCEDURE TABLES — join to paticd_proc
WHERE icd_version = 10 AND icd_pri_sec = 'P'
{icd_alias_lines}

icd_proc_match CTE template:
  SELECT ip.pat_key,
      CASE
{chr(10).join(f"          WHEN {_alias(i, 'i')}.code IS NOT NULL THEN '{''.join(cond)}'" for i, (cond, _) in enumerate(icd_entries))}
      END AS surgery_category
  FROM rhealth_premier_phd.bronze_native_premier_phd.paticd_proc ip
{chr(10).join(f"  LEFT JOIN {tbl} {_alias(i, 'i')} ON ip.icd_code = {_alias(i, 'i')}.code" for i, (_, tbl) in enumerate(icd_entries))}
  WHERE ip.icd_version = 10
    AND ip.icd_pri_sec = 'P'
    AND COALESCE({', '.join(f'{_alias(i, "i")}.code' for i in range(len(icd_entries)))}) IS NOT NULL
""")

    if cpt_entries:
        sections.append(f"""
CPT-4 TABLES — join to patcpt (any position, no icd_pri_sec filter)
{cpt_alias_lines}

cpt_match CTE template:
  SELECT cp.pat_key,
      CASE
{chr(10).join(f"          WHEN {_alias(i, 'c')}.code IS NOT NULL THEN '{cond}'" for i, (cond, _) in enumerate(cpt_entries))}
      END AS surgery_category
  FROM rhealth_premier_phd.bronze_native_premier_phd.patcpt cp
{chr(10).join(f"  LEFT JOIN {tbl} {_alias(i, 'c')} ON cp.cpt_code = {_alias(i, 'c')}.code" for i, (_, tbl) in enumerate(cpt_entries))}
  WHERE COALESCE({', '.join(f'{_alias(i, "c")}.code' for i in range(len(cpt_entries)))}) IS NOT NULL
""")

    if diag_entries:
        sections.append(f"""
ICD-10 CM DIAGNOSIS TABLES — join to paticd_diag
{diag_alias_lines}
""")

    all_union_parts = []
    if icd_entries:
        all_union_parts.append("    SELECT pat_key, surgery_category FROM icd_proc_match")
    if cpt_entries:
        all_union_parts.append("    SELECT pat_key, surgery_category FROM cpt_match")
    if diag_entries:
        all_union_parts.append("    SELECT pat_key, surgery_category FROM icd_diag_match")
    union_sql = "\n    UNION\n".join(all_union_parts)

    return f"""Generate the COMPLETE Step 1 SQL for Premier PHD attrition following the exact style rules.

Target table : {target_table}
Description  : {description}
Study window : {study_window or 'extract from description above'}

{''.join(sections)}

Required CTE chain (use exactly this structure):
1. {'icd_proc_match' if icd_entries else '(no ICD proc)'}  — from paticd_proc
2. {'cpt_match'      if cpt_entries else '(no CPT)'}       — from patcpt
3. all_matches AS (
{union_sql}
   )
4. ranked AS (
    SELECT p.pat_key, p.medrec_key, p.prov_id,
        p.admit_date AS index_date, p.discharge_date,
        p.age, p.gender, p.publish_type, p.i_o_ind, p.pat_type, p.ms_drg, p.los,
        p.pat_cost, p.pat_charges, p.pat_fix_cost, p.pat_var_cost,
        p.disc_status, m.surgery_category,
        ROW_NUMBER() OVER (
            PARTITION BY p.medrec_key, m.surgery_category
            ORDER BY p.admit_date ASC, p.pat_key ASC
        ) AS rn
    FROM rhealth_premier_phd.bronze_native_premier_phd.pat p
    INNER JOIN all_matches m ON p.pat_key = m.pat_key
    {win_filter}
   )
Final SELECT: all columns from ranked WHERE rn = 1

Then end with count check:
SELECT surgery_category, COUNT(*) AS index_admissions, COUNT(DISTINCT medrec_key) AS unique_patients
FROM {target_table} GROUP BY surgery_category ORDER BY surgery_category;

IMPORTANT: Output the COMPLETE SQL. Do not truncate. Include all CTEs, the final SELECT, and the count check."""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_step_sql(
    step_num: int,
    step_type: str,
    description: str,
    prev_table: str,
    target_table: str,
    token: str,
    code_table_mapping: Optional[Dict] = None,
    code_table_names: Optional[List] = None,
    study_window: str = "",
) -> str:
    label    = "INCLUSION" if step_type == "inclusion" else "EXCLUSION"
    max_tok  = 16000 if step_num == 1 else 4000

    if step_num == 1 and code_table_mapping:
        prompt = _build_step1_prompt(description, target_table, code_table_mapping, study_window)
    else:
        tables_info = (
            "\n".join(f"  - {t}" for t in (code_table_names or []))
            or "  (none)"
        )
        win_line = f"Study window: {study_window}" if study_window else ""
        prompt = f"""Generate the Databricks SQL for the following attrition step.
Follow the style rules and examples in your system prompt exactly.

Step number  : {step_num}
Step type    : {label}
Description  : {description}
Source table : {prev_table}
Target table : {target_table}
{win_line}

Code list temp tables available (already created earlier in this notebook):
{tables_info}

Requirements:
- Banner comment with ════ border
- CREATE OR REPLACE TEMPORARY TABLE {target_table} AS SELECT * FROM {prev_table} WHERE <condition>
- Appropriate count check SELECT at the end (match style from your examples)
- Return ONLY the complete SQL"""

    try:
        sql = _clean_sql(_call_claude(token, prompt, max_tokens=max_tok))

        # Validate — retry once if truncated
        if not _is_complete(sql, step_num):
            retry_prompt = (
                f"Your previous response was incomplete or truncated.\n"
                f"Generate the COMPLETE SQL again for this step. Do not stop early.\n\n"
                f"{prompt}"
            )
            sql = _clean_sql(_call_claude(token, retry_prompt, max_tokens=max_tok))

        return sql

    except Exception as e:
        return _fallback_sql(target_table, description, label, str(e))


def _make_waterfall_fallback(step_records: list) -> str:
    """Reliable Python-generated waterfall — used when LLM call fails or returns incomplete SQL."""
    def _esc(s: str) -> str:
        return s.replace("'", "''")

    rows = []
    for n, stype, desc, tbl in step_records:
        label     = "INC" if str(stype).lower() == "inclusion" else "EXC"
        safe_desc = _esc(str(desc)[:80])
        rows.append(
            f"    SELECT {n} AS n, '{label}' AS type, '{safe_desc}' AS step,\n"
            f"           COUNT(*) AS enc, COUNT(DISTINCT medrec_key) AS pts\n"
            f"    FROM {tbl}"
        )
    union_all = "\n    UNION ALL\n".join(rows)
    return (
        f"-- ════════════════════════════════════════════════════════════════════════════\n"
        f"-- ATTRITION WATERFALL\n"
        f"-- enc_dropped / pts_dropped = difference vs previous step\n"
        f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
        f"WITH counts AS (\n\n{union_all}\n\n)\n\n"
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


def _make_final_fallback(last_table: str) -> str:
    """Reliable Python-generated final summary — used when LLM call fails or returns incomplete SQL."""
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


def _is_waterfall_complete(sql: str) -> bool:
    s = sql.upper()
    return (
        sql.rstrip().endswith(";")
        and "WITH COUNTS AS" in s
        and "LAG(" in s
        and "ENC_DROPPED" in s
        and "PTS_DROPPED" in s
    )


def _is_final_complete(sql: str) -> bool:
    s = sql.upper()
    return (
        sql.rstrip().endswith(";")
        and "SURGERY_CATEGORY" in s
        and "INDEX_ADMISSIONS" in s
        and "MEAN_TOTAL_COST_USD" in s
    )


def generate_waterfall_sql(step_records: list, token: str) -> str:
    steps_info = "\n".join(
        f"  {n}. [{str(stype).upper()[:3]}] {desc}  →  table: {tbl}"
        for n, stype, desc, tbl in step_records
    )

    prompt = f"""Generate the COMPLETE attrition waterfall SQL following the style in your examples.

Steps:
{steps_info}

Requirements:
- Banner comment with ════ border
- WITH counts AS ( SELECT 1 AS n, 'INC'/'EXC' AS type, '<description>' AS step, COUNT(*) AS enc, COUNT(DISTINCT medrec_key) AS pts FROM <table> UNION ALL ... )
- Final SELECT must include: n AS step_num, type AS step_type, step AS step_description, enc_after, pts_after, LAG(enc) OVER (ORDER BY n) - enc AS enc_dropped, LAG(pts) OVER (ORDER BY n) - pts AS pts_dropped
- ORDER BY n
- Return ONLY the complete SQL. Do not truncate."""

    try:
        sql = _clean_sql(_call_claude(token, prompt, max_tokens=6000))
        if not _is_waterfall_complete(sql):
            retry = (
                f"Your previous response was incomplete. Generate the COMPLETE waterfall SQL again. "
                f"Do not stop early.\n\n{prompt}"
            )
            sql = _clean_sql(_call_claude(token, retry, max_tokens=6000))
        if _is_waterfall_complete(sql):
            return sql
        return _make_waterfall_fallback(step_records)
    except Exception:
        return _make_waterfall_fallback(step_records)


def generate_final_summary_sql(last_table: str, token: str) -> str:
    prompt = f"""Generate the COMPLETE final cohort summary SQL reading from {last_table}.
Follow the exact style in your examples.

Requirements:
- Banner comment with ════ border
- GROUP BY surgery_category, ORDER BY surgery_category
- Include ALL 14 columns: surgery_category, index_admissions, unique_patients, hospitals,
  mean_age, female_n, male_n, inpatient_n, outpatient_n, mean_los_days,
  mean_total_cost_usd, mean_room_board_cost_usd, mean_variable_cost_usd, mean_billed_charges_usd
- Use ROUND(AVG(...), 0) for cost columns, ROUND(AVG(...), 1) for age and LOS
- Return ONLY the complete SQL. Do not truncate."""

    try:
        sql = _clean_sql(_call_claude(token, prompt, max_tokens=3000))
        if not _is_final_complete(sql):
            sql = _clean_sql(_call_claude(
                token,
                f"Your previous response was incomplete. Regenerate the full final summary SQL.\n\n{prompt}",
                max_tokens=3000,
            ))
        if _is_final_complete(sql):
            return sql
        return _make_final_fallback(last_table)
    except Exception:
        return _make_final_fallback(last_table)


def _fallback_sql(target_table: str, description: str, label: str, error: str) -> str:
    return (
        f"-- ════════════════════════════════════════════════════════════════════════════\n"
        f"-- {label}: {description}\n"
        f"-- MODEL ERROR: {error}\n"
        f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
        f"CREATE OR REPLACE TEMPORARY TABLE {target_table} AS\n"
        f"-- TODO: Implement filter for: {description}\n"
        f"SELECT * FROM prev_step_table\n"
        f"WHERE 1=1;\n\n"
        f"SELECT COUNT(*) AS index_admissions, COUNT(DISTINCT medrec_key) AS unique_patients\n"
        f"FROM {target_table};"
    )


def is_configured() -> bool:
    return bool(CLAUDE_ENDPOINT_URL)
