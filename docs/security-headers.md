# Security headers — За Комфортом

GitHub Pages **не отдаёт** кастомные HTTP-заголовки из репозитория. Для `katalog.zakomfortom.com` нужен прокси/CDN перед Pages (обычно Cloudflare).

В корне лежит `_headers` (формат Cloudflare Pages / Netlify) как **эталон CSP**. Сам по себе файл на чистом GitHub Pages ничего не меняет и деплой не ломает.

## Рекомендуемый путь: Cloudflare перед GitHub Pages

1. Домен `katalog.zakomfortom.com` уже на Pages (`CNAME`).
2. Подключите зону в Cloudflare (прокси оранжевое облако на A/CNAME записи каталога).
3. **Rules → Transform Rules → Modify Response Header** (или Configuration Rules):
   - Match: hostname = `katalog.zakomfortom.com`
   - Set headers из `_headers` ниже (или скопируйте значения из файла).
4. Проверка: DevTools → Network → document → Response Headers; CSP без ошибок в Console (Метрика должна грузиться).

Альтернатива: Cloudflare Pages / Netlify вместо GH Pages — тогда `_headers` подхватится автоматически.

## Эталонные заголовки

См. файл `/_headers` в корне репо.

CSP рассчитан на:
- собственные скрипты/стили (`'self'`);
- Яндекс.Метрику: `mc.yandex.ru`, `mc.yandex.com`, `yandex.ru` / `*.yandex.ru` (tag.js, hit, clickmap);
- медиа только с того же origin (`assets/…`);
- `frame-ancestors 'none'` + `X-Frame-Options: DENY` против clickjacking.

Если включите webvisor в `js/metrika.js`, может понадобиться расширить `script-src` / `connect-src` (сейчас `webvisor: false`).

## Чего не делать

- Не вшивать meta CSP в HTML «на глаз» без проверки Метрики — легко сломать аналитику.
- Не коммитить секреты в headers.
- Не полагаться на `_headers` на голом GitHub Pages — заголовки не появятся.

## Related

Скрытие исходников пайплайна с публичного хоста (отдельно от headers): `docs/public-deploy.md`.
