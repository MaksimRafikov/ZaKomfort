#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"
CASES_DIR = ROOT / "content" / "cases"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9а-яё\s-]", "", value, flags=re.IGNORECASE)
    value = value.replace("ё", "е")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    # Keep only web-safe ascii in final slug.
    value = re.sub(r"[^a-z0-9-]", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def next_order() -> int:
    orders = []
    for path in CASES_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data.get("order"), int):
            orders.append(data["order"])
    return (max(orders) + 10) if orders else 10


def make_template(case_id: str, title: str, address: str) -> dict:
    return {
        "order": next_order(),
        "id": case_id,
        "title": title,
        "address": address,
        "areaSqm": None,
        "areaLabel": "площадь уточняется",
        "roomsLabel": "квартира",
        "format": "Дизайн + ремонт под ключ",
        "style": "Современный интерьер",
        "segment": "Комфорт",
        "complex": title,
        "tags": ["видео"],
        "rooms": ["гостиная", "кухня", "санузел"],
        "hasProjectRender": False,
        "hasVideo": True,
        "cover": f"assets/{case_id}/after-1.jpg",
        "summary": "Краткое описание объекта и результата работ.",
        "task": "Что хотел заказчик и какие ограничения были на старте.",
        "objectDescription": "Что именно выполнено в рамках реализации.",
        "workList": ["Пункт 1", "Пункт 2"],
        "highlights": ["Преимущество 1", "Преимущество 2"],
        "clientFit": ["Для кого подходит этот кейс"],
        "gallery": [
            {"src": f"assets/{case_id}/after-1.jpg", "alt": "После ремонта", "caption": ""}
        ],
        "video": {
            "label": "Видео с комментариями эксперта",
            "embedUrl": None,
            "externalUrl": None,
            "fileUrl": f"assets/{case_id}/expert-overview.mp4",
            "poster": f"assets/{case_id}/after-1.jpg",
            "note": "",
        },
        "cta": {
            "phone": "+7 (917) 766-09-38",
            "whatsapp": "https://wa.me/79177660938",
            "telegram": "https://t.me/+79177660938",
            "max": "https://max.ru/chat?phone=%2B79641995283",
            "vk": "https://vk.com/za.komfortom",
            "quiz": "https://zakomfortom.com/design-project",
            "buttonLabel": "Обсудить похожий дизайн",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create assets folder and print CASES template for a new catalog case."
    )
    parser.add_argument("--title", required=True, help="Case title, for example: ЖК Example")
    parser.add_argument("--address", default="Уфа", help="Case address")
    parser.add_argument("--id", dest="case_id", help="Optional explicit case id (kebab-case)")
    args = parser.parse_args()

    case_id = args.case_id.strip() if args.case_id else slugify(args.title)
    if not case_id or not re.fullmatch(r"[a-z0-9-]+", case_id):
        print("Invalid case id. Use lowercase kebab-case: letters, digits, dashes.", file=sys.stderr)
        return 1

    case_assets = ASSETS_DIR / case_id
    case_assets.mkdir(parents=True, exist_ok=True)

    readme = case_assets / "README.md"
    if not readme.exists():
        readme.write_text(
            "\n".join(
                [
                    f"# {args.title}",
                    "",
                    "Import photos via process-assets.py (web resize + compress).",
                    "",
                    "Example:",
                    f"python scripts/process-assets.py --case {case_id} --from inbox/<slug>/01-photos-after --prefix after",
                    "",
                    "Recommended files:",
                    "- `after-1.jpg` ... `after-N.jpg`",
                    "- `expert-overview.mp4`",
                    "- optional: `plan.png`, `before-1.jpg`, `compare-1.jpg`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    case_file = CASES_DIR / f"{case_id}.json"
    if case_file.exists():
        print(f"Case file already exists, not overwriting: {case_file.relative_to(ROOT)}", file=sys.stderr)
        return 1

    template = make_template(case_id, args.title, args.address)
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    case_file.write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Created: {case_file.relative_to(ROOT)}")
    print(f"Assets folder ready: {case_assets.relative_to(ROOT)}")
    print(
        "Next: process-assets.py --from inbox/... -> edit the JSON -> "
        "python scripts/build-pages.py -> python scripts/validate-cases.py"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
