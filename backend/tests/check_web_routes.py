"""Route coverage checker for web routes.

Fails if any web route has no corresponding test function.
Run: pytest tests/check_web_routes.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.routers.web import router

# Regex patterns to extract route path and method from test function name
# e.g. test_delete_reading -> matches "delete" and "reading"
# e.g. test_readings_page_with_data -> matches "readings_page"
# e.g. test_create_readings_batch -> matches "create_readings_batch"

TEST_FILE = Path(__file__).parent / "api" / "test_web.py"

# Route paths that are intentionally not tested (login page, root, etc. are GET pages)
# Add paths here if they're covered by a broader test (e.g. dashboard page test covers all chart data)
EXCLUDED_PATHS: set[str] = set()


def _extract_web_routes() -> list[tuple[str, str]]:
    """Return list of (method, path) for all routes in the web router."""
    routes = []
    for route in router.routes:
        if not hasattr(route, "methods") or not hasattr(route, "path"):
            continue
        for method in route.methods:
            if method in ("HEAD", "OPTIONS"):
                continue
            routes.append((method.upper(), route.path))
    return routes


def _extract_tested_routes() -> set[tuple[str, str]]:
    """Parse test_web.py and extract which routes are tested based on test names."""
    if not TEST_FILE.exists():
        return set()

    content = TEST_FILE.read_text()
    # Find all test function names
    test_names = re.findall(r"def (test_\w+)\(", content)

    tested: set[tuple[str, str]] = set()

    for name in test_names:
        name = name.removeprefix("test_")

        # Map test name patterns to route methods
        if name.startswith("login_") or name == "login_page":
            if "success" in name or "empty" in name or "invalid" in name:
                tested.add(("POST", "/web/login"))
            else:
                tested.add(("GET", "/web/login"))
        elif name.startswith("root_") or name == "root_no_family":
            tested.add(("GET", "/web/"))
        elif name.startswith("logout"):
            tested.add(("GET", "/web/logout"))
        elif name.startswith("create_family"):
            tested.add(("POST", "/web/families"))
        elif name.startswith("dashboard"):
            tested.add(("GET", "/web/families/{family_id}/dashboard"))
        elif name.startswith("export"):
            if "reading" in name:
                tested.add(("GET", "/web/families/{family_id}/export/readings.csv"))
            elif "book" in name:
                tested.add(("GET", "/web/families/{family_id}/export/books.csv"))
        elif "reading" in name:
            if "filter" in name:
                tested.add(("GET", "/web/families/{family_id}/readings"))
            elif "page" in name or "empty" in name or "with_data" in name:
                tested.add(("GET", "/web/families/{family_id}/readings"))
            elif name.startswith("create_reading") and "batch" not in name:
                tested.add(("POST", "/web/families/{family_id}/readings"))
            elif name.startswith("create_readings_batch"):
                tested.add(("POST", "/web/families/{family_id}/readings/batch"))
            elif name.startswith("finish_readings_batch"):
                tested.add(("POST", "/web/families/{family_id}/readings/batch/finish"))
            elif name.startswith("delete_reading"):
                tested.add(("DELETE", "/web/families/{family_id}/readings/{reading_id}"))
            elif name.startswith("patch_reading"):
                tested.add(("PATCH", "/web/families/{family_id}/readings/{reading_id}"))
        elif "book" in name:
            if "page" in name or "empty" in name or "with_data" in name:
                tested.add(("GET", "/web/families/{family_id}/books"))
            elif name.startswith("create_book") and "batch" not in name:
                tested.add(("POST", "/web/families/{family_id}/books"))
            elif name.startswith("create_books_batch"):
                tested.add(("POST", "/web/families/{family_id}/books/batch"))
            elif name.startswith("delete_book"):
                tested.add(("DELETE", "/web/families/{family_id}/books/{book_id}"))
            elif name.startswith("patch_book"):
                tested.add(("PATCH", "/web/families/{family_id}/books/{book_id}"))
        elif "member" in name:
            if "page" in name:
                tested.add(("GET", "/web/families/{family_id}/members"))
            elif name.startswith("create_member"):
                tested.add(("POST", "/web/families/{family_id}/members"))
            elif name.startswith("delete_member"):
                tested.add(("DELETE", "/web/families/{family_id}/members/{member_id}"))

    return tested


def test_all_web_routes_have_tests():
    """Every web route must have at least one corresponding test."""
    all_routes = _extract_web_routes()
    tested = _extract_tested_routes()

    missing = []
    for method, path in all_routes:
        if (method, path) not in tested and path not in EXCLUDED_PATHS:
            missing.append(f"  {method} {path}")

    if missing:
        pytest.fail(
            "The following web routes have NO test coverage:\n"
            + "\n".join(sorted(missing))
            + "\n\nAdd a test function in tests/api/test_web.py that matches the route."
        )


def test_post_patch_delete_redirects_use_303():
    """All POST/PATCH/DELETE handlers that redirect should use 303, not 302.

    302 tells the browser to replay the original method (e.g. DELETE → DELETE),
    causing infinite loops and 405 errors. 303 forces a GET follow-up.
    """
    web_py = Path(__file__).parent.parent / "app" / "routers" / "web.py"
    if not web_py.exists():
        pytest.skip("web.py not found")

    content = web_py.read_text()
    # Find RedirectResponse calls in POST/PATCH/DELETE handler functions
    lines = content.splitlines()

    in_form_handler = False
    violations = []

    for i, line in enumerate(lines, 1):
        # Detect function definitions
        if re.match(r"@router\.(post|patch|delete)\(", line):
            in_form_handler = True
        elif line.startswith("def ") and "htmx" in line or "batch" in line or "_htmx" in line:
            in_form_handler = True
        elif re.match(r"^def \w+\(", line) and not in_form_handler:
            in_form_handler = False
        elif re.match(r"^@router\.get\(", line):
            in_form_handler = False

        if in_form_handler and "RedirectResponse" in line and "HTTP_302_FOUND" in line:
            violations.append(f"  line {i}: {line.strip()}")

    if violations:
        pytest.fail(
            "POST/PATCH/DELETE handlers must use 303 (HTTP_303_SEE_OTHER), not 302:\n"
            + "\n".join(violations)
            + "\n\n302 causes browsers to replay DELETE/POST as the same method, causing 405 loops."
        )
