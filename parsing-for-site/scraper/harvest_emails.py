#!/usr/bin/env python3
"""Сбор e-mail с сайтов клубов (по ссылкам из базы).

Работает по доменам (а не по каждому клубу): один домен опрашивается один раз
(главная + типичные страницы контактов), e-mail затем раздаётся всем клубам с
этим доменом. Результат:
  data/emails_by_domain.csv  — domain,email  (с докачкой)
  data/emails.csv            — URL источника,E-mail  (для enrich.py)

Запуск:
  python3 harvest_emails.py --workers 12
"""
from __future__ import annotations
import argparse
import csv
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
MAIN = os.path.join(DATA, "sportgyms_clubs.csv")
BYDOMAIN = os.path.join(DATA, "emails_by_domain.csv")
EMAILS = os.path.join(DATA, "emails.csv")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

SOCIAL = ("vk.com", "vk.ru", "instagram", "ok.ru", "t.me", "telegram", "wa.me",
          "whatsapp", "facebook", "fb.com", "youtube", "youtu.be", "2gis",
          "yandex.", "google.", "zen.", "dzen.", "tiktok", "taplink", "linktr")

CONTACT_PATHS = ("", "contacts", "contacts/", "kontakty", "kontakty/", "contact",
                 "about", "o-nas", "kontakt")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
BAD_EMAIL = ("example.", "sentry.", "wixpress", "@2x", ".png", ".jpg", ".gif",
             ".webp", "your@", "email@", "domain.", "test@", "@sentry", "u003e",
             "react", "schema.org")
_lock = threading.Lock()


def domain_of(url: str) -> str | None:
    d = re.sub(r"^https?://", "", url.strip()).split("/")[0].lower()
    d = d.split("?")[0].split("#")[0]
    if not d or "." not in d:
        return None
    if "%" in d or " " in d or any(len(lbl) > 63 for lbl in d.split(".")):
        return None
    if any(s in d for s in SOCIAL):
        return None
    return d


def first_site(links: str) -> str | None:
    for l in links.split(";"):
        l = l.strip()
        if not l:
            continue
        d = domain_of(l)
        if d:
            return l if l.startswith("http") else "http://" + l
    return None


def clean_emails(text: str) -> list[str]:
    out = []
    for e in EMAIL_RE.findall(text):
        el = e.lower()
        if any(b in el for b in BAD_EMAIL):
            continue
        if el.endswith((".png", ".jpg", ".gif", ".webp", ".svg")):
            continue
        out.append(e)
    # приоритет «человеческих» ящиков
    pref = [e for e in out if e.lower().split("@")[0] in
            ("info", "mail", "club", "office", "reception", "zakaz", "sales", "hello")]
    uniq = list(dict.fromkeys(pref + out))
    return uniq[:3]


def harvest_domain(session, domain):
    base = "https://" + domain
    found = []
    for path in CONTACT_PATHS:
        for scheme_base in (base, "http://" + domain):
            url = scheme_base.rstrip("/") + "/" + path
            try:
                r = session.get(url, timeout=15, headers={"User-Agent": UA},
                                allow_redirects=True)
                if r.status_code == 200 and r.text:
                    found += clean_emails(r.text)
                    if found:
                        return domain, found[0]
                break  # https сработал/ответил — http не пробуем
            except Exception:
                continue
    return domain, found[0] if found else ""


def load_done():
    done = {}
    if os.path.exists(BYDOMAIN):
        with open(BYDOMAIN, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                done[row["domain"]] = row["email"]
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(MAIN, encoding="utf-8-sig")))
    club_site = {}      # URL источника -> domain
    for r in rows:
        site = first_site(r.get("Ссылки на сайт или соц. сети", ""))
        if site:
            club_site[r["URL источника"]] = domain_of(site)
    domains = sorted({d for d in club_site.values() if d})
    print(f"Клубов с сайтом: {len(club_site)} | уникальных доменов: {len(domains)}", flush=True)

    done = load_done()
    todo = [d for d in domains if d not in done]
    print(f"К опросу доменов: {len(todo)} (готово: {len(done)})", flush=True)

    new = not os.path.exists(BYDOMAIN)
    fbd = open(BYDOMAIN, "a", newline="", encoding="utf-8-sig")
    wbd = csv.DictWriter(fbd, fieldnames=["domain", "email"])
    if new:
        wbd.writeheader()

    t0 = time.time()
    ok = 0
    with requests.Session() as s:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(harvest_domain, s, d): d for d in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                d, email = fut.result()
                if email:
                    ok += 1
                with _lock:
                    wbd.writerow({"domain": d, "email": email})
                    fbd.flush()
                    done[d] = email
                if i % 100 == 0:
                    rate = i / (time.time() - t0)
                    print(f"  {i}/{len(todo)} | с e-mail={ok} | {rate:.1f}/с | "
                          f"ост.~{(len(todo)-i)/max(rate,0.01)/60:.0f} мин", flush=True)
    fbd.close()

    # маппинг URL -> email
    with open(EMAILS, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["URL источника", "E-mail"])
        w.writeheader()
        for url, dom in club_site.items():
            em = done.get(dom, "")
            if em:
                w.writerow({"URL источника": url, "E-mail": em})
    total_emails = sum(1 for v in done.values() if v)
    print(f"Готово. Доменов с e-mail: {total_emails}/{len(done)}. Файл: {EMAILS}", flush=True)


if __name__ == "__main__":
    main()
