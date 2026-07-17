#!/usr/bin/env python3
"""Парсер каталога фитнес-клубов с sportgyms.ru.

Живой сайт закрыт анти-бот сервисом, который блокирует запросы с дата-центровых
IP (капчу с такого адреса пройти нельзя). Поэтому данные берутся из публичного
веб-архива (Wayback Machine), где те же страницы доступны без анти-бота.

Пайплайн:
  1. Список карточек клубов берётся из sitemap.xml самого сайта.
  2. Для каждой карточки находится самый свежий снимок 200 OK в Wayback (CDX-индекс).
  3. Архивная страница скачивается «как есть» (суффикс id_), парсится beautifulsoup.
  4. Извлекаются поля: название, город, адрес, телефон, режим работы, ссылки.
  5. Результат пишется инкрементально в CSV (есть докачка) и затем в XLSX.

Запуск:
  python3 parse_sportgyms.py --build-cdx          # скачать CDX-индекс Wayback
  python3 parse_sportgyms.py                       # спарсить весь каталог
  python3 parse_sportgyms.py --limit 50            # быстрый прогон на 50 клубах
  python3 parse_sportgyms.py --city abakan         # только один город
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

BASE = "https://sportgyms.ru"
SITEMAP = f"{BASE}/sitemap.xml"
CDX = ("http://web.archive.org/cdx/search/cdx?url=sportgyms.ru/*"
       "&output=text&fl=original,timestamp,statuscode&filter=statuscode:200")

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data"))
CDX_FILE = os.path.join(DATA_DIR, "cdx_all.txt")
SITEMAP_FILE = os.path.join(DATA_DIR, "sitemap.xml")
OUT_CSV = os.path.join(DATA_DIR, "sportgyms_clubs.csv")
OUT_XLSX = os.path.join(DATA_DIR, "sportgyms_clubs.xlsx")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Карточка клуба: /<город>/<id>-<slug>.html
CLUB_RE = re.compile(r"/[a-z0-9-]+/\d+-[a-z0-9-]+\.html$")

COLUMNS = [
    "Название клуба",
    "Город",
    "Адрес",
    "Телефон",
    "Режим работы",
    "Ссылки на сайт или соц. сети",
    "URL источника",
    "Дата снимка",
]

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def http_get(session: requests.Session, url: str, tries: int = 4, timeout: int = 60):
    delay = 3
    for i in range(tries):
        try:
            r = session.get(url, timeout=timeout, headers={"User-Agent": UA})
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 503):
                time.sleep(delay)
                delay *= 2
                continue
            if 400 <= r.status_code < 500:
                return None
        except requests.RequestException:
            time.sleep(delay)
            delay = min(delay * 2, 40)
    return None


# --------------------------------------------------------------------------- #
# Подготовка списков URL и индекса Wayback
# --------------------------------------------------------------------------- #
def build_cdx():
    os.makedirs(DATA_DIR, exist_ok=True)
    log("Скачиваю CDX-индекс Wayback (несколько минут)…")
    with requests.get(CDX, stream=True, timeout=900, headers={"User-Agent": UA}) as r:
        r.raise_for_status()
        with open(CDX_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    n = sum(1 for _ in open(CDX_FILE, encoding="utf-8", errors="replace"))
    log(f"Готово: {CDX_FILE} ({n} строк)")


def get_sitemap_urls():
    if not os.path.exists(SITEMAP_FILE):
        os.makedirs(DATA_DIR, exist_ok=True)
        log("Скачиваю sitemap.xml…")
        with requests.Session() as s:
            txt = http_get(s, SITEMAP)
        if not txt:
            sys.exit("Не удалось скачать sitemap.xml")
        open(SITEMAP_FILE, "w", encoding="utf-8").write(txt)
    txt = open(SITEMAP_FILE, encoding="utf-8", errors="replace").read()
    return re.findall(r"<loc>(https://sportgyms\.ru/[^<]+)</loc>", txt)


def norm(u: str) -> str:
    """Нормализует URL для сопоставления sitemap ↔ CDX."""
    u = re.sub(r"^https?://", "", u.strip())
    u = u.replace(":80/", "/").replace(":443/", "/")
    return u.rstrip("/").lower()


CITYID_RE = re.compile(r"sportgyms\.ru/([a-z0-9-]+)/(\d+)-")


def city_id(u: str):
    m = CITYID_RE.search(norm(u))
    return (m.group(1), m.group(2)) if m else None


def load_cdx_lists():
    """Строит индексы Wayback со ВСЕМИ снимками 200 (для отката к более старым).

    Возвращает (by_url, by_cityid), где значения — списки (timestamp, original),
    отсортированные от свежих к старым. Перебор от свежих к старым нужен, потому
    что часть недавних снимков сама является анти-бот заглушкой; в этом случае
    берётся ближайший рабочий снимок постарше.
    """
    if not os.path.exists(CDX_FILE):
        sys.exit(f"Нет {CDX_FILE}. Сначала запустите с --build-cdx")
    by_url: dict[str, list[tuple[str, str]]] = {}
    by_cityid: dict[tuple[str, str], list[tuple[str, str]]] = {}
    with open(CDX_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue
            original, ts = parts[0], parts[1]
            by_url.setdefault(norm(original), []).append((ts, original))
            ci = city_id(original)
            if ci:
                by_cityid.setdefault(ci, []).append((ts, original))
    for d in (by_url, by_cityid):
        for k, v in d.items():
            d[k] = sorted(set(v), key=lambda x: x[0], reverse=True)
    return by_url, by_cityid


def candidates_for(url, by_url, by_cityid, k=8):
    """Список снимков-кандидатов (свежие первыми, без дублей по timestamp)."""
    merged = list(by_url.get(norm(url), []))
    ci = city_id(url)
    if ci:
        merged += by_cityid.get(ci, [])
    seen, out = set(), []
    for ts, orig in sorted(merged, key=lambda x: x[0], reverse=True):
        if ts in seen:
            continue
        seen.add(ts)
        out.append((ts, orig))
        if len(out) >= k:
            break
    return out


# --------------------------------------------------------------------------- #
# Парсинг страницы клуба
# --------------------------------------------------------------------------- #
def _unwrap(href: str) -> str:
    m = re.search(r"/web/\d+(?:id_|im_|fw_)?/(https?://.*)$", href)
    return m.group(1) if m else href


def _clean_div(div) -> str:
    if div is None:
        return ""
    for s in div.find_all(["strong", "b"]):
        s.extract()
    for a in div.find_all("a", href=True):
        txt = a.get_text(strip=True)
        if "custom" in a.get("href", "") or txt in ("(на карте)", "на карте"):
            a.extract()
    return re.sub(r"\s+", " ", div.get_text(" ", strip=True)).strip(" :,")


def parse_club(html: str, source_url: str) -> dict | None:
    soup = BeautifulSoup(html, "lxml")

    name = ""
    h1 = soup.find("h1")
    if h1:
        name = re.sub(r"\s+", " ", h1.get_text(" ", strip=True)).strip()
    if not name:
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            name = og["content"].strip()

    # ссылки берём ДО очистки блока
    links = []
    nc = soup.find("div", class_="ciNC")
    if nc:
        for a in nc.find_all("a", href=True):
            href = _unwrap(a["href"].strip())
            if not href or href.startswith("#") or href.startswith("/"):
                continue
            if "web.archive.org" in href:
                continue
            links.append(href)
    links = list(dict.fromkeys(links))

    city_raw = _clean_div(soup.find("div", class_="ciCities"))
    # «Город / Регион» или «Город » Округ » Район» — берём только город
    city = re.split(r"[/»]", city_raw)[0].strip() if city_raw else ""
    address = _clean_div(soup.find("div", class_="ciAdress"))
    phone = _clean_div(soup.find("div", class_="ciPhone"))
    worktime = _clean_div(soup.find("div", class_="ciWorkTime"))

    if not name and not address and not phone:
        return None

    return {
        "Название клуба": name,
        "Город": city,
        "Адрес": address,
        "Телефон": phone,
        "Режим работы": worktime,
        "Ссылки на сайт или соц. сети": " ; ".join(links),
        "URL источника": source_url,
    }


# --------------------------------------------------------------------------- #
# Основной прогон
# --------------------------------------------------------------------------- #
def load_done(path: str) -> set[str]:
    done = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("URL источника"):
                    done.add(row["URL источника"])
    return done


def fetch_and_parse(session, url, candidates):
    """Перебирает снимки от свежих к старым, пока не найдёт страницу с данными."""
    for ts, original in candidates:
        snap = f"https://web.archive.org/web/{ts}id_/{original}"
        html = http_get(session, snap)
        if not html:
            continue
        rec = parse_club(html, url)
        if rec:
            return url, rec, ts
    return url, None, candidates[0][0] if candidates else ""


def run(limit=None, city=None, workers=6):
    os.makedirs(DATA_DIR, exist_ok=True)
    urls = [u for u in get_sitemap_urls() if CLUB_RE.search(u)]
    if city:
        urls = [u for u in urls if f"/{city}/" in u]
    log(f"Карточек клубов в sitemap: {len(urls)}")

    by_url, by_cityid = load_cdx_lists()
    log(f"URL в CDX-индексе Wayback: {len(by_url)} | клубов по (город,id): {len(by_cityid)}")

    tasks = []
    missing = 0
    for u in urls:
        cands = candidates_for(u, by_url, by_cityid)
        if cands:
            tasks.append((u, cands))
        else:
            missing += 1
    log(f"Есть снимок: {len(tasks)} | нет снимка: {missing}")

    if limit:
        tasks = tasks[:limit]

    done = load_done(OUT_CSV)
    tasks = [t for t in tasks if t[0] not in done]
    if not tasks:
        log("Нечего обрабатывать (всё уже собрано).")
    log(f"К обработке (с учётом докачки): {len(tasks)}")

    new_file = not os.path.exists(OUT_CSV)
    f = open(OUT_CSV, "a", newline="", encoding="utf-8-sig")
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    if new_file:
        writer.writeheader()

    write_lock = threading.Lock()
    ok = err = 0
    t0 = time.time()
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(fetch_and_parse, session, u, cands): u
                    for (u, cands) in tasks}
            for i, fut in enumerate(as_completed(futs), 1):
                url, rec, ts = fut.result()
                if rec:
                    rec["Дата снимка"] = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}"
                    with write_lock:
                        writer.writerow(rec)
                        f.flush()
                    ok += 1
                else:
                    err += 1
                if i % 50 == 0:
                    rate = i / (time.time() - t0)
                    log(f"  {i}/{len(tasks)} | ok={ok} err={err} | "
                        f"{rate:.1f}/с | ост.~{(len(tasks)-i)/max(rate,0.01)/60:.0f} мин")
    f.close()
    log(f"Готово. Успешно: {ok}, без данных: {err}. CSV: {OUT_CSV}")
    export_xlsx()


def export_xlsx():
    if not os.path.exists(OUT_CSV):
        return
    try:
        from openpyxl import Workbook
    except ImportError:
        log("openpyxl не установлен — XLSX пропущен")
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "sportgyms"
    with open(OUT_CSV, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            ws.append(row)
    for col, width in zip("ABCDEFGH", (34, 18, 46, 24, 40, 46, 44, 12)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    wb.save(OUT_XLSX)
    log(f"XLSX: {OUT_XLSX}")


def main():
    ap = argparse.ArgumentParser(description="Парсер каталога sportgyms.ru через Wayback")
    ap.add_argument("--build-cdx", action="store_true", help="скачать CDX-индекс Wayback")
    ap.add_argument("--limit", type=int, default=None, help="ограничить число клубов")
    ap.add_argument("--city", type=str, default=None, help="только указанный город (слаг)")
    ap.add_argument("--workers", type=int, default=6, help="число параллельных потоков")
    ap.add_argument("--xlsx-only", action="store_true", help="только пересобрать XLSX из CSV")
    args = ap.parse_args()

    if args.build_cdx:
        build_cdx()
        return
    if args.xlsx_only:
        export_xlsx()
        return
    run(limit=args.limit, city=args.city, workers=args.workers)


if __name__ == "__main__":
    main()
