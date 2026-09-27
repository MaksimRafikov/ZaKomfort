# Public deploy allowlist — ZaKomfort / katalog.zakomfortom.com

## Problem

GitHub Pages was publishing the **entire** `main` branch root. That exposed:

- `/scripts/*.py` — build and asset pipeline
- `/content/**/*.json` — case source data
- `/AGENTS.md`, `/WORKFLOW.md`, `/docs/**`, `/_headers`, `/.gitignore`, `/requirements.txt`

`inbox/` and some docs were already 404 in places, but enough tooling was live to map the pipeline.

## Solution

1. `scripts/export-public-site.py` copies **only** visitor-facing files into `_site/`:
   - root: `index.html`, `case.html`, `tips.html`, `404.html`, `CNAME`, `.nojekyll`, `robots.txt`, `sitemap.xml`
   - dirs: `assets/`, `cases/`, `tips/`, `css/`, `js/`
2. `.github/workflows/deploy-pages.yml` builds, validates, exports, and deploys `_site` via **GitHub Actions**.
3. Repo Settings → Pages → Source must be **GitHub Actions** (not “Deploy from a branch”).

Cloudflare / `_headers` remain optional and still need customer DNS approval (see `docs/security-headers.md`). This change does **not** touch NS records.

## Local check

```powershell
python scripts/build-pages.py
python scripts/validate-cases.py
python scripts/export-public-site.py
python -m http.server 8080 --directory _site
```

## After first Actions deploy

Confirm these return **404**:

- `/AGENTS.md`
- `/scripts/build-pages.py`
- `/content/site.json`
- `/docs/security-headers.md`
- `/WORKFLOW.md`
- `/.gitignore`
- `/requirements.txt`

Public pages (`/`, `/cases/.../`, `/tips.html`) must stay **200**.
