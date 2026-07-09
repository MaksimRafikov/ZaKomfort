#!/usr/bin/env python3
"""Import inbox photos into assets/ with web optimization (resize + compress)."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from media_protect import (
    IMAGE_SUFFIXES,
    natural_sort_key,
    optimize_image_file,
    output_path_for,
    iter_case_images,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
INBOX_DIR = ROOT / "inbox"
SOURCE_SUFFIXES = IMAGE_SUFFIXES | {".heic", ".heif"}

CASE_INBOX_MAP: dict[str, str] = {
    "na-uspenskoy": "zhk-na-uspenskoy",
    "kondi-nova": "zhk-kondi-nova",
    "kvartal-entuziastov-2": "zhk-kvartal-entuziastov-2",
    "novaland": "zhk-novaland",
    "trilogiya-120": "zhk-trilogiya",
    "kvartal-entuziastov": "zhk-kvartal-entuziastov",
    "tau-house-2": "zhk-tau-house-2",
    "green-park-93": "zhk-green-park",
    "nesterovsky-49": "zhk-nesterovsky",
    "imperial-3k": "zhk-imperial",
    "tau-house-3k": "zhk-tau-house",
    "pervomaysky-44": "zhk-pervomaysky",
    "venskiy-les": "zhk-venskiy-les",
}

INBOX_PREFIX_DIRS = {
    "after": "01-photos-after",
    "before": "02-photos-before",
    "compare": "03-compare",
    "plan": "03-plan",
}

DEFAULT_FIDAN_ROOT = Path(
    r"C:\Users\Пользователь\Desktop\Студия ИИ-видео\Фидан - За Комфортом"
)

FIDAN_FOLDER_MAP: dict[str, str] = {
    "kondi-nova": "Конди Нова",
    "kvartal-entuziastov-2": "Квартал Энтузиастов 2",
    "novaland": "Новаленд",
    "green-park-93": "Грин Парк",
    "nesterovsky-49": "Нестеровский",
    "pervomaysky-44": "Первомайский",
}

FIDAN_PLAN_FILES: dict[str, str] = {
    "kondi-nova": "Схема пнг.png",
    "kvartal-entuziastov-2": "Схема пнг.png",
    "novaland": "Схема пнг.png",
    "green-park-93": "Схема пнг.png",
    "nesterovsky-49": "Схема ПНГ.png",
}

PERVOMAYSKY_MANUAL_SOURCES: dict[str, str] = {
    "before-1.jpg": "До/646e8d3f-e041-4b71-bc3f-6eb6f2d25bbe.jpg",
    "after-2.jpg": "После/photo_2026-05-06_18-48-41.jpg",
    "after-3.jpg": "После/photo_2026-05-06_18-48-31.jpg",
}


def find_ffmpeg() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = [
        Path(r"C:\ffmpeg\bin\ffmpeg.exe"),
        Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe",
    ]
    winget_glob = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if winget_glob.is_dir():
        for pkg in winget_glob.glob("Gyan.FFmpeg_*"):
            for exe in pkg.rglob("ffmpeg.exe"):
                candidates.append(exe)
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def rasterize_source(source: Path, work_dir: Path) -> Path:
    if source.suffix.lower() not in {".heic", ".heif"}:
        return source

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(f"HEIC source requires ffmpeg: {source}")

    target = work_dir / f"{source.stem}.jpg"
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(source),
            "-frames:v",
            "1",
            str(target),
        ],
        capture_output=True,
    )
    if result.returncode != 0 or not target.is_file():
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg failed for {source.name}: {stderr[-500:]}")
    return target


def find_inbox_source(inbox_root: Path, target_name: str) -> Path | None:
    stem = Path(target_name).stem

    stem_matches: list[Path] = []
    for path in inbox_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if path.stem.lower() == stem.lower():
            stem_matches.append(path)
    if stem_matches:
        return sorted(stem_matches, key=natural_sort_key)[0]

    numbered = re.match(r"^(after|before|compare)-(\d+)$", stem, re.IGNORECASE)
    if numbered:
        prefix, index = numbered.group(1).lower(), int(numbered.group(2))
        folder_name = INBOX_PREFIX_DIRS.get(prefix)
        if folder_name:
            folder = inbox_root / folder_name
            if folder.is_dir():
                sources = sorted(
                    [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES],
                    key=natural_sort_key,
                )
                if 1 <= index <= len(sources):
                    return sources[index - 1]

    if stem.lower() == "plan":
        plan_dir = inbox_root / INBOX_PREFIX_DIRS["plan"]
        if plan_dir.is_dir():
            plans = sorted(
                [p for p in plan_dir.iterdir() if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES],
                key=natural_sort_key,
            )
            if plans:
                return plans[0]

    return None


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
        [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES],
        key=natural_sort_key,
    )
    if not sources:
        raise RuntimeError(f"No images found in {source_dir}")

    created: list[Path] = []
    index = start_index
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        for source in sources:
            ext = ".png" if prefix == "plan" else ".jpg"
            target = case_dir / f"{prefix}-{index}{ext}"
            raster = rasterize_source(source, work_dir)
            shutil.copy2(raster, target)
            final = optimize_image_file(target, force=True) or target
            created.append(final)
            index += 1
    return created


def rebuild_case_from_inbox(case_id: str, inbox_slug: str) -> tuple[int, int, list[str]]:
    case_dir = ASSETS_DIR / case_id
    inbox_root = INBOX_DIR / inbox_slug
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Case assets folder not found: {case_dir}")
    if not inbox_root.is_dir():
        raise FileNotFoundError(f"Inbox folder not found: {inbox_root}")

    rebuilt = 0
    fallback = 0
    warnings: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        for asset_path in sorted(case_dir.iterdir()):
            if not asset_path.is_file():
                continue
            if asset_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue

            source = find_inbox_source(inbox_root, asset_path.name)
            if source:
                raster = rasterize_source(source, work_dir)
                shutil.copy2(raster, asset_path)
                optimize_image_file(asset_path, force=True)
                rebuilt += 1
                print(f"rebuilt: {asset_path.relative_to(ROOT)} <- {source.relative_to(ROOT)}")
            else:
                optimize_image_file(asset_path, force=True)
                fallback += 1
                warning = (
                    f"No inbox source for {asset_path.relative_to(ROOT)}; "
                    "re-optimized in place (watermark may remain if file was previously marked)"
                )
                warnings.append(warning)
                print(f"fallback: {asset_path.relative_to(ROOT)}")

    return rebuilt, fallback, warnings


def find_fidan_case_dir(fidan_root: Path, case_id: str) -> Path:
    folder_name = FIDAN_FOLDER_MAP.get(case_id)
    if not folder_name:
        raise FileNotFoundError(f"No Fidan folder mapping for case: {case_id}")
    case_dir = fidan_root / folder_name
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Fidan case folder not found: {case_dir}")
    return case_dir


def find_fidan_plan_source(fidan_root: Path, case_id: str) -> Path | None:
    plan_name = FIDAN_PLAN_FILES.get(case_id)
    if not plan_name:
        return None
    case_dir = find_fidan_case_dir(fidan_root, case_id)
    direct = case_dir / plan_name
    if direct.is_file():
        return direct
    matches = [p for p in case_dir.rglob("*") if p.is_file() and p.name == plan_name]
    return matches[0] if matches else None


def _image_mse(left: Path, right: Path, *, size: int = 96) -> float:
    with Image.open(left) as left_img, Image.open(right) as right_img:
        left_rgb = left_img.convert("RGB").resize((size, size))
        right_rgb = right_img.convert("RGB").resize((size, size))
        left_px = list(left_rgb.getdata())
        right_px = list(right_rgb.getdata())
    return sum(
        (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
        for a, b in zip(left_px, right_px, strict=True)
    ) / (size * size)


def match_assets_to_sources(
    targets: list[Path],
    sources: list[Path],
    *,
    max_score: float = 3500,
) -> dict[str, Path]:
    pairs: list[tuple[float, str, Path]] = []
    for target in targets:
        for source in sources:
            try:
                pairs.append((_image_mse(target, source), target.name, source))
            except OSError:
                continue
    pairs.sort(key=lambda item: item[0])

    mapping: dict[str, Path] = {}
    used_targets: set[str] = set()
    used_sources: set[Path] = set()
    for score, target_name, source in pairs:
        if target_name in used_targets or source in used_sources or score > max_score:
            continue
        mapping[target_name] = source
        used_targets.add(target_name)
        used_sources.add(source)
    return mapping


def apply_source_to_asset(asset_path: Path, source: Path, work_dir: Path) -> None:
    raster = rasterize_source(source, work_dir)
    shutil.copy2(raster, asset_path)
    optimize_image_file(asset_path, force=True)


def rebuild_plans_from_fidan(fidan_root: Path) -> tuple[int, list[str]]:
    rebuilt = 0
    warnings: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        for case_id in FIDAN_PLAN_FILES:
            asset_path = ASSETS_DIR / case_id / "plan.png"
            if not asset_path.is_file():
                warnings.append(f"Missing asset plan: {asset_path.relative_to(ROOT)}")
                continue
            source = find_fidan_plan_source(fidan_root, case_id)
            if not source:
                warnings.append(f"No Fidan plan source for {case_id}")
                continue
            apply_source_to_asset(asset_path, source, work_dir)
            rebuilt += 1
            print(
                f"rebuilt: {asset_path.relative_to(ROOT)} "
                f"<- {source.relative_to(fidan_root)}"
            )
    return rebuilt, warnings


def rebuild_pervomaysky_from_fidan(fidan_root: Path) -> tuple[int, list[str]]:
    case_id = "pervomaysky-44"
    case_dir = ASSETS_DIR / case_id
    fidan_case = find_fidan_case_dir(fidan_root, case_id)
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Case assets folder not found: {case_dir}")

    targets = sorted(
        [
            p
            for p in case_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and p.name != "plan.png"
        ],
        key=lambda p: p.name,
    )
    sources = sorted(
        [p for p in fidan_case.rglob("*") if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES],
        key=lambda p: str(p).lower(),
    )
    mapping = match_assets_to_sources(targets, sources)
    for target_name, rel_source in PERVOMAYSKY_MANUAL_SOURCES.items():
        mapping[target_name] = fidan_case / rel_source

    plan_source = INBOX_DIR / "zhk-pervomaysky" / "03-plan" / "Plan.png"
    warnings: list[str] = []
    rebuilt = 0

    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        for asset_path in sorted(case_dir.iterdir()):
            if not asset_path.is_file() or asset_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            if asset_path.name == "plan.png":
                if plan_source.is_file():
                    apply_source_to_asset(asset_path, plan_source, work_dir)
                    rebuilt += 1
                    print(
                        f"rebuilt: {asset_path.relative_to(ROOT)} "
                        f"<- {plan_source.relative_to(ROOT)}"
                    )
                else:
                    warnings.append(f"No plan source for {asset_path.relative_to(ROOT)}")
                continue

            source = mapping.get(asset_path.name)
            if not source or not source.is_file():
                warnings.append(f"No Fidan source for {asset_path.relative_to(ROOT)}")
                continue
            apply_source_to_asset(asset_path, source, work_dir)
            rebuilt += 1
            print(
                f"rebuilt: {asset_path.relative_to(ROOT)} "
                f"<- {source.relative_to(fidan_root)}"
            )

    return rebuilt, warnings


def rebuild_missing_from_fidan(fidan_root: Path) -> tuple[int, list[str]]:
    if not fidan_root.is_dir():
        raise FileNotFoundError(f"Fidan archive not found: {fidan_root}")

    total_rebuilt = 0
    all_warnings: list[str] = []

    print("=== plans from Fidan ===")
    rebuilt, warnings = rebuild_plans_from_fidan(fidan_root)
    total_rebuilt += rebuilt
    all_warnings.extend(warnings)

    print("\n=== pervomaysky-44 from Fidan ===")
    rebuilt, warnings = rebuild_pervomaysky_from_fidan(fidan_root)
    total_rebuilt += rebuilt
    all_warnings.extend(warnings)

    return total_rebuilt, all_warnings


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


def optimize_assets(
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
            result = optimize_image_file(path, force=force)
            if result:
                changed += 1
                after = result.relative_to(ROOT).as_posix()
                print(f"optimized: {after}")
                if before != after:
                    replacements[before] = after
            else:
                skipped += 1

    if sync_data and replacements:
        count = sync_data_js(replacements)
        print(f"Updated {count} path(s) in js/data.js")

    return changed, skipped, replacements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Optimize catalog images in assets/ (and import from inbox/)."
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
        "--optimize-all",
        action="store_true",
        help="Optimize all case images in assets/ (skips assets/brand)",
    )
    parser.add_argument(
        "--protect-all",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--recompress-all",
        action="store_true",
        help="Re-optimize all images (JPG for photos, sync js/data.js paths)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-optimize even if file is already processed",
    )
    parser.add_argument(
        "--sync-data",
        action="store_true",
        help="Update js/data.js when image paths change to .jpg",
    )
    parser.add_argument(
        "--rebuild-from-inbox",
        action="store_true",
        help="Rebuild case images from inbox originals (requires --case)",
    )
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Rebuild all mapped cases from inbox originals",
    )
    parser.add_argument(
        "--inbox",
        help="Inbox slug under inbox/ (default: from built-in case map)",
    )
    parser.add_argument(
        "--rebuild-missing-from-fidan",
        action="store_true",
        help="Rebuild previously unmatched images from the Fidan archive",
    )
    parser.add_argument(
        "--fidan-root",
        type=Path,
        default=DEFAULT_FIDAN_ROOT,
        help="Path to 'Фидан - За Комфортом' source archive",
    )
    args = parser.parse_args()

    if args.recompress_all:
        args.force = True
        args.sync_data = True

    if args.protect_all:
        args.optimize_all = True

    if args.rebuild_missing_from_fidan:
        try:
            rebuilt, warnings = rebuild_missing_from_fidan(args.fidan_root)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"\nDone. Rebuilt from Fidan: {rebuilt}, warnings: {len(warnings)}")
        for warning in warnings:
            print(f"WARN: {warning}", file=sys.stderr)
        return 0

    if args.rebuild_all:
        total_rebuilt = 0
        total_fallback = 0
        all_warnings: list[str] = []
        for case_id, inbox_slug in CASE_INBOX_MAP.items():
            if not (ASSETS_DIR / case_id).is_dir():
                print(f"skip: assets/{case_id} (missing)")
                continue
            print(f"\n=== {case_id} <= {inbox_slug} ===")
            try:
                rebuilt, fallback, warnings = rebuild_case_from_inbox(case_id, inbox_slug)
            except (FileNotFoundError, RuntimeError) as exc:
                print(str(exc), file=sys.stderr)
                return 1
            total_rebuilt += rebuilt
            total_fallback += fallback
            all_warnings.extend(warnings)
        print(
            f"\nDone. Rebuilt from inbox: {total_rebuilt}, "
            f"fallback optimize: {total_fallback}, warnings: {len(all_warnings)}"
        )
        for warning in all_warnings:
            print(f"WARN: {warning}", file=sys.stderr)
        return 0

    if args.rebuild_from_inbox:
        if not args.case:
            print("--case is required with --rebuild-from-inbox", file=sys.stderr)
            return 1
        inbox_slug = args.inbox or CASE_INBOX_MAP.get(args.case)
        if not inbox_slug:
            print(
                f"No inbox mapping for {args.case}; pass --inbox <slug>",
                file=sys.stderr,
            )
            return 1
        try:
            rebuilt, fallback, warnings = rebuild_case_from_inbox(args.case, inbox_slug)
        except (FileNotFoundError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Done. Rebuilt: {rebuilt}, fallback: {fallback}")
        for warning in warnings:
            print(f"WARN: {warning}", file=sys.stderr)
        return 0

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

    if args.optimize_all or args.case or args.recompress_all:
        changed, skipped, replacements = optimize_assets(
            case_id=args.case,
            force=args.force,
            sync_data=args.sync_data,
        )
        print(f"Done. Optimized: {changed}, skipped: {skipped}, path updates: {len(replacements)}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
