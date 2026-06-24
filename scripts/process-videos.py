#!/usr/bin/env python3
"""Import expert-tip videos from inbox, transcode for web, extract posters (no watermark)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX_DIR = ROOT / "inbox" / "expert-tips"
ASSETS_TIPS = ROOT / "assets" / "tips"
TIPS_DATA = ROOT / "js" / "tips-data.js"
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}

# slug -> (source filename, category, short summary)
TIP_CATALOG: dict[str, tuple[str, str, str]] = {
    "repair-life-hacks": (
        "3 решения в ремонте чтобы облегчить жизнь.MP4",
        "Общее",
        "Три практичных решения, которые упрощают повседневную жизнь после ремонта.",
    ),
    "outdated-solutions": (
        "3 устаревших решения - на что заменить.MP4",
        "Дизайн",
        "Что уже не актуально в интерьере и чем заменить устаревшие приёмы.",
    ),
    "design-tricks-5": (
        "5 дизайнерских фишек.MP4",
        "Дизайн",
        "Пять приёмов, которые делают интерьер выразительнее без лишних затрат.",
    ),
    "modern-interior-5": (
        "5 идей в современном интерьере.mp4",
        "Дизайн",
        "Современные идеи для интерьера: что работает сегодня и почему.",
    ),
    "built-in-coffee": (
        "Встроенная кофемашина.MP4",
        "Кухня",
        "Как встроить кофемашину в кухню: эргономика, коммуникации и обслуживание.",
    ),
    "wardrobe-small-bedroom": (
        "Гардеробная в маленькой спальне.MP4",
        "Планировка",
        "Как организовать гардеробную в компактной спальне без потери комфорта.",
    ),
    "where-not-to-save": (
        "Где нельзя экономить.MP4",
        "Бюджет",
        "На чём экономить опасно: узлы ремонта, где дешевизна оборачивается проблемами.",
    ),
    "hidden-doors-plinth": (
        "Двери скрытого монтажа и плинтус.MP4",
        "Отделка",
        "Скрытые двери и плинтус: как связать отделку и получить чистые линии.",
    ),
    "installation-benefits": (
        "Еще одна польза инсталяции в санузле.MP4",
        "Санузел",
        "Дополнительные плюсы инсталляции в санузле помимо экономии места.",
    ),
    "layout-importance": (
        "Зачем обращать внимание на планировку квартиры.MP4",
        "Планировка",
        "Почему планировка важнее отделки и как оценить квартиру до ремонта.",
    ),
    "electric-panel": (
        "Идеальный электрический щит.MP4",
        "Инженерия",
        "Как должен быть устроен электрощит: безопасность, резерв и удобство.",
    ),
    "kitchen-interior": (
        "Интерьер кухни.MP4",
        "Кухня",
        "Ключевые решения для функциональной и аккуратной кухни.",
    ),
    "kitchen-zone": (
        "Как правильно организовать кухонную зону.MP4",
        "Кухня",
        "Зонирование кухни: рабочий треугольник, хранение и освещение.",
    ),
    "beautiful-organized": (
        "Как сделать красиво и организованно.MP4",
        "Планировка",
        "Как совместить эстетику и порядок в интерьере без перегруза.",
    ),
    "wall-corners": (
        "Как сохранить углы стен.MP4",
        "Отделка",
        "Как защитить углы стен при ремонте и эксплуатации.",
    ),
    "plinth-timing": (
        "Когда устанавливать плинтус.MP4",
        "Отделка",
        "На каком этапе ремонта ставить плинтус и почему порядок важен.",
    ),
    "hide-pipes-bathroom": (
        "Куда спрятать трубы в ванной.MP4",
        "Инженерия",
        "Варианты маскировки труб в ванной с доступом для обслуживания.",
    ),
    "water-heater-hack": (
        "Лайфхак с водонагревателем.MP4",
        "Инженерия",
        "Практичный приём с водонагревателем для удобства и экономии места.",
    ),
    "heating-solutions": (
        "Не стандартные решения по отоплению.MP4",
        "Инженерия",
        "Нестандартные решения по отоплению в современном интерьере.",
    ),
    "bathroom-4sqm": (
        "Пример ванной комнаты 4 кв м.MP4",
        "Санузел",
        "Разбор планировки и отделки ванной площадью 4 м².",
    ),
    "bathroom-7sqm": (
        "Санузел 7 кв м.MP4",
        "Санузел",
        "Как распределить зоны в санузле 7 м²: душ, сантехника, хранение.",
    ),
    "secret-pantry": (
        "Секретная кладовая.MP4",
        "Планировка",
        "Скрытая кладовая в интерьере: где разместить и как спрятать.",
    ),
    "minimalism-secrets": (
        "Секреты минимализма в интерьере.MP4",
        "Дизайн",
        "Как сделать минималистичный интерьер тёплым и жилым.",
    ),
    "low-price-danger": (
        "Чем опасна низная цена в ремонте.MP4",
        "Бюджет",
        "Риски дешёвого ремонта: где экономия превращается в переделки.",
    ),
    "shadow-plinth": (
        "Что важно знать о теневом плинтусе.MP4",
        "Отделка",
        "Теневой плинтус: монтаж, сочетание с полом и типичные ошибки.",
    ),
    "bathroom-door-seam": (
        "Шов примыкания под дверью в санузел.MP4",
        "Санузел",
        "Как оформить шов примыкания пола к санузлу под дверью.",
    ),
}


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates: list[Path] = [
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
    raise FileNotFoundError("ffmpeg not found. Install: winget install Gyan.FFmpeg")


def find_ffprobe(ffmpeg: str) -> str:
    probe = Path(ffmpeg).with_name("ffprobe.exe")
    if probe.is_file():
        return str(probe)
    found = shutil.which("ffprobe")
    if found:
        return found
    raise FileNotFoundError("ffprobe not found alongside ffmpeg")


def probe_duration(ffprobe: str, path: Path) -> int | None:
    try:
        out = subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return max(0, int(round(float(out))))
    except (subprocess.CalledProcessError, ValueError, OSError):
        return None


def transcode_video(
    ffmpeg: str,
    source: Path,
    target: Path,
    *,
    crf: int,
    max_height: int,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    vf = (
        f"scale='min(1280,iw)':'min({max_height},ih)':force_original_aspect_ratio=decrease,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(target),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(
            f"ffmpeg failed for {source.name}:\n{stderr[-2000:]}"
        )


def extract_poster(ffmpeg: str, source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-ss",
            "2",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            "scale=720:-2:flags=lanczos",
            "-q:v",
            "3",
            str(target),
        ],
        check=True,
        capture_output=True,
    )


def title_from_filename(filename: str) -> str:
    return Path(filename).stem.strip()


def build_tips_data_js(entries: list[dict]) -> str:
    lines = [
        "/** Expert repair tips — generated by scripts/process-videos.py */",
        "const EXPERT_TIPS = " + json.dumps(entries, ensure_ascii=False, indent=2) + ";",
        "",
        "function getTipCategories() {",
        '  const cats = new Set(EXPERT_TIPS.map((t) => t.category));',
        '  return Array.from(cats).sort((a, b) => a.localeCompare(b, "ru"));',
        "}",
        "",
        "function getTipById(id) {",
        "  return EXPERT_TIPS.find((t) => t.id === id);",
        "}",
        "",
    ]
    return "\n".join(lines)


def process_all(
    *,
    source_dir: Path | None,
    force: bool,
    dry_run: bool,
    generate_data: bool,
) -> int:
    inbox = source_dir or INBOX_DIR
    if not inbox.is_dir():
        print(f"ERROR: inbox not found: {inbox}", file=sys.stderr)
        return 1

    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe(ffmpeg)
    print(f"Using ffmpeg: {ffmpeg}")

    inbox_files = {p.name: p for p in inbox.iterdir() if p.suffix.lower() in VIDEO_SUFFIXES}
    data_entries: list[dict] = []
    errors: list[str] = []

    for slug, (filename, category, summary) in TIP_CATALOG.items():
        source = inbox_files.get(filename)
        if not source:
            errors.append(f"Missing source: {filename} (slug {slug})")
            continue

        out_dir = ASSETS_TIPS / slug
        video_out = out_dir / "video.mp4"
        poster_out = out_dir / "poster.jpg"
        title = title_from_filename(filename)

        size_mb = source.stat().st_size / (1024 * 1024)
        crf = 30 if size_mb > 50 else 28
        max_h = 720

        if dry_run:
            print(f"[dry-run] {slug}: {filename} ({size_mb:.1f} MB) crf={crf}")
            continue

        if not force and video_out.is_file() and poster_out.is_file():
            print(f"SKIP {slug} (exists, use --force)")
        else:
            print(f"Processing {slug} ({size_mb:.1f} MB)...", flush=True)
            transcode_video(ffmpeg, source, video_out, crf=crf, max_height=max_h)
            extract_poster(ffmpeg, video_out, poster_out)
            vsize = video_out.stat().st_size / (1024 * 1024)
            print(f"  -> video {vsize:.1f} MB, poster OK", flush=True)

        duration = probe_duration(ffprobe, video_out) if video_out.is_file() else None
        data_entries.append(
            {
                "id": slug,
                "title": title,
                "summary": summary,
                "category": category,
                "durationSec": duration,
                "cover": f"assets/tips/{slug}/poster.jpg",
                "video": {
                    "label": title,
                    "fileUrl": f"assets/tips/{slug}/video.mp4",
                    "embedUrl": None,
                    "poster": f"assets/tips/{slug}/poster.jpg",
                },
            }
        )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if generate_data and data_entries and not dry_run:
        TIPS_DATA.write_text(build_tips_data_js(data_entries), encoding="utf-8")
        print(f"Wrote {TIPS_DATA} ({len(data_entries)} tips)")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcode expert-tip videos for web.")
    parser.add_argument(
        "--from",
        dest="source_dir",
        type=Path,
        help="Source folder (default: inbox/expert-tips)",
    )
    parser.add_argument("--force", action="store_true", help="Re-transcode existing outputs")
    parser.add_argument("--dry-run", action="store_true", help="List work without transcoding")
    parser.add_argument(
        "--no-data",
        action="store_true",
        help="Skip regenerating js/tips-data.js",
    )
    args = parser.parse_args()
    return process_all(
        source_dir=args.source_dir,
        force=args.force,
        dry_run=args.dry_run,
        generate_data=not args.no_data,
    )


if __name__ == "__main__":
    sys.exit(main())
