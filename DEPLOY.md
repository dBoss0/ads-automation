# Databricks Apps — Deployment Guide

**App name:** `jnj-medtech-code-automation`  
**Workspace:** `https://dbc-db3d8a4e-f2cf.cloud.databricks.com`

---

## Pre-requisites

| Requirement | Notes |
|---|---|
| Databricks Premium tier | Required for Databricks Apps |
| Databricks CLI v0.200+ | New CLI (not legacy `databricks-cli` pip package) |
| Python 3.10+ | Already in your environment |
| Your PAT token | Used to authenticate CLI |
| GitHub repo access | App syncs from source in workspace |

---

## Step 1 — Install the Databricks CLI

```powershell
# Windows — download the installer
winget install Databricks.DatabricksCLI
```

Or via pip (new CLI):
```powershell
pip install databricks-cli
```

Verify:
```powershell
databricks --version
# Should show: 0.2xx.x or higher
```

---

## Step 2 — Authenticate CLI to the workspace

```powershell
databricks configure --host https://dbc-db3d8a4e-f2cf.cloud.databricks.com --token
```

When prompted, paste your PAT token. This writes `~/.databrickscfg`.

Verify:
```powershell
databricks current-user me
# Should return your Databricks user profile JSON
```

---

## Step 3 — Validate the bundle

From inside the project folder (`attrition_ex1`):

```powershell
databricks bundle validate
```

Expected output: `Bundle configuration is valid.`

If you see schema errors, they will point to exact lines in `databricks.yml`.

---

## Step 4 — Deploy the bundle (Dev)

```powershell
databricks bundle deploy --target dev
```

This uploads all source files under `source_code_path: .` to the Databricks workspace.  
Files uploaded: `streamlit_app.py`, `app.yaml`, `ads_automation/`, `requirements.txt`, etc.

Files excluded by `.gitignore` are NOT uploaded (so `test_endpoint.py` with your PAT stays local).

---

## Step 5 — Start the app

```powershell
databricks bundle run jnj-medtech-code-automation --target dev
```

After ~60 seconds the CLI will print the app URL:

```
App URL: https://jnj-medtech-code-automation-<workspace-hash>.databricksapps.com
```

Open that URL in any browser — no Streamlit local install needed.

---

## Step 6 — Give access to PNV1@ITS.JNJ.com

In the Databricks workspace UI:

1. Go to **Compute → Apps** (left sidebar)
2. Click **jnj-medtech-code-automation**
3. Click the **Permissions** tab
4. Click **Add permission** → search for `PNV1@ITS.JNJ.com` → grant **Can Use** role
5. Click **Save**

PNV1 can now open the same app URL without needing a PAT or local Python setup.  
They authenticate via their Databricks SSO (JNJ OKTA) automatically.

---

## Step 7 — Production deploy (when ready)

```powershell
databricks bundle deploy --target prod
databricks bundle run jnj-medtech-code-automation --target prod
```

Prod mode disables auto-recreate and enforces strict permission policies.

---

## How the app works in Databricks Apps context

| What | How |
|---|---|
| PAT token | NOT needed — Databricks Apps injects `DATABRICKS_TOKEN` automatically |
| Notebook path | Auto-detected from injected token via SCIM API `/api/2.0/preview/scim/v2/Me` |
| Model Serving | `CAN_QUERY` on `databricks-claude-opus-5` is declared in `app.yaml → resources` |
| `PYTHONDONTWRITEBYTECODE` | Set in `app.yaml → env` — no stale `.pyc` in container |
| Logo | Falls back to web URL when local `*.png` not present (already handled in code) |

---

## Checking app status / logs

```powershell
# List all apps
databricks apps list

# Get app details and status
databricks apps get jnj-medtech-code-automation

# View app logs (last 100 lines)
databricks apps logs jnj-medtech-code-automation
```

---

## Updating the app after code changes

```powershell
# Redeploy with latest code
databricks bundle deploy --target dev

# The running app picks up new code automatically (hot reload)
# If it doesn't restart manually:
databricks apps restart jnj-medtech-code-automation
```

---

## Teardown (if needed)

```powershell
databricks bundle destroy --target dev
```

This removes the app and all uploaded files from the workspace — local files are unaffected.

---

## Notes

- `app.py` in the root is an old CLI entry point — it is NOT used by Databricks Apps. The entry point is `app.yaml → command`, which runs `streamlit_app.py` directly.
- `.streamlit/` is in `.gitignore` and will not be uploaded. Streamlit server config is handled entirely via command-line flags in `app.yaml`.
- The `databricks.yml` `bundle_version` field has been removed — the current DAB spec uses `bundle:` directly without a version prefix.
