# Deploy "Current" — three paths, pick one

The plan calls for the live site at **benkalish.com**, but Netlify is hooked
to `BenKalish42/PersonalWebsite`, not directly to this repo. The legacy way
is `scripts/deploy_to_benkalish.sh` from a dev machine. Three faster paths:

---

## Path A — drag-and-drop the prebuilt zip (30 seconds, no auth)

A clean public bundle is stashed at:

```
/opt/cursor/artifacts/current-almanac-v1.0.0-rc.1-public.zip
```

Steps:

1. Download that zip.
2. Unzip locally.
3. Open https://app.netlify.com → choose any site (or "Add new site" → "Deploy
   manually") → drag the unzipped folder onto the deploys page.

The bundle was built clean — no API keys baked in. The Workbench will show
"key not configured" badges, which is correct for a public deploy. To enable
LLM features, route through the FastAPI backend (set `VITE_API_URL`).

---

## Path B — direct Netlify CLI from a shell (1 command)

Run from anywhere with this repo cloned and `npm install` done:

```bash
NETLIFY_AUTH_TOKEN=<your_token> ./scripts/deploy_to_netlify.sh --new
# follow the prompts to create a new site, OR:
NETLIFY_AUTH_TOKEN=<your_token> NETLIFY_SITE_ID=<existing_site_id> \
  ./scripts/deploy_to_netlify.sh
```

Get a token at https://app.netlify.com/user/applications → "Personal access tokens".

---

## Path C — fully automated via GitHub Actions

Two workflows live in `.github/workflows/`:

- `deploy-to-benkalish.yml` — pushes to `PersonalWebsite/static/Current/`,
  Netlify there picks it up. Needs `PERSONAL_WEBSITE_TOKEN` (PAT).
- `deploy-to-netlify.yml` — pushes directly to a Netlify site. Needs
  `NETLIFY_AUTH_TOKEN` + `NETLIFY_SITE_ID`.

Either one works. Pick the one that matches where you want the live site.

Settings → Secrets and variables → Actions → New repository secret. Then
either re-push to master or trigger via Actions tab → Run workflow.

---

## A note on API keys in the public bundle

`fetchDeepSeekChat()` in `src/services/llmService.ts` calls DeepSeek directly
from the browser. Vite bakes any `VITE_*` env at build time, which means
**setting `VITE_DEEPSEEK_API_KEY` makes the key visible in the public JS**.

For a real public site, leave those unset and let the FastAPI backend handle
the call (set `VITE_API_URL` to point at your backend). The current bundle
in `current-almanac-v1.0.0-rc.1-public.zip` was built with **no keys** —
clean for public exposure.
