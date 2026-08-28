#!/usr/bin/env python3
"""Small post-deploy smoke test for Gatehouse."""

import argparse

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    headers = {"X-Workspace-ID": "demo", "X-Actor": "smoke", "X-Role": "approver"}
    with httpx.Client(base_url=base, timeout=5.0) as client:
        client.get("/healthz").raise_for_status()
        client.get("/readyz").raise_for_status()
        overview = client.get("/api/v1/overview", headers=headers)
        overview.raise_for_status()
        requests = client.get("/api/v1/access-requests", headers=headers)
        requests.raise_for_status()
        print({"health": "ok", "pending": overview.json()["pending"], "requests": len(requests.json())})


if __name__ == "__main__":
    main()
