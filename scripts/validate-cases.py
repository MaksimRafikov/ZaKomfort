#!/usr/bin/env python3
"""Validate catalog content.

Source of truth: content/cases/*.json (+ content/site.json). The script checks:
1. Schema of every case JSON (required fields, types, media paths).
2. That generated artifacts are fresh: js/data.js, js/config.js,
   cases/<slug>/index.html, sitemap.xml (run scripts/build-pages.py to fix).
3. Referenced assets exist and are web-optimized; no inbox/ references anywhere.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
CONTENT_DIR = ROOT / "content"
CASES_DIR = CONTENT_DIR / "cases"
DATA_FILE = ROOT / "js" / "data.js"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

ID_RE = re.compile(r"^[a-z0-9-]+$")

# field -> (types, required)
CASE_SCHEMA: dict[str, tuple[tuple[type, ...], bool]] = {
    "order": ((int,), True),
    "id": ((str,), True),
    "title": ((str,), True),
    "address": ((str,), True),
    "areaSqm": ((int, float, type(None)), True),
    "areaLabel": ((str,), True),
    "roomsLabel": ((str,), True),
    "format": ((str,), True),
    "style": ((str,), True),
    "segment": ((str,), True),
    "complex": ((str,), True),
    "tags": ((list,), True),
    "rooms": ((list,), True),
    "hasProjectRender": ((bool,), True),
    "hasVideo": ((bool,), True),
    "cover": ((str,), True),
    "summary": ((str,), True),
    "task": ((str,), True),
    "objectDescription": ((str,), True),
    "workList": ((list,), True),
    "plan": ((dict, type(None)), False),
    "highlights": ((list,), True),
    "clientFit": ((list,), True),
    "gallery": ((list,), True),
    "beforeGallery": ((list,), False),
    "compareGallery": ((list,), False),
    "video": ((dict, type(None)), False),
    "cta": ((dict,), True),
}

CTA_REQUIRED = ("phone", "whatsapp", "telegram", "quiz", "buttonLabel")


def load_build_module():
    spec = importlib.util.spec_from_file_location(
        "build_pages", SCRIPTS_DIR / "build-pages.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def type_names(types: tuple[type, ...]) -> str:
    return "/".join("null" if t is type(None) else t.__name__ for t in types)


def check_media_item(
    item: object, ctx: str, case_id: str, errors: list[str]
) -> str | None:
    """Validate a {src, alt, caption} entry; return src when usable."""
    if not isinstance(item, dict) or not isinstance(item.get("src"), str):
        errors.append(f"{ctx}: expected object with string `src`")
        return None
    src = item["src"]
    if not src.startswith(f"assets/{case_id}/"):
        errors.append(f"{ctx}: src must start with assets/{case_id}/ (got {src!r})")
    if not item.get("alt"):
        errors.append(f"{ctx}: missing `alt` text")
    return src


def validate_case_file(path: Path) -> tuple[list[str], list[str], set[str]]:
    """Returns (errors, warnings, referenced asset paths)."""
    errors: list[str] = []
    warnings: list[str] = []
    assets: set[str] = set()
    name = f"content/cases/{path.name}"

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{name}: invalid JSON ({exc})"], warnings, assets

    if not isinstance(data, dict):
        return [f"{name}: top-level value must be an object"], warnings, assets

    for field, (types, required) in CASE_SCHEMA.items():
        if field not in data:
            if required:
                errors.append(f"{name}: missing required field `{field}`")
            continue
        if not isinstance(data[field], types):
            errors.append(
                f"{name}: field `{field}` must be {type_names(types)}, "
                f"got {type(data[field]).__name__}"
            )
    for field in data:
        if field not in CASE_SCHEMA:
            warnings.append(f"{name}: unknown field `{field}`")

    case_id = data.get("id")
    if isinstance(case_id, str):
        if case_id != path.stem:
            errors.append(f"{name}: id {case_id!r} does not match filename")
        if not ID_RE.fullmatch(case_id):
            errors.append(f"{name}: id must be lowercase kebab-case")
    if errors:
        return errors, warnings, assets
    if not (ROOT / "assets" / case_id).is_dir():
        errors.append(f"{name}: assets/{case_id}/ folder does not exist")

    for field in ("tags", "rooms", "workList", "highlights", "clientFit"):
        values = data.get(field) or []
        bad = [v for v in values if not isinstance(v, str) or not v.strip()]
        if bad:
            errors.append(f"{name}: `{field}` must contain non-empty strings")

    cover = data["cover"]
    if not cover.startswith(f"assets/{case_id}/"):
        errors.append(f"{name}: cover must start with assets/{case_id}/")
    assets.add(cover)

    if not data["gallery"]:
        errors.append(f"{name}: gallery must not be empty")
    for field in ("gallery", "beforeGallery", "compareGallery"):
        for i, item in enumerate(data.get(field) or []):
            src = check_media_item(item, f"{name}: {field}[{i}]", case_id, errors)
            if src:
                assets.add(src)

    plan = data.get("plan")
    if plan:
        src = check_media_item(plan, f"{name}: plan", case_id, errors)
        if src:
            assets.add(src)

    video = data.get("video") or {}
    if data.get("hasVideo"):
        sources = [video.get(k) for k in ("fileUrl", "embedUrl", "externalUrl")]
        if not any(isinstance(s, str) and s for s in sources):
            errors.append(
                f"{name}: hasVideo is true but video has no fileUrl/embedUrl/externalUrl"
            )
    if isinstance(video.get("fileUrl"), str):
        assets.add(video["fileUrl"])
    if isinstance(video.get("poster"), str):
        assets.add(video["poster"])

    cta = data.get("cta") or {}
    for key in CTA_REQUIRED:
        if not isinstance(cta.get(key), str) or not cta[key].strip():
            errors.append(f"{name}: cta.{key} is missing or empty")
    for key, value in cta.items():
        if key in ("phone", "buttonLabel") or not isinstance(value, str):
            continue
        if not value.startswith(("https://", "tel:")):
            errors.append(f"{name}: cta.{key} must be an https:// or tel: link")

    raw = path.read_text(encoding="utf-8")
    if "inbox/" in raw:
        errors.append(f"{name}: forbidden reference to inbox/")

    return errors, warnings, assets


def validate_generated(build, site: dict, cases: list[dict]) -> list[str]:
    """Generated artifacts must match a fresh in-memory build."""
    errors: list[str] = []
    stale_hint = " (run: python scripts/build-pages.py)"

    if not DATA_FILE.exists():
        errors.append("Missing js/data.js" + stale_hint)
    elif DATA_FILE.read_text(encoding="utf-8") != build.build_data_js(cases):
        errors.append("js/data.js is out of date" + stale_hint)

    config_js = ROOT / "js" / "config.js"
    if not config_js.exists():
        errors.append("Missing js/config.js" + stale_hint)
    elif config_js.read_text(encoding="utf-8") != build.build_config_js(site):
        errors.append("js/config.js is out of date" + stale_hint)

    versions = build.asset_versions()
    for c in cases:
        page = ROOT / "cases" / c["id"] / "index.html"
        if not page.is_file():
            errors.append(f'Missing cases/{c["id"]}/index.html' + stale_hint)
        elif page.read_text(encoding="utf-8") != build.build_case_page(
            site, c, versions
        ):
            errors.append(f'cases/{c["id"]}/index.html is out of date' + stale_hint)

    sitemap = ROOT / "sitemap.xml"
    if not sitemap.is_file():
        errors.append("Missing sitemap.xml" + stale_hint)
    else:
        text = sitemap.read_text(encoding="utf-8")
        missing = [
            c["id"] for c in cases if build.case_url(site, c["id"]) not in text
        ]
        if missing:
            errors.append(
                "sitemap.xml misses case URLs: " + ", ".join(missing) + stale_hint
            )

    return errors


def find_inbox_refs(text: str) -> list[str]:
    pattern = re.compile(r'["\'](inbox/[A-Za-z0-9_\-./]+)["\']', re.IGNORECASE)
    return pattern.findall(text)


def find_asset_paths(text: str) -> list[str]:
    pattern = re.compile(
        r'["\'](assets/[A-Za-z0-9_\-./]+\.(?:png|jpg|jpeg|webp|gif|mp4|mov|webm))["\']',
        re.IGNORECASE,
    )
    return pattern.findall(text)


def validate_tips() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    tips_file = ROOT / "js" / "tips-data.js"
    if not tips_file.exists():
        warnings.append("Missing js/tips-data.js (run scripts/process-videos.py).")
        return errors, warnings

    text = tips_file.read_text(encoding="utf-8")
    inbox_refs = sorted(set(find_inbox_refs(text)))
    if inbox_refs:
        errors.append(
            "Found forbidden inbox references in js/tips-data.js: " + ", ".join(inbox_refs)
        )

    asset_paths = find_asset_paths(text)
    missing = [p for p in sorted(set(asset_paths)) if not (ROOT / p).exists()]
    if missing:
        errors.append(
            "Missing assets referenced by js/tips-data.js: "
            + ", ".join(missing[:12])
            + (" ..." if len(missing) > 12 else "")
        )

    ids = re.findall(r'["\']id["\']?\s*:\s*["\']([a-z0-9-]+)["\']', text)
    dupes = sorted({tid for tid in ids if ids.count(tid) > 1})
    if dupes:
        errors.append("Duplicate tip ids in js/tips-data.js: " + ", ".join(dupes))

    return errors, warnings


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not CASES_DIR.is_dir() or not list(CASES_DIR.glob("*.json")):
        errors.append("No case files found in content/cases/*.json")
        return errors, warnings

    all_assets: set[str] = set()
    ids: list[str] = []
    orders: dict[int, list[str]] = {}
    for path in sorted(CASES_DIR.glob("*.json")):
        case_errors, case_warnings, assets = validate_case_file(path)
        errors.extend(case_errors)
        warnings.extend(case_warnings)
        all_assets.update(assets)
        if not case_errors:
            data = json.loads(path.read_text(encoding="utf-8"))
            ids.append(data["id"])
            orders.setdefault(data["order"], []).append(data["id"])

    dupes = sorted({cid for cid in ids if ids.count(cid) > 1})
    if dupes:
        errors.append("Duplicate case ids: " + ", ".join(dupes))
    for order, owners in sorted(orders.items()):
        if len(owners) > 1:
            warnings.append(
                f"Cases share order={order}: " + ", ".join(owners)
            )

    missing_assets = sorted(p for p in all_assets if not (ROOT / p).exists())
    if missing_assets:
        errors.append(
            "Missing assets referenced by content/cases: "
            + ", ".join(missing_assets[:12])
            + (" ..." if len(missing_assets) > 12 else "")
        )

    # Generated artifacts (data.js, case pages, sitemap) must be fresh.
    try:
        build = load_build_module()
        site = build.load_site()
        cases = build.load_cases()
        errors.extend(validate_generated(build, site, cases))
    except SystemExit as exc:
        errors.append(f"build-pages.py failed to load cases: {exc}")
    except Exception as exc:  # noqa: BLE001 - report any build breakage
        errors.append(f"Failed to run build-pages checks: {exc!r}")

    # Web-optimization + responsive-variant checks for referenced images.
    unprotected_images = []
    missing_variants = []
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from media_protect import (
            expected_variants,
            is_protected_image,
            should_skip_assets_path,
        )

        for p in sorted(all_assets):
            full = ROOT / p
            if full.suffix.lower() not in IMAGE_SUFFIXES or not full.exists():
                continue
            if should_skip_assets_path(full, ROOT / "assets"):
                continue
            if not is_protected_image(full):
                unprotected_images.append(p)
            if any(not v.exists() for v in expected_variants(full)):
                missing_variants.append(p)
    except ImportError:
        pass
    if unprotected_images:
        warnings.append(
            "Unoptimized images (run process-assets.py --optimize-all): "
            + ", ".join(unprotected_images[:8])
            + (" ..." if len(unprotected_images) > 8 else "")
        )
    if missing_variants:
        warnings.append(
            "Images without responsive variants (run process-assets.py --optimize-all): "
            + ", ".join(missing_variants[:8])
            + (" ..." if len(missing_variants) > 8 else "")
        )

    tip_errors, tip_warnings = validate_tips()
    errors.extend(tip_errors)
    warnings.extend(tip_warnings)

    return errors, warnings


def main() -> int:
    errors, warnings = validate()

    if errors:
        print("VALIDATION_FAILED")
        for e in errors:
            print(f"- ERROR: {e}")
        for w in warnings:
            print(f"- WARN: {w}")
        return 1

    print("VALIDATION_OK")
    for w in warnings:
        print(f"- WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
