"""
Run this script to validate a Databricks model serving endpoint.

Usage:
    python test_endpoint.py
"""

import requests
import json

# ── Fill these in ─────────────────────────────────────────────────────────────
ENDPOINT_URL = ""   # e.g. https://dbc-xxx.cloud.databricks.com/serving-endpoints/my-model/invocations
PAT_TOKEN    = ""   # your Databricks PAT (same one used in the app)
# ─────────────────────────────────────────────────────────────────────────────


def test_endpoint(url: str, token: str) -> None:
    if not url or not token:
        print("ERROR: Fill in ENDPOINT_URL and PAT_TOKEN at the top of this file.")
        return

    print(f"\nTesting endpoint: {url}")
    print("-" * 60)

    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",   "content": "Reply with exactly: ENDPOINT OK"},
        ],
        "max_tokens": 20,
    }

    try:
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=30,
        )

        print(f"HTTP status : {resp.status_code}")

        if resp.status_code == 200:
            data = resp.json()
            # OpenAI-compatible response
            reply = (
                data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
            )
            model = data.get("model", "unknown")
            print(f"Model       : {model}")
            print(f"Reply       : {reply}")
            print("\nRESULT: ENDPOINT IS WORKING")
        else:
            print(f"Response    : {resp.text[:500]}")
            print("\nRESULT: ENDPOINT FAILED")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection error — check the URL\n{e}")
    except requests.exceptions.Timeout:
        print("Timeout — endpoint took > 30s to respond")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    test_endpoint(ENDPOINT_URL, PAT_TOKEN)
