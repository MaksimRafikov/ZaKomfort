#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT / "assets"


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


def make_template(case_id: str, title: str, address: str) -> dict:
    return {
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
        "cover": f"assets/{case_id}/after-1.png",
        "summary": "Краткое описание объекта и результата работ.",
        "task": "Что хотел заказчик и какие ограничения были на старте.",
        "objectDescription": "Что именно выполнено в рамках реализации.",
        "workList": ["Пункт 1", "Пункт 2"],
        "highlights": ["Преимущество 1", "Преимущество 2"],
        "clientFit": ["Для кого подходит этот кейс"],
        "gallery": [
            {"src": f"assets/{case_id}/after-1.png", "alt": "После ремонта", "caption": ""}
        ],
        "video": {
            "label": "Видео с комментариями эксперта",
            "embedUrl": None,
            "externalUrl": None,
            "fileUrl": f"assets/{case_id}/expert-overview.mp4",
            "poster": f"assets/{case_id}/after-1.png",
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
                    "Put production-ready media for this case in this folder.",
                    "",
                    "Recommended files:",
                    "- `after-1.png` ... `after-N.png`",
                    "- `expert-overview.mp4`",
                    "- optional: `plan.png`, `before-1.png`, `compare-1.png`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    template = make_template(case_id, args.title, args.address)
    print("CASE_TEMPLATE_START")
    print(json.dumps(template, ensure_ascii=False, indent=2))
    print("CASE_TEMPLATE_END")
    print(f"Assets folder ready: {case_assets.relative_to(ROOT)}")
    print("Next: copy media -> paste template object into js/data.js -> run python scripts/validate-cases.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
