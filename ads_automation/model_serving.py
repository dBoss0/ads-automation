"""
Databricks Model Serving — Claude Opus 5 SQL generation.
Endpoint: databricks-claude-opus-5 on dbc-db3d8a4e-f2cf.cloud.databricks.com
"""

import requests

CLAUDE_ENDPOINT_URL = (
    "https://dbc-db3d8a4e-f2cf.cloud.databricks.com"
    "/serving-endpoints/databricks-claude-opus-5/invocations"
)

PREMIER_CATALOG = "rhealth_premier_phd.bronze_native_premier_phd"

# ─── Few-shot style reference drawn from the mock validation notebook ─────────
_STYLE_REFERENCE = """
You are a Databricks SQL expert writing attrition cohort notebooks for Premier PHD
(PINC AI™ Healthcare Database v2.2). Study SQL runs on Databricks SQL Warehouse —
use ANSI SQL only (no Spark-specific syntax).

CATALOG/SCHEMA: rhealth_premier_phd.bronze_native_premier_phd
KEY TABLES AND FIELDS:
  pat           : pat_key, medrec_key, prov_id, admit_date, discharge_date,
                  age, gender (M/F/U), i_o_ind (I/O), pat_type, ms_drg, los,
                  pat_cost, pat_charges, pat_fix_cost, pat_var_cost,
                  disc_status, publish_type (CP/CV)
  paticd_proc   : pat_key, icd_version (9/10), icd_code,
                  icd_pri_sec (P=Principal / S=Secondary)
  paticd_diag   : pat_key, icd_version (9/10), icd_code,
                  icd_pri_sec (A=Admitting / P=Principal / S=Secondary), icd_poa
  patcpt        : pat_key, cpt_code
  prov_enrollment: prov_id, ip_max_dx_date
  providers     : prov_id, urban_rural, teaching, beds_grp, prov_region

STYLE RULES — follow every one of these exactly:
1. Every step is: CREATE OR REPLACE TEMPORARY TABLE <name> AS ... ;
2. Step names: step1_surgery_index, step2_<slug>, step3_<slug>, ...
   Slug = lowercase description, spaces → underscores, max 35 chars.
3. Each cell ends with a SELECT count check appropriate to the step (see examples).
4. Use a banner comment block at the top:
   -- ════════════════════════════════════════════════════════════════════════════
   -- STEP N (INCLUSION/EXCLUSION) — <description>
   -- ════════════════════════════════════════════════════════════════════════════
5. Step 1 always uses WITH CTEs (icd_proc_match, cpt_match, all_matches, ranked)
   and ROW_NUMBER() OVER (PARTITION BY medrec_key, surgery_category ORDER BY admit_date, pat_key) AS rn
   to pick the index (first) admission.
6. Steps 2+ always SELECT * FROM prev_step_table WHERE <condition>.
7. Use DATE_ADD(date_col, N) for date arithmetic.
8. Use COALESCE() not IFNULL().
9. All column references in SELECT lists must match the pat table field names exactly.

EXAMPLE — Step 1 (index admission with ICD-10 PCS + CPT-4 code lists):
-- ════════════════════════════════════════════════════════════════════════════
-- STEP 1 (INCLUSION)
-- Primary surgery procedure code, 2016-01-01 to 2022-12-31.
-- Index = first qualifying admission per patient per surgery category.
-- ════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE TEMPORARY TABLE step1_surgery_index AS

WITH

icd_match AS (
    SELECT
        ip.pat_key,
        CASE
            WHEN b.code  IS NOT NULL THEN 'Bariatric'
            WHEN cs.code IS NOT NULL THEN 'C-Section'
        END AS surgery_category
    FROM rhealth_premier_phd.bronze_native_premier_phd.paticd_proc ip
    LEFT JOIN tmp__bariatric__icd_10_pcs   b  ON ip.icd_code = b.code
    LEFT JOIN tmp__c___section__icd_10_pcs cs ON ip.icd_code = cs.code
    WHERE ip.icd_version = 10
      AND ip.icd_pri_sec = 'P'
      AND COALESCE(b.code, cs.code) IS NOT NULL
),

cpt_match AS (
    SELECT DISTINCT
        cp.pat_key,
        'Bariatric' AS surgery_category
    FROM rhealth_premier_phd.bronze_native_premier_phd.patcpt cp
    INNER JOIN tmp__bariatric__cpt4 b ON cp.cpt_code = b.code
),

all_matches AS (
    SELECT pat_key, surgery_category FROM icd_match
    UNION
    SELECT pat_key, surgery_category FROM cpt_match
),

ranked AS (
    SELECT
        p.pat_key, p.medrec_key, p.prov_id,
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
    WHERE p.admit_date BETWEEN '2016-01-01' AND '2022-12-31'
)

SELECT
    pat_key, medrec_key, prov_id, index_date, discharge_date,
    age, gender, publish_type, i_o_ind, pat_type, ms_drg, los,
    pat_cost, pat_charges, pat_fix_cost, pat_var_cost,
    disc_status, surgery_category
FROM ranked
WHERE rn = 1;

-- Count check
SELECT
    surgery_category,
    COUNT(*)                   AS index_admissions,
    COUNT(DISTINCT medrec_key) AS unique_patients
FROM step1_surgery_index
GROUP BY surgery_category
ORDER BY surgery_category;

EXAMPLE — Step 2 (age filter):
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
    SELECT
        prov_id,
        MAX(ip_max_dx_date) AS max_data_date
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

EXAMPLE — Step 5 (publish type):
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

OUTPUT RULES:
- Return ONLY the SQL. No markdown code fences, no explanation text.
- The SQL must be runnable as-is on Databricks SQL Warehouse.
- Always include the banner comment and the count check SELECT at the end.
"""


def _call_claude(token: str, user_message: str, max_tokens: int = 2000) -> str:
    payload = {
        "messages": [
            {"role": "system", "content": _STYLE_REFERENCE},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
    }
    resp = requests.post(
        CLAUDE_ENDPOINT_URL,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_step_sql(
    step_num: int,
    step_type: str,
    description: str,
    prev_table: str,
    target_table: str,
    token: str,
    code_table_names: list = None,
    study_window: str = "",
) -> str:
    """
    Call Claude Opus 5 to generate SQL for one attrition step.

    Args:
        step_num        : 1-based step index
        step_type       : "inclusion" or "exclusion"
        description     : Step description text from the protocol
        prev_table      : Source temp table name from prior step
        target_table    : Target temp table name to CREATE
        token           : Databricks PAT token
        code_table_names: List of code list temp table names available in this session
        study_window    : Optional date range string e.g. "2016-01-01 to 2022-12-31"
    """
    label = "INCLUSION" if step_type == "inclusion" else "EXCLUSION"
    tables_info = (
        "\n".join(f"  - {t}" for t in code_table_names)
        if code_table_names else "  (none)"
    )
    window_line = f"Study window: {study_window}" if study_window else ""

    prompt = f"""Generate the Databricks SQL for the following attrition step.
Follow the style, structure, and rules shown in your examples exactly.

Step number  : {step_num}
Step type    : {label}
Description  : {description}
Source table : {prev_table}
Target table : {target_table}
{window_line}

Code list temp tables available in this session (already created):
{tables_info}

Write the complete SQL for target table {target_table} — banner comment,
CREATE OR REPLACE TEMPORARY TABLE, and count check SELECT at the end.
Return ONLY the SQL."""

    try:
        sql = _call_claude(token, prompt)
        # Strip accidental markdown fences if model adds them
        if sql.startswith("```"):
            sql = "\n".join(
                line for line in sql.splitlines()
                if not line.strip().startswith("```")
            ).strip()
        return sql
    except Exception as e:
        return _fallback_sql(target_table, description, label, str(e))


def generate_waterfall_sql(step_records: list, token: str) -> str:
    """
    Call Claude to generate the attrition waterfall query from all step table names.
    step_records: list of (n, step_type, description, table_name)
    """
    steps_info = "\n".join(
        f"  {n}. [{stype.upper()[:3]}] {desc}  →  {tbl}"
        for n, stype, desc, tbl in step_records
    )

    prompt = f"""Generate the attrition waterfall SQL for these steps:

{steps_info}

Follow the exact style from the examples:
- WITH counts AS ( SELECT 1 AS n, ... FROM step1 UNION ALL SELECT 2 ... FROM step2 ... )
- Final SELECT with LAG(enc_after) OVER (ORDER BY n) - enc_after AS enc_dropped
- ORDER BY n

Return ONLY the SQL."""

    try:
        sql = _call_claude(token, prompt)
        if sql.startswith("```"):
            sql = "\n".join(
                line for line in sql.splitlines()
                if not line.strip().startswith("```")
            ).strip()
        return sql
    except Exception as e:
        return f"-- TODO: Waterfall query generation failed: {e}"


def generate_final_summary_sql(last_table: str, token: str) -> str:
    """Call Claude to generate the final cohort summary query."""
    prompt = f"""Generate the final cohort summary SQL reading from {last_table}.
Follow the exact style from the examples — group by surgery_category,
include: index_admissions, unique_patients, hospitals, mean_age, female_n, male_n,
inpatient_n, outpatient_n, mean_los_days, mean_total_cost_usd, mean_room_board_cost_usd,
mean_variable_cost_usd, mean_billed_charges_usd.
Return ONLY the SQL."""

    try:
        sql = _call_claude(token, prompt)
        if sql.startswith("```"):
            sql = "\n".join(
                line for line in sql.splitlines()
                if not line.strip().startswith("```")
            ).strip()
        return sql
    except Exception as e:
        return f"-- TODO: Final summary generation failed: {e}"


def _fallback_sql(target_table: str, description: str, label: str, error: str) -> str:
    return (
        f"-- ════════════════════════════════════════════════════════════════════════════\n"
        f"-- {label}: {description}\n"
        f"-- MODEL ERROR: {error}\n"
        f"-- ════════════════════════════════════════════════════════════════════════════\n\n"
        f"CREATE OR REPLACE TEMPORARY TABLE {target_table} AS\n"
        f"-- TODO: Implement filter for: {description}\n"
        f"SELECT * FROM prev_step_table\n"
        f"WHERE 1=1;  -- REPLACE with actual criterion\n\n"
        f"SELECT COUNT(*) AS index_admissions, COUNT(DISTINCT medrec_key) AS unique_patients\n"
        f"FROM {target_table};"
    )


def is_configured() -> bool:
    return bool(CLAUDE_ENDPOINT_URL)
