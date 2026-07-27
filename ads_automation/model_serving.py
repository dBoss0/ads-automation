"""
Databricks Model Serving integration for AI-assisted SQL generation.

Plug in your endpoint URLs below once you have them from your Databricks workspace.
Both Claude and GPT endpoints use the same OpenAI-compatible chat completions API.
"""

import json
import requests

# ─── Configure your model serving endpoint URLs here ─────────────────────────
CLAUDE_ENDPOINT_URL = ""   # e.g. https://dbc-xxxx.cloud.databricks.com/serving-endpoints/claude-endpoint/invocations
GPT_ENDPOINT_URL    = ""   # e.g. https://dbc-xxxx.cloud.databricks.com/serving-endpoints/gpt-endpoint/invocations
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Databricks SQL expert specializing in Premier PHD (PINC AI Healthcare Database) analytics.
You write Databricks SQL that runs on a SQL Warehouse (not Spark SQL — use ANSI SQL syntax).
Always use fully-qualified table names from rhealth_premier_phd.bronze_native_premier_phd.
Key tables: patdemo (pat), paticd_proc (icd_proc), paticd_diag (icd_diag), patcpt, prov_enrollment, providers.
Return ONLY the SQL body (no markdown fences, no explanations). The result must be a CREATE OR REPLACE TEMPORARY TABLE statement."""

_DICT_CONTEXT = """
Premier PHD key fields:
patdemo: pat_key, medrec_key, admit_date, discharge_date, disc_mon, prov_id, i_o_ind, pat_type,
  ms_drg, age, gender (M/F/U), race, adm_type, disc_status, los, pat_cost, pat_charges,
  publish_type (CP/CV), std_payor
paticd_proc: pat_key, icd_version (9/10), icd_code, icd_pri_sec (P=Principal/S=Secondary), proc_date
paticd_diag: pat_key, icd_version (9/10), icd_code, icd_pri_sec (A=Admitting/P=Principal/S=Secondary), icd_poa
patcpt: pat_key, cpt_code, cpt_pos, proc_date
prov_enrollment: prov_id, disc_mon, ip_max_dx_date, ip_proj_wgt  [join on prov_id + disc_mon]
providers: prov_id, urban_rural, teaching, beds_grp, prov_region, cost_type
"""


def _call_endpoint(url: str, token: str, user_message: str, max_tokens: int = 1500) -> str:
    """Call an OpenAI-compatible Databricks model serving endpoint."""
    payload = {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_step_sql(
    step_num: int,
    description: str,
    prev_table: str,
    target_table: str,
    token: str,
    prefer_claude: bool = True,
) -> str:
    """
    Call the model serving endpoint to generate SQL for an attrition step.
    Returns the full CREATE OR REPLACE TEMPORARY TABLE ... AS SELECT ... SQL.
    Falls back gracefully to a TODO comment if endpoints are not configured.

    Args:
        step_num:      Step number (1-based).
        description:   Attrition step description text.
        prev_table:    Source temp table from the prior step.
        target_table:  Name of the temp table to create.
        token:         Databricks PAT token.
        prefer_claude: If True, try Claude endpoint first; otherwise try GPT first.
    """
    primary_url   = CLAUDE_ENDPOINT_URL if prefer_claude else GPT_ENDPOINT_URL
    secondary_url = GPT_ENDPOINT_URL    if prefer_claude else CLAUDE_ENDPOINT_URL

    if not primary_url and not secondary_url:
        return _fallback_sql(target_table, description)

    prompt = _build_prompt(step_num, description, prev_table, target_table)

    for url in [u for u in [primary_url, secondary_url] if u]:
        try:
            sql = _call_endpoint(url, token, prompt)
            if sql and "SELECT" in sql.upper():
                return sql
        except Exception:
            continue

    return _fallback_sql(target_table, description)


def _build_prompt(step_num: int, description: str, prev_table: str, target_table: str) -> str:
    return f"""{_DICT_CONTEXT}

Write a Databricks SQL attrition step.

Step number: {step_num}
Step description: "{description}"
Source table: {prev_table}  (contains pat_key, medrec_key, prov_id, disc_mon, surgery_category; already filtered by all prior steps)
Target table: {target_table}

Write:
  CREATE OR REPLACE TEMPORARY TABLE {target_table} AS
  SELECT <columns>
  FROM {prev_table} pat
  JOIN rhealth_premier_phd.bronze_native_premier_phd.<relevant_table> ...
  WHERE <filter matching the step description>;

Include all columns from {prev_table} in the SELECT (use pat.*).
Use only Premier PHD tables and the exact field names listed above.
Return only the SQL — no markdown, no explanation."""


def _fallback_sql(target_table: str, description: str) -> str:
    return (
        f"CREATE OR REPLACE TEMPORARY TABLE {target_table} AS\n"
        f"SELECT *\n"
        f"FROM prev_step_table;\n"
        f"-- TODO: Implement filter for: {description}\n"
        f"-- Configure CLAUDE_ENDPOINT_URL or GPT_ENDPOINT_URL in ads_automation/model_serving.py"
    )


def is_configured() -> bool:
    """Return True if at least one model serving endpoint is configured."""
    return bool(CLAUDE_ENDPOINT_URL or GPT_ENDPOINT_URL)
