#!/usr/bin/env python3
"""Обогащение базы: добавляет «Бренд/сеть», «Тип объекта» и (если собран) «E-mail».

Запуск:
  python3 enrich.py        # пересобрать обогащённые колонки в основном CSV
Идемпотентно: можно запускать многократно. E-mail подмешивается из data/emails.csv
(URL источника -> e-mail), если файл существует.
"""
from __future__ import annotations
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
MAIN = os.path.join(DATA, "sportgyms_clubs.csv")
EMAILS = os.path.join(DATA, "emails.csv")

OUT_COLUMNS = [
    "Название клуба",
    "Бренд/сеть",
    "Тип объекта",
    "Город",
    "Адрес",
    "Телефон",
    "E-mail",
    "Режим работы",
    "Ссылки на сайт или соц. сети",
    "URL источника",
    "Дата снимка",
]

# Правила типа объекта по тексту названия (порядок важен — сверху вниз)
TYPE_RULES = [
    ("Бассейн", ("бассейн", "плавательн", "водного спорта", "аквапарк", "аквацентр")),
    ("Спорткомплекс/ФОК", ("физкультурно-оздоровительн", "фок ", "фок«", "спортивный комплекс",
                            "спорткомплекс", "дворец спорта", "ледов", "стадион", "манеж",
                            "дворец водного")),
    ("Фитнес-клуб", ("фитнес", "fitness", "тренаж", "gym", "джим", "кроссфит", "crossfit",
                     "ems", "атлетическ", "вэлнес", "wellness")),
    ("Студия", ("студия", "studio")),
    ("Спортшкола/секция", ("спортивная школа", "сдюшор", "дюсш", "секц", "школа ")),
]


def club_type(name: str) -> str:
    low = " " + name.lower() + " "
    for label, keys in TYPE_RULES:
        if any(k in low for k in keys):
            return label
    if "спорт" in low:
        return "Спортцентр/клуб"
    return "Другое"


def brand(name: str) -> str:
    m = re.search(r"«([^»]+)»", name)
    if m:
        return m.group(1).strip()
    m = re.search(r'"([^"]+)"', name)
    return m.group(1).strip() if m else ""


def load_emails() -> dict[str, str]:
    if not os.path.exists(EMAILS):
        return {}
    out = {}
    with open(EMAILS, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            url = row.get("URL источника") or row.get("url")
            email = row.get("E-mail") or row.get("email")
            if url and email:
                out[url] = email
    return out


def main():
    rows = list(csv.DictReader(open(MAIN, encoding="utf-8-sig")))
    emails = load_emails()
    # счётчик брендов -> пометка сети считается на лету не требуется
    for r in rows:
        name = r.get("Название клуба", "")
        r["Бренд/сеть"] = brand(name)
        r["Тип объекта"] = club_type(name)
        if "E-mail" not in r or not r["E-mail"]:
            r["E-mail"] = emails.get(r.get("URL источника", ""), "")
    with open(MAIN, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # краткая статистика
    import collections
    t = collections.Counter(r["Тип объекта"] for r in rows)
    nets = collections.Counter(r["Бренд/сеть"] for r in rows if r["Бренд/сеть"])
    with_email = sum(1 for r in rows if r["E-mail"])
    print(f"Строк: {len(rows)}")
    print("Типы:", dict(t))
    print("E-mail заполнено:", with_email)
    print("Топ-10 сетей:", nets.most_common(10))


if __name__ == "__main__":
    main()
