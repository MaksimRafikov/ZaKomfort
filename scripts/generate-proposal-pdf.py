#!/usr/bin/env python3
"""Generate client proposal PDF from docs/client-proposal.html."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "client-proposal.html"
OUTPUT = ROOT / "docs" / "Коммерческое-предложение-ИИ-студия.pdf"


def main() -> int:
    if not HTML.is_file():
        print(f"ERROR: HTML not found: {HTML}", file=sys.stderr)
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Installing playwright...", file=sys.stderr)
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        from playwright.sync_api import sync_playwright

    uri = HTML.resolve().as_uri()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(uri, wait_until="networkidle")
        page.pdf(
            path=str(OUTPUT),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()

    print(f"PDF_OK: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
