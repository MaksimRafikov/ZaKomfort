# Каталог работ ЗА КОМФОРТОМ

Статический каталог кейсов ремонта: HTML/CSS/JS. Источник данных — `content/cases/*.json` и `content/site.json`; `js/data.js`, `js/config.js`, `cases/<slug>/index.html` и `sitemap.xml` генерируются сборкой.

## Cursor Cloud specific instructions

- Репозиторий: `MaksimRafikov/ZaKomfort`, ветка `main`.
- Сборка: `python3 scripts/build-pages.py` (data.js, config.js, страницы кейсов, sitemap, кэш-версии `?v=`). Просмотр — `python3 -m http.server 8080`.
- После любых изменений в `content/`, `js/`, `css/` или `assets/` всегда запускайте: `python3 scripts/build-pages.py`, затем `python3 scripts/validate-cases.py`.
- Новый кейс: `python3 scripts/scaffold-case.py --title "..."`, затем `python3 scripts/process-assets.py --case <id> --from inbox/<slug>/...`, правки в `content/cases/<id>.json`, пересборка.
- Советы эксперта: исходники в `inbox/expert-tips/`, обработка `python3 scripts/process-videos.py` (ffmpeg, без водяного знака) → `assets/tips/<slug>/`, данные в `js/tips-data.js`.
- В публичном коде ссылайтесь только на `assets/<case-id>/...`, никогда на `inbox/`.
- Правила проекта: `.cursor/rules/*.mdc`. Hooks в `.cursor/hooks.json` рассчитаны на Windows/PowerShell в десктопе; в Cloud Agents основной контроль — `validate-cases.py` и rules.

## Content pipeline

1. Исходники — `inbox/<project-slug>/` (неизменяемый архив загрузок).
2. Продакшен-медиа — `assets/<case-id>/` через `scripts/process-assets.py`: мастер-изображение ресайзится до 1440px (JPEG/PNG) и рядом автоматически создаются адаптивные варианты — `<имя>-640.<ext>`, `<имя>-1024.<ext>` (если мастер шире) и WebP-копии `<имя>.webp`, `<имя>-640.webp`, `<имя>-1024.webp`. Варианты — производные файлы: не редактируйте их вручную и не ссылайтесь на них в JSON.
3. Данные кейса — один файл `content/cases/<id>.json` (id совпадает с именем файла и папкой `assets/<id>/`). В `src`/`cover` указывайте только мастер-файлы; srcset подставляет сборка.
4. `python scripts/build-pages.py` генерирует `js/data.js` (с полями `coverSrcset`/`coverWebpSrcset` для карточек), статические страницы `cases/<slug>/index.html` с `<picture>`+srcset, `sitemap.xml` и проставляет кэш-версии `?v=<hash>` во всех HTML — вручную версии не редактируются.
5. `python scripts/validate-cases.py` проверяет схему JSON, существование ассетов, свежесть сгенерированных файлов и наличие адаптивных вариантов изображений.

## Аналитика и медиа-защита

- Яндекс.Метрика: счётчик задаётся полем `metrikaId` в `content/site.json` (null — выключено). Цели на CTA-клики (`cta_call`, `cta_whatsapp`, `cta_telegram`, `cta_max`, `cta_vk`, `cta_quiz`, `cta_calc`) вешает `js/metrika.js` автоматически; цели типа «JavaScript-событие» с этими идентификаторами нужно завести в интерфейсе Метрики.
- Защита медиа минимальна (`js/media-guard.js`): блокировка контекстного меню и drag для фото/видео кейсов. Водяных знаков и DOM-«щитов» нет.
