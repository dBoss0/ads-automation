# J&J MedTech — ADS Code Automation Platform
## Full Technical Documentation

**Version:** 1.0.0  
**Platform:** Databricks + Streamlit + Claude Opus 5  
**Data Source:** Premier PHD (PINC AI™ Healthcare Database v2.2)  
**Owner:** J&J MedTech Analytics & Data Sciences (ADS)

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Databricks Infrastructure](#3-databricks-infrastructure)
4. [LLM — Claude Opus 5 via Model Serving](#4-llm--claude-opus-5-via-model-serving)
5. [Agentic Flow — End to End](#5-agentic-flow--end-to-end)
6. [Premier PHD Data Model](#6-premier-phd-data-model)
7. [Code File Deep Dive](#7-code-file-deep-dive)
8. [SQL Generation Strategy](#8-sql-generation-strategy)
9. [Key Design Decisions](#9-key-design-decisions)
10. [Security & Access Control](#10-security--access-control)
11. [Environment Setup](#11-environment-setup)

---

## 1. Platform Overview

The **ADS Code Automation Platform** converts a clinical study protocol document (`.docx`) into a fully-executable Databricks SQL attrition cohort notebook — in under 60 seconds.

**What it eliminates:**  
Analysts previously wrote attrition SQL by hand: reading the protocol, translating each criterion into SQL, creating temp tables, writing waterfall queries. Each notebook took 4–8 hours. This platform generates the same notebook in one click.

**What the platform does, step by step:**

| Step | What Happens |
|---|---|
| 1 | Analyst uploads a clinical protocol `.docx` |
| 2 | Python parser extracts the study title, data source, inclusion/exclusion criteria |
| 3 | Analyst uploads an Excel file with ICD/CPT/DRG code lists from the client |
| 4 | Analyst selects which procedure categories to include |
| 5 | Platform calls **Claude Opus 5** (hosted on Databricks Model Serving) to generate SQL for each attrition step |
| 6 | Platform Python-generates the Attrition Waterfall and Final Summary cells (no LLM — deterministic templates) |
| 7 | Platform assembles a complete `.sql` Databricks SOURCE-format notebook |
| 8 | Platform pushes the notebook directly to the analyst's Databricks workspace via REST API |
| 9 | Analyst opens the notebook in Databricks and runs it against Premier PHD data |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ANALYST'S MACHINE                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Streamlit Web App  (streamlit_app.py)           │  │
│  │                                                              │  │
│  │  ┌─────────┐  ┌─────────────┐  ┌──────────────────────────┐ │  │
│  │  │Protocol │  │  Code List  │  │  Category Selector       │ │  │
│  │  │.docx    │  │  Excel/CSV  │  │  (INC/EXC per condition) │ │  │
│  │  │Upload   │  │  Upload     │  │                          │ │  │
│  │  └────┬────┘  └──────┬──────┘  └────────────┬─────────────┘ │  │
│  │       │              │                       │               │  │
│  │       ▼              ▼                       ▼               │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │              parser.py                                  │ │  │
│  │  │  Extracts: title, data_source, inclusion/exclusion steps│ │  │
│  │  └──────────────────────┬──────────────────────────────────┘ │  │
│  │                         │                                     │  │
│  │                         ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │         notebook_generator.py                           │ │  │
│  │  │                                                         │ │  │
│  │  │  Step 1 SQL ──► model_serving.py ──► Claude Opus 5     │ │  │
│  │  │  Step 2 SQL ──► model_serving.py ──► Claude Opus 5     │ │  │
│  │  │  Step N SQL ──► model_serving.py ──► Claude Opus 5     │ │  │
│  │  │  Waterfall  ──► Python Template (no LLM)               │ │  │
│  │  │  Final Summ ──► Python Template (no LLM)               │ │  │
│  │  └──────────────────────┬──────────────────────────────────┘ │  │
│  │                         │  notebook SQL (plain text)          │  │
│  │                         ▼                                     │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │         databricks_api.py                               │ │  │
│  │  │  POST /api/2.0/workspace/import  (base64 encoded SQL)   │ │  │
│  │  └──────────────────────┬──────────────────────────────────┘ │  │
│  └─────────────────────────┼────────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────────┘
                             │  HTTPS REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              DATABRICKS WORKSPACE (dbc-db3d8a4e-f2cf)              │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Model Serving Endpoint                                       │ │
│  │  Name: databricks-claude-opus-5                               │ │
│  │  URL:  /serving-endpoints/databricks-claude-opus-5/invocations│ │
│  │  API:  OpenAI-compatible chat completions                     │ │
│  │  LLM:  Anthropic Claude Opus 5 (hosted by Databricks)        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Unity Catalog — Data Storage                                 │ │
│  │                                                               │ │
│  │  Catalog : rhealth_premier_phd                                │ │
│  │  Schema  : bronze_native_premier_phd                          │ │
│  │  Tables  : pat, paticd_proc, paticd_diag, patcpt,            │ │
│  │            prov_enrollment, providers, ...                    │ │
│  │                                                               │ │
│  │  Scratch Catalog: rhealth_datasets_scratch_space              │ │
│  │  Scratch Schema : scratch_dbx_prphd_ads_automation_poc        │ │
│  │  (PHD Data Dictionary Delta table lives here)                 │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Generated Notebook (pushed by app)                           │ │
│  │  Path: /Users/<email>/ads_automation/<study>_attrition        │ │
│  │  Format: Databricks SOURCE SQL (.sql)                         │ │
│  │  Runs on: SQL Warehouse (ANSI SQL — no Spark syntax)          │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Databricks Infrastructure

### 3.1 Unity Catalog

**Unity Catalog** is Databricks' unified governance layer for all data assets. Everything in this project is organized within it.

```
Unity Catalog Structure used in this project:

rhealth_premier_phd
└── bronze_native_premier_phd          ← PHD source tables (read-only)
    ├── pat                            ← Patient/encounter master
    ├── paticd_proc                    ← ICD procedure codes
    ├── paticd_diag                    ← ICD diagnosis codes
    ├── patcpt                         ← CPT-4 / HCPCS codes
    ├── patbill                        ← Charge-level billing
    ├── prov_enrollment                ← Hospital data contribution dates
    ├── providers                      ← Hospital characteristics
    └── ... (lookup tables, add-on tables)

rhealth_datasets_scratch_space
└── scratch_dbx_prphd_ads_automation_poc    ← POC workspace
    └── premier_phd_data_dictionary_v2_2    ← Delta table (one-time setup)
```

**Why Unity Catalog matters here:**  
The generated SQL notebooks are designed to run inside Databricks with Unity Catalog governance. Access controls, lineage, and table versioning are all managed there — we never expose raw data outside this boundary.

### 3.2 Delta Tables

The PHD source data (`pat`, `paticd_proc`, etc.) lives in **Delta format** — Databricks' ACID-compliant table format built on Parquet + transaction logs.

**Critical rule enforced in this app:**  
> Delta table names must NEVER appear in the Streamlit UI or be displayed to users. They are referenced only in generated SQL.

The platform also generates a **PHD Data Dictionary Delta table** (one-time setup):
- Contains all 300+ field definitions from the PHD V2.2 documentation
- Stored in the scratch catalog for analysts to query/reference
- Generated by `premier_ddl.py` → pushed to Databricks as a notebook → run once

### 3.3 Model Serving — Claude Opus 5

Databricks **Model Serving** hosts the LLM as a REST endpoint inside the Databricks workspace. This means:
- The LLM call never leaves the Databricks security perimeter
- Authentication uses the same PAT token as all other Databricks API calls
- The endpoint exposes an **OpenAI-compatible** chat completions API

**Endpoint details:**
```
Host:     dbc-db3d8a4e-f2cf.cloud.databricks.com
Path:     /serving-endpoints/databricks-claude-opus-5/invocations
Auth:     Bearer <PAT>
Method:   POST
Format:   {"messages": [...], "max_tokens": N}
```

**Important quirk:** The Databricks-hosted Claude endpoint returns `content` as a list of content blocks rather than a plain string:
```json
{
  "choices": [{
    "message": {
      "content": [{"type": "text", "text": "SELECT ..."}]
    }
  }]
}
```
Our `_call_claude()` function handles both formats (list and plain string).

### 3.4 Databricks Workspace API

The app uses two Databricks REST APIs:

| API | Used For |
|---|---|
| `POST /api/2.0/workspace/mkdirs` | Create the target directory if it doesn't exist |
| `POST /api/2.0/workspace/import` | Push the generated notebook as a SOURCE-format SQL file |
| `GET /api/2.0/preview/scim/v2/Me` | Auto-detect the current user's email from their PAT token |

The notebook is Base64-encoded before sending:
```python
"content": base64.b64encode(content.encode("utf-8")).decode("ascii")
```

### 3.5 Notebook Format — Databricks SOURCE

Generated notebooks use **Databricks SOURCE format** — plain text with special comment markers:

```sql
-- Databricks notebook source

-- COMMAND ----------

-- MAGIC %md
-- MAGIC # Study Title

-- COMMAND ----------

CREATE OR REPLACE TEMPORARY TABLE step1_surgery_index AS ...;

-- COMMAND ----------

WITH counts AS ( ... )
SELECT ...
```

- `-- Databricks notebook source` → tells Databricks this is a SOURCE format file
- `-- COMMAND ----------` → cell separator
- `-- MAGIC %md` → markdown cell (rendered as formatted text in Databricks)
- All other content → SQL cells executed on the SQL Warehouse

---

## 4. LLM — Claude Opus 5 via Model Serving

### 4.1 What Claude Generates

Claude Opus 5 generates **SQL for attrition steps 1 through N**. It does NOT generate the waterfall or final summary (those are deterministic Python templates).

For each step, Claude receives:
- A detailed **system prompt** containing:
  - Full PHD schema (exact table names, field names, valid values)
  - Style rules (banner format, temp table naming, count check requirements)
  - Window function guidance (ROW_NUMBER vs RANK vs LAG/LEAD)
  - 6 complete SQL examples covering age filter, hospital data contribution, gender, publish type, cost exclusion, missing data
- A **step-specific user prompt** containing:
  - Step number, type (inclusion/exclusion), description
  - Source table (previous step's output)
  - Target table name
  - Available code list temp tables
  - For Step 1: structured template with ICD/CPT table aliases, CTE chain, study window dates

### 4.2 System Prompt Architecture

The `_SYSTEM` string in `model_serving.py` is the most important piece of the LLM configuration. It has three sections:

**Section 1 — INFRASTRUCTURE**  
Tells Claude the exact catalog, schema, table names, and all field names with their types and valid values. This prevents hallucination of non-existent columns.

**Section 2 — MANDATORY STYLE RULES (11 rules)**  
```
Rule 1:  Banner comment format with ════ border
Rule 2:  Always CREATE OR REPLACE TEMPORARY TABLE
Rule 3:  Step 1 table must be named step1_surgery_index
Rule 4:  Step 1 must use 4-CTE pattern: icd_proc_match → cpt_match → all_matches → ranked
Rule 5:  Steps 2+ always SELECT * FROM <prev_table> WHERE <condition>
Rule 6:  Each cell ends with a count-check SELECT
Rule 7:  Date arithmetic: DATE_ADD(col, N) only
Rule 8:  Use COALESCE() not IFNULL()
Rule 9:  ICD proc codes use paticd_proc; CPT uses patcpt; ICD diag uses paticd_diag
Rule 10: Window function guidance (ROW_NUMBER vs RANK vs DENSE_RANK vs LAG/LEAD)
Rule 11: Return ONLY the SQL — no markdown fences, no explanations
```

**Section 3 — STEP EXAMPLES**  
Six complete example SQL blocks covering the most common attrition patterns. These serve as few-shot examples so Claude matches the exact style.

### 4.3 Step 1 — Structured Prompt

Step 1 is the most complex — it must identify the index surgery from ICD procedure codes, CPT codes, and/or diagnosis codes across multiple conditions (e.g., TKA, THA, Bariatric, C-section). 

Instead of free-form prompting, we use `_build_step1_prompt()` which generates a **structured template prompt**:

```
icd_proc_match CTE template:
  SELECT ip.pat_key,
      CASE
          WHEN i00.code IS NOT NULL THEN 'TKA'
          WHEN i01.code IS NOT NULL THEN 'THA'
      END AS surgery_category
  FROM rhealth_premier_phd.bronze_native_premier_phd.paticd_proc ip
  LEFT JOIN tmp__tka__icd_10_pcs i00 ON ip.icd_code = i00.code
  LEFT JOIN tmp__tha__icd_10_pcs i01 ON ip.icd_code = i01.code
  WHERE ip.icd_version = 10 AND ip.icd_pri_sec = 'P'
    AND COALESCE(i00.code, i01.code) IS NOT NULL
```

This tells Claude exactly what the CTE structure should be, leaving only minor fill-in work (study window dates, final SELECT).

### 4.4 Validation and Retry

After each LLM call, the SQL is validated:

```python
def _is_complete(sql: str, step_num: int) -> bool:
    # Must end with semicolon
    # Must contain CREATE OR REPLACE TEMPORARY TABLE
    # Step 1: must contain ALL_MATCHES, RANKED, WHERE RN = 1, COUNT(*)
    # Other steps: must contain COUNT(*)
```

If validation fails → one automatic retry with a "your response was incomplete" prompt → if still fails → fallback template SQL with a `-- TODO:` comment.

### 4.5 Why Waterfall and Final Summary Bypass the LLM

Early testing showed Claude consistently hallucinated for these two cells — instead of generating a waterfall counting query, it would generate a new Step 1-style SQL with hardcoded procedure codes from its training data.

**Root cause:** The waterfall and final summary are pure mechanical templates with zero domain-specific logic. The LLM adds no value and introduces risk. They are now always generated by Python functions (`_fallback_waterfall`, `_fallback_final`) that produce identical, correct output every time.

---

## 5. Agentic Flow — End to End

```
User Action                     App Component              External Call
─────────────────────────────────────────────────────────────────────────
1. Paste PAT token              streamlit_app.py           GET /scim/v2/Me
   → auto-detects user email                               → returns userName

2. Upload .docx protocol        parser.py
   → read_docx()                                           (local, no network)
   → extract_project_title()
   → detect_data_source()
   → extract_study_selection()
   → split_criteria_sections()
   → extract_steps()
   → returns {title, attrition[], data_sources[]}

3. Upload Excel code list        streamlit_app.py
   → parse sheets with pandas                              (local, no network)
   → map: condition, coding_system, code, description
   → store in session_state.codelists_df

4. Select procedure categories   streamlit_app.py
   → multiselect widget
   → filter codelists_df to selected conditions only

5. Click "Generate & Push"       notebook_generator.py
   a. Build code list temp tables (pure Python, no LLM)
   b. Build code_table_mapping {condition: {type: [tables]}}
   c. For each attrition step:
      → if token present: call generate_step_sql()        POST /serving-endpoints/.../invocations
        → _build_step1_prompt() OR plain prompt
        → _call_claude() → validate → retry if needed
        → _fallback_sql() if still invalid
      → else: return TODO template
   d. Always Python-generate waterfall (_fallback_waterfall)
   e. Always Python-generate final summary (_fallback_final)
   f. Assemble all cells with CELL_SEP
   g. Return complete notebook SQL string

6. Push to Databricks            databricks_api.py
   → save_notebook()                                       POST /api/2.0/workspace/mkdirs
   → base64 encode notebook SQL                            POST /api/2.0/workspace/import
   → return notebook URL

7. Display result                streamlit_app.py
   → success banner with clickable Databricks URL
   → download button for local SQL copy
   → step preview table
```

---

## 6. Premier PHD Data Model

**Premier Healthcare Database (PHD)** is PINC AI's™ hospital-based administrative claims database covering ~25% of US hospital discharges.

### 6.1 Key Tables Used in Attrition

| Actual Table Name | PHD Doc Name | Purpose | Join Key |
|---|---|---|---|
| `pat` | PATDEMO | Patient/encounter master | `pat_key`, `medrec_key` |
| `paticd_proc` | PATICD_PROC | ICD-9/10 procedure codes | `pat_key` |
| `paticd_diag` | PATICD_DIAG | ICD-9/10 diagnosis codes | `pat_key` |
| `patcpt` | PATCPT | CPT-4 / HCPCS codes | `pat_key` |
| `prov_enrollment` | PROV_ENROLLMENT | Hospital data contribution dates | `prov_id` |
| `providers` | PROVIDERS | Hospital characteristics | `prov_id` |

> **Critical naming note:** The PHD documentation calls the patient table `PATDEMO`. The actual Databricks table is named `pat`. All generated SQL uses `pat`.

### 6.2 Key Fields

**`pat` table — the foundation of every cohort:**

| Field | Type | Description |
|---|---|---|
| `pat_key` | Integer | Unique encounter ID (de-identified) |
| `medrec_key` | Integer | Unique patient ID — tracks same patient across visits |
| `prov_id` | Integer | Hospital ID |
| `admit_date` | Date | Admission date |
| `discharge_date` | Date | Discharge date |
| `age` | Smallint | Age in years at admission |
| `gender` | Char(1) | M / F / U |
| `i_o_ind` | Char(1) | I = Inpatient, O = Outpatient |
| `los` | Smallint | Length of stay (inpatient only) |
| `pat_cost` | Decimal | Total cost (fixed + variable) |
| `pat_fix_cost` | Decimal | Fixed cost (room & board, overhead) |
| `pat_var_cost` | Decimal | Variable cost (pharmacy, supplies) |
| `pat_charges` | Decimal | Total billed charges |
| `publish_type` | Char(2) | CP = full financial validation; CV = validity only |
| `ms_drg` | Smallint | Medicare Severity DRG |

**`paticd_proc` — for identifying surgical procedures:**

| Field | Values | Usage |
|---|---|---|
| `icd_version` | 9 or 10 | Always filter `= 10` for modern studies |
| `icd_pri_sec` | P = Principal, S = Secondary | Always filter `= 'P'` for index procedure |
| `icd_code` | ICD-10-PCS code | Join to client-supplied code list temp table |

**`prov_enrollment` — for hospital data contribution filter:**

| Field | Usage |
|---|---|
| `ip_max_dx_date` | Latest inpatient discharge date known for hospital — used in 90-day filter |

### 6.3 The Standard Step 1 SQL Pattern

Step 1 always follows a 4-CTE pattern that is enforced by the LLM system prompt:

```sql
-- STEP 1 (INCLUSION): Primary surgery procedure (Index encounter)

CREATE OR REPLACE TEMPORARY TABLE step1_surgery_index AS

WITH icd_proc_match AS (
    -- Match ICD-10 PCS principal procedure codes to surgery categories
    SELECT ip.pat_key,
        CASE
            WHEN tka.code IS NOT NULL THEN 'TKA'
            WHEN tha.code IS NOT NULL THEN 'THA'
        END AS surgery_category
    FROM rhealth_premier_phd.bronze_native_premier_phd.paticd_proc ip
    LEFT JOIN tmp__tka__icd_10_pcs tka ON ip.icd_code = tka.code
    LEFT JOIN tmp__tha__icd_10_pcs tha ON ip.icd_code = tha.code
    WHERE ip.icd_version = 10
      AND ip.icd_pri_sec = 'P'
      AND COALESCE(tka.code, tha.code) IS NOT NULL
),

cpt_match AS (
    -- Match CPT-4 codes (any position — no principal flag in Premier CPT)
    SELECT cp.pat_key,
        CASE
            WHEN tka_cpt.code IS NOT NULL THEN 'TKA'
        END AS surgery_category
    FROM rhealth_premier_phd.bronze_native_premier_phd.patcpt cp
    LEFT JOIN tmp__tka__cpt_4 tka_cpt ON cp.cpt_code = tka_cpt.code
    WHERE COALESCE(tka_cpt.code) IS NOT NULL
),

all_matches AS (
    -- Deduplicate across code systems with UNION (not UNION ALL)
    SELECT pat_key, surgery_category FROM icd_proc_match
    UNION
    SELECT pat_key, surgery_category FROM cpt_match
),

ranked AS (
    -- One index encounter per patient per surgery category
    -- Using ROW_NUMBER for deterministic single-record selection
    SELECT p.pat_key, p.medrec_key, p.prov_id,
           p.admit_date AS index_date, p.discharge_date,
           p.age, p.gender, p.publish_type, p.i_o_ind,
           p.los, p.pat_cost, p.pat_charges, p.pat_fix_cost, p.pat_var_cost,
           p.disc_status, m.surgery_category,
           ROW_NUMBER() OVER (
               PARTITION BY p.medrec_key, m.surgery_category
               ORDER BY p.admit_date ASC, p.pat_key ASC
           ) AS rn
    FROM rhealth_premier_phd.bronze_native_premier_phd.pat p
    INNER JOIN all_matches m ON p.pat_key = m.pat_key
    WHERE p.admit_date BETWEEN '2019-01-01' AND '2023-12-31'
)

SELECT * FROM ranked WHERE rn = 1;

SELECT surgery_category, COUNT(*) AS index_admissions,
       COUNT(DISTINCT medrec_key) AS unique_patients
FROM step1_surgery_index
GROUP BY surgery_category ORDER BY surgery_category;
```

**Why this pattern:**
- `icd_proc_match` — ICD-10 PCS principal procedures only (icd_pri_sec = 'P')
- `cpt_match` — CPT codes at any position (no principal flag in Premier CPT)
- `all_matches` — `UNION` (not `UNION ALL`) deduplicates across code systems
- `ranked` — `ROW_NUMBER()` picks one index encounter per patient per surgery category (earliest admission). If a patient had TKA and THA in the same window, both appear as separate rows (different `surgery_category`)
- `WHERE rn = 1` — keeps only the index (first) encounter

### 6.4 Attrition Waterfall SQL Pattern

```sql
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
    SELECT 3, 'EXC', '3. EXCLUDE: Zero or negative costs',
           COUNT(*), COUNT(DISTINCT medrec_key)
    FROM step3_positive_cost

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
```

**Key points:**
- First row uses `SELECT N AS n, 'INC'/'EXC' AS type, '...' AS step, COUNT(*) AS enc, COUNT(DISTINCT medrec_key) AS pts`
- Subsequent rows use compact positional form (no column aliases)
- `LAG()` window function computes the drop from the previous step
- Exclusion steps prefixed with `EXCLUDE:` in the description

---

## 7. Code File Deep Dive

### 7.1 `streamlit_app.py` — The UI Layer

**Purpose:** Orchestrates the full user journey — file uploads, state management, LLM calls, Databricks push.

**Key sections:**

```python
# Session state initialization (line ~877)
for key, default in [
    ("steps_df", None),          # DataFrame: step_type + description
    ("codelists_df", None),      # DataFrame: condition + coding_system + code + description
    ("selected_conditions", None),  # list of condition names user wants in notebook
    ("dbx_token", ""),           # PAT token (password-masked input)
    ("dbx_user", ""),            # auto-detected email from SCIM API
    ("dbx_notebook_url", None),  # URL of pushed notebook
    ("dbx_notebook_sql", None),  # raw SQL string (for download button)
]:
```

**Token auto-detection (line ~980):**
```python
if dbx_token_input != st.session_state.dbx_token:
    st.session_state.dbx_token = dbx_token_input
    st.session_state.nb_path_override = None  # reset path for new user
    if dbx_token_input:
        try:
            st.session_state.dbx_user = get_current_user(_DBX_HOST, dbx_token_input)
        except Exception:
            st.session_state.dbx_user = ""
```
When anyone (DR20, PNV1, etc.) pastes their PAT, the app immediately calls Databricks SCIM API to get their email, then uses it to build the default notebook path `/Users/<email>/ads_automation/...`.

**Category selector (line ~1542):**
```python
# Auto-include new conditions while preserving prior deselections
if st.session_state.selected_conditions is None:
    st.session_state.selected_conditions = all_conds
else:
    prev  = set(st.session_state.selected_conditions)
    known = [c for c in st.session_state.selected_conditions if c in all_conds]
    new   = [c for c in all_conds if c not in prev]
    st.session_state.selected_conditions = known + new
```
If user had TKA selected and imports a new file with THA, THA gets auto-added. If user had previously deselected something, that deselection is preserved.

**Codelist filtering before generation (line ~1653):**
```python
active_codelists = active_codelists[
    active_codelists["condition"].isin(st.session_state.selected_conditions)
].reset_index(drop=True)
```
Only the selected conditions' code lists are passed to the notebook generator. Deselected conditions create no temp tables and do not appear in Step 1 SQL.

---

### 7.2 `ads_automation/parser.py` — Protocol Parser

**Purpose:** Convert a `.docx` clinical protocol into a structured list of attrition steps.

**Pipeline:**
```
read_docx()
  ↓ extracts paragraphs + table cells as plain text lines
extract_project_title(lines)
  ↓ looks for "Study Title:", "Protocol Title:", etc. with regex
detect_data_source(text)
  ↓ matches against DATA_SOURCE_MASTER dictionary
    e.g. "PINC AI" → "Premier Healthcare Database"
    strips trademark symbols (™, ®) before matching
extract_study_selection(text)
  ↓ finds the inclusion/exclusion block by section keywords
    start: "study design", "study population", "inclusion criteria"
    end: anchored AFTER exclusion section to avoid premature cutoff
split_criteria_sections(text)
  ↓ uses last occurrence of "inclusion criteria" / "exclusion criteria"
    (last occurrence skips table-of-contents mentions)
extract_steps(inclusion_text), extract_steps(exclusion_text)
  ↓ splits on newlines, strips bullets/numbering
  ↓ removes boilerplate lines ("patients will be included", "must meet all the following", etc.)
```

**Output:**
```python
{
    "title": "Comparative Effectiveness of Bariatric Surgery...",
    "data_sources": ["Premier Healthcare Database"],
    "attrition": [
        (1, "inclusion", "Primary bariatric surgery procedure (ICD-10 PCS codes)..."),
        (2, "inclusion", "Age >= 18 at index admission"),
        (3, "inclusion", "Hospital contributes data >= 90 days post-discharge"),
        (4, "exclusion", "Patients with zero or negative total costs"),
    ]
}
```

---

### 7.3 `ads_automation/model_serving.py` — LLM Interface

**Purpose:** All communication with the Claude Opus 5 endpoint. SQL generation, validation, retry, fallback.

**Key function — `_call_claude()` (line ~285):**
```python
def _call_claude(token: str, user_message: str, max_tokens: int = 8000) -> str:
    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
    }
    resp = requests.post(CLAUDE_ENDPOINT_URL, headers=..., json=payload, timeout=120)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    # Databricks returns content as list of blocks, not plain string
    if isinstance(content, list):
        content = "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return content.strip()
```

**Key function — `generate_step_sql()` (line ~481):**
```python
def generate_step_sql(step_num, step_type, description, prev_table,
                      target_table, token, code_table_mapping, ...):
    if step_num == 1 and code_table_mapping:
        prompt = _build_step1_prompt(...)   # structured CTE template
    else:
        prompt = f"...plain prompt..."       # step description + source table

    sql = _clean_sql(_call_claude(token, prompt, max_tokens=max_tok))
    if not _is_complete(sql, step_num):
        sql = _clean_sql(_call_claude(token, retry_prompt, max_tokens=max_tok))
    return sql   # or _fallback_sql() on exception
```

**`_build_step1_prompt()` — the structured Step 1 prompt builder (line ~345):**  
Takes the code_table_mapping (which temp tables exist for which conditions and code systems) and builds an explicit CTE scaffold with JOIN aliases. This dramatically reduces hallucination because Claude is filling in a known template rather than inventing structure.

---

### 7.4 `ads_automation/notebook_generator.py` — Notebook Builder

**Purpose:** Orchestrates all cells into a complete Databricks SOURCE-format notebook.

**Key function — `generate_databricks_notebook()` (line ~143):**

```python
def generate_databricks_notebook(title, steps_df, codelists_df, premier_catalog, token, study_window):
    cells = []

    # 1. Header markdown cell
    cells.append(_md_cell(f"%md\n# {title}\n..."))

    # 2. Code list temp table cells (one per condition × coding_system)
    for (cond, sys), grp in codelists_df.groupby(["condition", "coding_system"]):
        cells.append(_codelist_sql(cond, sys, pairs))

    # 3. Build code_table_mapping for Step 1 structured prompt
    code_table_mapping = _build_code_table_mapping(codelists_df)

    # 4. Attrition step cells — LLM generates SQL
    for idx, row in clean_steps.iterrows():
        tbl = "step1_surgery_index" if n==1 else _step_table_name(n, desc)
        sql = _llm_step(step_num=n, ..., code_table_mapping=... if n==1 else None)
        cells.append(sql)
        step_records.append((n, stype, desc, tbl))

    # 5. Waterfall — always Python-generated
    cells.append(_fallback_waterfall(step_records))

    # 6. Final summary — always Python-generated
    cells.append(_fallback_final(prev_table))

    return NOTEBOOK_HEADER + "\n" + CELL_SEP.join(cells)
```

**`_codelist_sql()` — generates a temp table from client code list (line ~91):**
```python
# Creates: CREATE OR REPLACE TEMPORARY TABLE tmp__tka__icd_10_pcs AS
#          SELECT * FROM VALUES ('0SR90..', 'TKA knee'), ('0SRB0..', 'TKA knee') AS t(code, description);
#          SELECT COUNT(*) AS codes FROM tmp__tka__icd_10_pcs;
```
Temp table name is deterministic: `tmp__{condition}__{coding_system}` with all special characters replaced by underscores.

**`_step_table_name()` — semantic naming (line ~60):**
```python
# Maps description keywords to short table names:
# "Age >= 18" → step2_age_18_plus
# "Hospital contributes >= 90 days" → step3_hosp_90d
# "Known gender" → step4_known_gender
# Falls back to first 3 meaningful words from description
```

**`_md_cell()` — converts text to Databricks markdown cell (line ~71):**
```python
# Each line becomes: -- MAGIC <line content>
# Empty lines become: -- MAGIC 
```

---

### 7.5 `ads_automation/databricks_api.py` — Databricks REST Client

**Purpose:** All direct Databricks API calls — push notebook, detect user, create directories.

```python
def save_notebook(host, token, path, content):
    # 1. Create parent directory
    requests.post(f"{host}/api/2.0/workspace/mkdirs", ...)
    # 2. Base64-encode and push notebook
    payload = {
        "path": path,
        "format": "SOURCE",    # plain text with -- COMMAND ---------- markers
        "language": "SQL",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "overwrite": True,
    }
    requests.post(f"{host}/api/2.0/workspace/import", ...)

def get_current_user(host, token):
    # Calls SCIM v2 /Me endpoint
    # Returns the userName field (email address)
    resp = requests.get(f"{host}/api/2.0/preview/scim/v2/Me", ...)
    return resp.json().get("userName", "")
```

**Environment detection (`is_databricks_app()`):**  
When the app runs inside Databricks Apps (deployed mode), `DATABRICKS_HOST` and `DATABRICKS_TOKEN` env vars are injected automatically. The `resolve_host()` and `resolve_token()` functions check env vars first, falling back to the sidebar PAT for local development.

---

### 7.6 `ads_automation/premier_ddl.py` — PHD Data Dictionary

**Purpose:** Two things in one file:
1. The `PHD_DICTIONARY` list — 300+ field definitions from the PHD V2.2 documentation, embedded as Python dicts
2. `generate_delta_ddl_notebook()` — generates a one-time-run Databricks notebook that creates this dictionary as a Delta table

**Why embed the dictionary in Python:**  
- Zero external dependency — no database lookup needed at app startup
- Used by `model_serving.py` to know exact field names and valid values
- Serves as authoritative reference for SQL generation accuracy

**Key lookup functions:**
```python
get_table_fields("paticd_proc")   # all fields for that table
get_field("pat", "publish_type")  # one field dict with valid_values
get_valid_values("pat", "gender") # returns "M=Male|F=Female|U=Unknown"
get_all_table_names()             # ['admtype', 'aprdrg', 'chgmstr', ...]
```

---

## 8. SQL Generation Strategy

### 8.1 What the LLM Generates vs What Python Generates

| Cell Type | Generator | Reason |
|---|---|---|
| Code list temp tables | Python | Pure mechanical — VALUES list from dataframe |
| Step 1 (surgery index) | LLM + structured prompt | Domain logic: CTE chain, multi-code-system JOIN, ROW_NUMBER deduplication |
| Steps 2–N | LLM + plain prompt | WHERE clause logic varies per protocol (age, cost, gender, DRG, etc.) |
| Attrition waterfall | Python template | Deterministic — just UNION ALL across all step tables |
| Final cohort summary | Python template | Fixed 14-column SELECT — no variation |

### 8.2 The Temp Table Chain

Each step reads exclusively from the previous step's temp table:

```
rhealth_premier_phd.bronze_native_premier_phd.pat  (source)
         ↓
step1_surgery_index          (INC: surgery with date window)
         ↓
step2_age_18_plus            (INC: age filter)
         ↓
step3_hosp_90d               (INC: hospital data contribution)
         ↓
step4_known_gender           (INC: gender M or F)
         ↓
step5_publish_cv             (INC: publish_type = CV)
         ↓
step6_positive_cost          (EXC: remove zero/negative costs)
         ↓
step7_final_cohort           (EXC: remove missing key data)
         ↓
Waterfall + Final Summary    (read from all step tables)
```

**Why temp tables instead of subqueries or CTEs?**  
- Temp tables are materialized — analysts can run cells individually and check counts at each step
- Each cell ends with a count-check SELECT for verification
- Session-scoped — auto-dropped when the Databricks session ends

### 8.3 Window Functions Used

| Function | Use Case |
|---|---|
| `ROW_NUMBER()` | Step 1: select exactly ONE index encounter per patient per surgery category (first admission) |
| `LAG()` | Waterfall: compute drop counts = previous step count − current step count |
| `RANK()` | Available for tied-priority scenarios (e.g., same-day procedures equally valid) |
| `DENSE_RANK()` | Available when no gaps in rank sequence are desired |

---

## 9. Key Design Decisions

### 9.1 No Delta Table Names in UI
Delta table names (`rhealth_premier_phd.bronze_native_premier_phd.pat` etc.) never appear in the Streamlit UI. They are only written into generated SQL. This prevents analysts from accidentally querying raw data outside the intended notebook flow and maintains data governance.

### 9.2 PYTHONDONTWRITEBYTECODE on Windows/OneDrive
The app runs on OneDrive Desktop, which resets file modification timestamps during sync. This causes Python to use stale `.pyc` bytecode that may be months old. `run_app.bat` sets `PYTHONDONTWRITEBYTECODE=1` so Python always reads `.py` source files directly.

### 9.3 PAT Token — Never Committed to Git
`test_endpoint.py` (with PAT fields) is kept as an untracked file. The committed version has empty credential fields. `.gitignore` conventions are followed throughout.

### 9.4 Category-Filtered Code Lists
When multiple procedure categories are in the Excel (e.g., TKA + THA + Bariatric), the app lets analysts select which ones to include. Only selected categories create temp tables and appear in Step 1 SQL. This prevents cross-contamination when a client sends one unified Excel for multiple studies.

### 9.5 Multi-User PAT Support
Any user with a Databricks PAT can use the app. Their email is auto-detected via the SCIM API, and the notebook is saved to their own `/Users/<email>/` directory. No admin configuration needed to add users.

---

## 10. Security & Access Control

| Layer | Mechanism |
|---|---|
| Databricks workspace access | PAT token (Personal Access Token) — each user uses their own |
| LLM access | Same PAT — Model Serving endpoint checks workspace permissions |
| PHD data access | Unity Catalog row/column-level security on the PHD tables — the app cannot override catalog permissions |
| Notebook write access | Users can only write to directories their PAT has write permission on |
| Credential storage | PAT is session-only (in-memory Streamlit session state) — never written to disk or committed to git |
| Source data protection | Delta table names never shown in UI — only written into generated SQL cells |

---

## 11. Environment Setup

### 11.1 Requirements

```
python-docx>=1.1.0    # read .docx protocol files
streamlit>=1.35.0     # web UI
pandas>=2.0.0         # dataframe operations, Excel parsing
openpyxl>=3.1.0       # Excel file reading
requests>=2.31.0      # Databricks REST API calls, LLM HTTP calls
databricks-sdk>=0.28.0  # (available for future Databricks SDK usage)
```

### 11.2 Local Setup

```bash
git clone https://github.com/dBoss0/ads-automation.git
cd ads-automation
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 11.3 Running the App

**Windows (recommended — prevents stale bytecode):**
```
run_app.bat
```

**Or directly:**
```
streamlit run streamlit_app.py
```

### 11.4 One-Time Databricks Setup (per environment)

Click **Setup PHD Data Dictionary Table** in the sidebar:
- Generates a Databricks notebook that creates `premier_phd_data_dictionary_v2_2` Delta table
- Target: `rhealth_datasets_scratch_space.scratch_dbx_prphd_ads_automation_poc`
- Run the pushed notebook once in Databricks to populate the table
- This table is a reference artifact — used for documentation/validation, not required by the SQL generation pipeline

---

## Appendix — File Structure

```
attrition_ex1/
├── streamlit_app.py              # Main Streamlit UI — full user journey
├── run_app.bat                   # Windows launch script (sets PYTHONDONTWRITEBYTECODE=1)
├── requirements.txt              # Python dependencies
├── test_endpoint.py              # Utility to validate Databricks endpoint (no PAT committed)
│
├── ads_automation/
│   ├── __init__.py
│   ├── parser.py                 # .docx protocol parser → attrition steps
│   ├── model_serving.py          # Claude Opus 5 LLM interface + SQL generation
│   ├── notebook_generator.py     # Assembles full Databricks SOURCE notebook
│   ├── databricks_api.py         # Databricks REST API client
│   └── premier_ddl.py            # PHD Data Dictionary + Delta DDL notebook generator
│
├── tests/
│   └── test_attrition_extraction.py   # Unit tests for protocol parser
│
└── TECHNICAL_DOCUMENTATION.md    # This document
```

---

*J&J MedTech — Analytics & Data Sciences | ADS Code Automation Platform v1.0.0*  
*Data Source: Premier PHD (PINC AI™ Healthcare Database v2.2)*  
*Infrastructure: Databricks Unity Catalog + Model Serving (Claude Opus 5)*
