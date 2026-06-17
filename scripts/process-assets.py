#!/usr/bin/env python3
"""Import inbox photos into assets/ with watermark and web optimization."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from media_protect import (
    IMAGE_SUFFIXES,
    natural_sort_key,
    output_path_for,
    protect_image_file,
    iter_case_images,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"


def import_inbox_folder(
    source_dir: Path,
    case_id: str,
    *,
    prefix: str,
    start_index: int,
    force: bool,
) -> list[Path]:
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    case_dir = ASSETS_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    sources = sorted(
        [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES],
        key=natural_sort_key,
    )
    if not sources:
        raise RuntimeError(f"No images found in {source_dir}")

    created: list[Path] = []
    index = start_index
    for source in sources:
        ext = ".png" if prefix == "plan" else ".jpg"
        target = case_dir / f"{prefix}-{index}{ext}"
        shutil.copy2(source, target)
        final = protect_image_file(target, force=True) or target
        created.append(final)
        index += 1
    return created


def sync_data_js(replacements: dict[str, str]) -> int:
    data_file = ROOT / "js" / "data.js"
    text = data_file.read_text(encoding="utf-8")
    applied = 0
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if old in text:
            text = text.replace(old, new)
            applied += 1
    if applied:
        data_file.write_text(text, encoding="utf-8")
    return applied


def protect_assets(
    *,
    case_id: str | None,
    force: bool,
    sync_data: bool = False,
) -> tuple[int, int, dict[str, str]]:
    if case_id:
        roots = [ASSETS_DIR / case_id]
    else:
        roots = [ASSETS_DIR]

    changed = 0
    skipped = 0
    replacements: dict[str, str] = {}
    for root in roots:
        for path in list(iter_case_images(root)):
            before = path.relative_to(ROOT).as_posix()
            expected = output_path_for(path).relative_to(ROOT).as_posix()
            result = protect_image_file(path, force=force)
            if result:
                changed += 1
                after = result.relative_to(ROOT).as_posix()
                print(f"protected: {after}")
                if before != after:
                    replacements[before] = after
                elif before != expected and expected in replacements.values():
                    pass
            else:
                skipped += 1

    if sync_data and replacements:
        count = sync_data_js(replacements)
        print(f"Updated {count} path(s) in js/data.js")

    return changed, skipped, replacements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watermark and optimize catalog images in assets/ (and import from inbox/)."
    )
    parser.add_argument("--case", help="Case id folder under assets/, e.g. na-uspenskoy")
    parser.add_argument(
        "--from",
        dest="source",
        help="Import images from inbox subfolder into assets/<case>/",
    )
    parser.add_argument(
        "--prefix",
        default="after",
        help="Filename prefix for imported images (after, before, compare, plan)",
    )
    parser.add_argument("--start", type=int, default=1, help="Starting index for imported files")
    parser.add_argument(
        "--protect-all",
        action="store_true",
        help="Watermark all case images in assets/ (skips assets/brand)",
    )
    parser.add_argument(
        "--recompress-all",
        action="store_true",
        help="Re-optimize all images (JPG for photos, sync js/data.js paths)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-apply watermark even if file is already protected",
    )
    parser.add_argument(
        "--sync-data",
        action="store_true",
        help="Update js/data.js when image paths change to .jpg",
    )
    args = parser.parse_args()

    if args.recompress_all:
        args.force = True
        args.sync_data = True

    if args.source:
        if not args.case:
            print("--case is required with --from", file=sys.stderr)
            return 1
        source_dir = Path(args.source)
        if not source_dir.is_absolute():
            source_dir = ROOT / source_dir
        try:
            created = import_inbox_folder(
                source_dir,
                args.case,
                prefix=args.prefix,
                start_index=args.start,
                force=True,
            )
        except (FileNotFoundError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        for path in created:
            print(f"imported: {path.relative_to(ROOT)}")
        print(f"Imported {len(created)} file(s) into assets/{args.case}/")
        return 0

    if args.protect_all or args.case or args.recompress_all:
        changed, skipped, replacements = protect_assets(
            case_id=args.case,
            force=args.force,
            sync_data=args.sync_data,
        )
        print(f"Done. Protected: {changed}, skipped: {skipped}, path updates: {len(replacements)}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
