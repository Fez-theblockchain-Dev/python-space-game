"""
Smoke-test script for the Space Cowboys Store (Django server).

Checks every page and API endpoint for expected status codes and
response shapes.  Run it while the Django server is up:

    python manage.py runserver 8080          # start server first
    python -m tests_debug_log.test_django_server   # then run this

You can override the base URL with an env var:

    SERVER_URL=http://127.0.0.1:9000 python -m tests_debug_log.test_django_server
"""
import json
import os
import sys
import requests

BASE_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8080").rstrip("/")

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"

results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = ""):
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {name}" + (f"  — {detail}" if detail else ""))
    results.append((name, ok, detail))


def try_get(path: str, *, name: str, expect_status: int = 200, json_key: str | None = None):
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=10, allow_redirects=False)
    except requests.ConnectionError:
        record(name, False, f"Connection refused → {url}")
        return None
    except Exception as exc:
        record(name, False, str(exc))
        return None

    ok = resp.status_code == expect_status
    detail = f"HTTP {resp.status_code}"

    if ok and json_key:
        try:
            data = resp.json()
            if json_key not in data:
                ok = False
                detail += f" (missing key '{json_key}')"
            else:
                detail += f" ✓ '{json_key}' present"
        except ValueError:
            ok = False
            detail += " (not valid JSON)"

    record(name, ok, detail)
    return resp


def try_post(path: str, body: dict, *, name: str, expect_status: int = 200, json_key: str | None = None):
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.post(url, json=body, timeout=10, allow_redirects=False)
    except requests.ConnectionError:
        record(name, False, f"Connection refused → {url}")
        return None
    except Exception as exc:
        record(name, False, str(exc))
        return None

    ok = resp.status_code == expect_status
    detail = f"HTTP {resp.status_code}"

    if ok and json_key:
        try:
            data = resp.json()
            if json_key not in data:
                ok = False
                detail += f" (missing key '{json_key}')"
            else:
                detail += f" ✓ '{json_key}' present"
        except ValueError:
            ok = False
            detail += " (not valid JSON)"

    record(name, ok, detail)
    return resp


def main():
    print(f"\n{'=' * 60}")
    print(f"  Space Cowboys Store — Server Health Check")
    print(f"  Target: {BASE_URL}")
    print(f"{'=' * 60}\n")

    # ------------------------------------------------------------------
    # 1. Connectivity
    # ------------------------------------------------------------------
    print("▸ Connectivity")
    try:
        resp = requests.get(BASE_URL + "/", timeout=5)
        record("Server is reachable", True, f"HTTP {resp.status_code}")
    except requests.ConnectionError:
        record("Server is reachable", False, f"Cannot connect to {BASE_URL}")
        print(f"\n  Server is not running.  Start it first:\n")
        print(f"    python manage.py runserver 8080\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Page endpoints
    # ------------------------------------------------------------------
    print("\n▸ Pages")
    try_get("/", name="Landing page (GET /)")
    try_get("/shop/", name="Shop page (GET /shop/)")
    try_get("/shop/gold_100/", name="Package detail (GET /shop/gold_100/)")
    try_get("/shop/nonexistent_pkg/", name="Invalid package redirects",
            expect_status=302)
    try_get("/payment/success/", name="Payment success page")
    try_get("/payment/cancelled/", name="Payment cancelled page")

    # ------------------------------------------------------------------
    # 3. JSON API — read-only
    # ------------------------------------------------------------------
    print("\n▸ JSON API (read-only)")
    resp = try_get("/api/packages/", name="GET /api/packages/", json_key="packages")
    if resp and resp.ok:
        pkgs = resp.json().get("packages", [])
        record(
            "  └ Package count",
            len(pkgs) > 0,
            f"{len(pkgs)} package(s) returned",
        )

    try_get("/api/wallet/balance/", name="GET /api/wallet/balance/",
            json_key="gold_coins")
    try_get("/api/transactions/", name="GET /api/transactions/",
            json_key="transactions")

    # ------------------------------------------------------------------
    # 4. POST endpoints — validation checks (no real Stripe calls)
    # ------------------------------------------------------------------
    print("\n▸ POST endpoint validation")
    try_post(
        "/api/create-payment-intent/",
        {"package_id": "INVALID"},
        name="PaymentIntent rejects invalid package",
        expect_status=400,
        json_key="error",
    )
    try_post(
        "/api/create-checkout-session/",
        {"package_id": "INVALID"},
        name="Checkout rejects invalid package",
        expect_status=400,
        json_key="error",
    )
    try_post(
        "/api/create-checkout-session/",
        {"package_id": "gold_100", "quantity": 0},
        name="Checkout rejects quantity=0",
        expect_status=400,
        json_key="error",
    )
    try_post(
        "/api/create-checkout-session/",
        {"package_id": "gold_100", "quantity": 100},
        name="Checkout rejects quantity>99",
        expect_status=400,
        json_key="error",
    )

    # ------------------------------------------------------------------
    # 5. Method-not-allowed guards
    # ------------------------------------------------------------------
    print("\n▸ Method guards")
    try_get("/api/create-payment-intent/", name="GET → PaymentIntent (expect 405)",
            expect_status=405)
    try_get("/api/create-checkout-session/", name="GET → Checkout (expect 405)",
            expect_status=405)
    try_get("/api/stripe-webhook/", name="GET → Webhook (expect 405)",
            expect_status=405)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  ({failed} failed)")
    else:
        print(f"  — all green!")
    print(f"{'=' * 60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
