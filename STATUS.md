# Каталог «За Комфортом» — status

Статический каталог кейсов (HTML/CSS/JS). Пайплайн: `inbox` → `process-assets` → `assets` → `content/cases` → `build-pages` → `validate-cases` → **export-public-site** → GitHub Actions Pages.

## Handoff

- **Фаза сейчас:** public-deploy allowlist внедрён; CDN headers по-прежнему отложены
- **Сделано (2026-09-27):** деплой только `_site/` (без `scripts/`, `content/`, `docs/`, `AGENTS.md`, …). См. `docs/public-deploy.md`, workflow `.github/workflows/deploy-pages.yml`
- **CDN headers:** **отложено** — нет полномочий на NS всего `zakomfortom.com`; эталон в `_headers` + `docs/security-headers.md`. Cloudflare / смена NS **не** трогать без явного ОК заказчика
- **Критерий готово (каталог):** страницы/медиа/Метрика; после Actions-деплоя служебные пути → 404
- **Не делать:** менять NS в reg.ru; meta CSP в HTML «наугад»; CF без ОК заказчика
- **Следующее:** обычные задачи каталога; после первого Actions-деплоя — проверить 404 на `/AGENTS.md` и `/scripts/build-pages.py`
- **Новый чат:** вставить шаблон ниже

--- первый сообщение нового чата ---

Прочитай STATUS.md → ## Handoff. Публичный деплой — allowlist `_site/` (docs/public-deploy.md). CDN security headers отложены (нет полномочий на NS всего zakomfortom.com). Не поднимать Cloudflare без явного ОК заказчика. Бери следующую задачу по каталогу из запроса пользователя.
