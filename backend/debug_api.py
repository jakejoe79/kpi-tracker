"""Simple CLI to exercise backend timer endpoints against a live server.
Usage:
    python debug_api.py <base_url> [date]

Example:
    python debug_api.py https://kpi-tracker.onrender.com 2026-03-04

The script will call /timer/start, /timer (status), /timer/stop and print JSON replies.
"""
import sys
import requests
from datetime import date


def call(endpoint, base, data=None, method="get"):
    url = f"{base.rstrip('/')}/api{endpoint}"
    try:
        if method == "get":
            r = requests.get(url, timeout=10)
        elif method == "post":
            r = requests.post(url, json=data, timeout=10)
        else:
            r = requests.request(method, url, json=data, timeout=10)
    except Exception as e:
        print(f"{method.upper()} {url} failed: {e}")
        return None
    print(f"{method.upper()} {endpoint} -> {r.status_code}")
    try:
        print(r.json())
    except Exception:
        print(r.text)
    return r


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_api.py <base_url> [date]")
        sys.exit(1)
    base = sys.argv[1].rstrip('/')
    entry_date = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()

    print(f"Testing timer endpoints for {entry_date} on {base}")
    call(f"/entries/{entry_date}/timer/start", base, method="post")
    call(f"/entries/{entry_date}/timer", base, method="get")
    call(f"/entries/{entry_date}/timer/stop", base, method="post")
    call(f"/entries/{entry_date}", base, method="get")


if __name__ == '__main__':
    main()
