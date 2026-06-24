#!/usr/bin/env python3
"""Check left-edge alignment of headings vs logo text and content blocks."""

from playwright.sync_api import sync_playwright

PAGES = [
    ("index", "http://127.0.0.1:8765/index.html", ".hero h1", ".filters"),
    ("tips", "http://127.0.0.1:8765/tips.html", ".hero h1", ".filters"),
    ("404", "http://127.0.0.1:8765/404.html", ".page-404 h1", ".page-404 .lead"),
    ("case", "http://127.0.0.1:8765/case.html?id=pervomaysky-44", ".case-hero h1", ".section h2"),
]
WIDTHS = [1440, 768, 375]
TOL = 1.5


def check(page, h_sel, b_sel):
    return page.evaluate(
        """(args) => {
        const [hSel, bSel] = args;
        const logo = document.querySelector('.logo__img');
        const h1 = document.querySelector(hSel);
        const block = document.querySelector(bSel);
        if (!logo || !h1 || !block) return { ok: false, reason: 'missing' };
        const logoRect = logo.getBoundingClientRect();
        const textX = logoRect.left + logoRect.width * (223 / 801);
        const h1Left = h1.getBoundingClientRect().left;
        const blockLeft = block.getBoundingClientRect().left;
        return {
            ok: true,
            textX,
            h1Left,
            blockLeft,
            h1Delta: h1Left - textX,
            blockDelta: blockLeft - textX,
            h1BlockDelta: h1Left - blockLeft,
        };
    }""",
        [h_sel, b_sel],
    )


def main():
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in WIDTHS:
            page = browser.new_page(viewport={"width": width, "height": 900})
            for name, url, h_sel, b_sel in PAGES:
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(400)
                data = check(page, h_sel, b_sel)
                if not data.get("ok"):
                    failed.append((name, width, "missing elements"))
                    print(f"FAIL {name:5} {width:4}px | missing elements")
                    continue
                ok = (
                    abs(data["h1Delta"]) <= TOL
                    and abs(data["blockDelta"]) <= TOL
                    and abs(data["h1BlockDelta"]) <= TOL
                )
                status = "OK" if ok else "FAIL"
                print(
                    f"{status} {name:5} {width:4}px | "
                    f"h1 dText={data['h1Delta']:6.1f} "
                    f"block dText={data['blockDelta']:6.1f} "
                    f"h1-block={data['h1BlockDelta']:6.1f}"
                )
                if not ok:
                    failed.append((name, width, data))
            page.close()
        browser.close()

    print("---")
    if failed:
        raise SystemExit(f"FAILED: {len(failed)} checks")
    print("ALL OK")


if __name__ == "__main__":
    main()
