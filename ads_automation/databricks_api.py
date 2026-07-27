import base64
import os
import requests

# When running as a Databricks App, host + token are injected as env vars.
# Falls back to the values passed explicitly (sidebar PAT for local dev).
_ENV_HOST  = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
_ENV_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")


def resolve_host(host: str) -> str:
    return (_ENV_HOST or host).rstrip("/")


def resolve_token(token: str) -> str:
    return _ENV_TOKEN or token


def save_notebook(host: str, token: str, path: str, content: str) -> dict:
    """Push a SOURCE-format SQL notebook to Databricks workspace."""
    h, t = resolve_host(host), resolve_token(token)
    url = f"{h}/api/2.0/workspace/import"
    payload = {
        "path": path,
        "format": "SOURCE",
        "language": "SQL",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "overwrite": True,
    }
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {t}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json() if resp.text.strip() else {}


def get_notebook_url(host: str, path: str) -> str:
    """Return a clickable Databricks workspace URL for the given notebook path."""
    return f"{resolve_host(host)}/#workspace{path}"


def get_current_user(host: str, token: str) -> str:
    """Return the userName of the current user via SCIM API."""
    h, t = resolve_host(host), resolve_token(token)
    url = f"{h}/api/2.0/preview/scim/v2/Me"
    resp = requests.get(url, headers={"Authorization": f"Bearer {t}"}, timeout=15)
    resp.raise_for_status()
    return resp.json().get("userName", "")


def is_databricks_app() -> bool:
    """True when running inside a Databricks App (env vars are present)."""
    return bool(_ENV_HOST and _ENV_TOKEN)
