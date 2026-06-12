# Каталог работ ЗА КОМФОРТОМ

Статический каталог кейсов ремонта: HTML/CSS/JS, данные в `js/data.js`.

## Cursor Cloud specific instructions

- Репозиторий: `MaksimRafikov/ZaKomfort`, ветка `main`.
- Сборка не требуется — откройте `index.html` или поднимите локальный сервер: `python3 -m http.server 8080`.
- После изменений в `js/data.js` или `assets/` всегда запускайте: `python3 scripts/validate-cases.py`.
- Новый кейс: `python3 scripts/scaffold-case.py --title "..."`, затем медиа из `inbox/<slug>/` в `assets/<case-id>/`.
- В публичном коде ссылайтесь только на `assets/<case-id>/...`, никогда на `inbox/`.
- Правила проекта: `.cursor/rules/*.mdc`. Hooks в `.cursor/hooks.json` рассчитаны на Windows/PowerShell в десктопе; в Cloud Agents основной контроль — `validate-cases.py` и rules.

## Content pipeline

1. Исходники — `inbox/<project-slug>/` (неизменяемый архив загрузок).
2. Продакшен-медиа — `assets/<case-id>/` (`after-1`, `before-1`, `plan`, `expert-overview.mp4`).
3. Один объект кейса в `js/data.js` с совпадающим `id` и `cover`.
