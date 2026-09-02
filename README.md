# WorthWearing

Try it on. Know if it’s worth owning.

WorthWearing is a B2B2C wardrobe-compatibility layer that retailers can embed on a product page. It combines Perfect Corp virtual try-on imagery with a deterministic Return Risk score to answer: will this shopper actually wear and keep this item?

This repository is a **decision-support prototype** for the Perfect Corp sponsor challenge. It does not claim verified return reduction, fit accuracy, sustainability savings, or cost-per-wear accuracy. Scores come from curated closet metadata and explicit rules. A production version could later calibrate those scores against retailer purchase and return outcomes.

## Product language

| Role | Name |
| --- | --- |
| Product | WorthWearing |
| Retail product | WorthWearing Intelligence |
| Core score | Worth Score |
| Risk metric | Return Risk |
| Supporting metric | Wardrobe Compatibility |
| Recommendations | Worth It / Think Again / Skip It |

Demo line: *Virtual try-on shows whether it looks good. WorthWearing shows whether it deserves a place in your wardrobe.*

Close: *We don’t help shoppers buy more. We help them keep what they buy.*

## Architecture

```
/frontend   Next.js 15 + TypeScript + Tailwind + Recharts
/backend    FastAPI + Python 3.12 + Pydantic + httpx
/backend/data/closet.json     twelve-item curated closet
/backend/data/products.json   Jacket A (duplicative) and Jacket B (versatile)
```

- `GET /health` — service health and enabled provider modes
- `GET /api/demo` — shopper, closet, candidates, demo copy
- `POST /api/analyze` — deterministic analysis for a candidate
- `POST /api/try-on` and `GET /api/try-on/{job_id}` — Perfect Corp or prepared demo
- `POST /api/try-on/{job_id}/fallback` — explicit “Use prepared demo result”
- `POST /api/scenarios` — optional Image Generator (disabled without credentials)

Try-on providers share `VirtualTryOnProvider.create_try_on()` / `get_status()`.

- `PerfectCorpProvider` keeps `PERFECT_CORP_API_KEY` server-side, uses timeouts, retries transient failures twice, and normalizes cloth-v4 responses. Official payload fields are documented in `backend/app/providers/perfect_corp.py`.
- `DemoProvider` returns labeled pre-generated assets when `DEMO_MODE=true` or live credentials are missing.
- Live calls that fail or exceed 20 seconds never silently substitute a demo image. The UI offers **Use prepared demo result**.
- MCP is an optional adapter behind the same interfaces. The app does not describe MCP as active unless a real MCP tool call succeeds (`mcp_active` on `/health`).

## Scoring

Every closet item and candidate has `id`, `name`, `category`, `subcategory`, `colors`, `style_tags`, `season_tags`, `occasion_tags`, `layer`, `image_url`, and optional `price`.

```
D duplication            max weighted Jaccard vs same-category closet item
                         (color 20%, subcategory 30%, style 35%, season 15%)
I style isolation        1 − (eligible items compatible in style and color)
C climate mismatch       1 − Jaccard(candidate seasons, profile climate)
O occasion narrowness    1 − supported occasions / target occasions
U usage uncertainty      higher when outfits are few or occasion coverage is weak

Return Risk = round(100 × (0.30D + 0.25I + 0.20C + 0.15O + 0.10U))
Worth It 0–39 · Think Again 40–69 · Skip It 70–100
Wardrobe Compatibility = 100 − round(100 × (0.40I + 0.25C + 0.20O + 0.15D))
Worth Score = 100 − Return Risk
```

Cost per wear is an **Estimated CPW scenario**: `price / estimated_wears` over a visible twelve-month assumption. It is not a prediction.

Seed metadata is tuned so Jacket A lands about 75–90 (Skip It) against the existing leather jacket, and Jacket B lands about 15–35 (Worth It) with at least four compatible outfits.

## Setup

Requires Python 3.12 and Node 20+.

```bash
cp .env.example .env
# backend
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
# frontend (separate terminal)
cd frontend
npm install
printf 'NEXT_PUBLIC_API_URL=http://localhost:8000\n' > .env.local
npm run dev
```

Open http://localhost:3000 then `/demo`.

To use live Perfect Corp try-on, set `DEMO_MODE=false` and `PERFECT_CORP_API_KEY`. Keep the key out of client code. If the live call fails or exceeds twenty seconds, use the prepared demo result instead of assuming success.

## Tests

```bash
cd backend && python3 -m pytest
cd frontend && npm test
cd frontend && npx playwright install chromium && npm run test:e2e
```

## Two-minute presentation check

1. Open `/demo`. Confirm Maya’s photo and the twelve-item closet.
2. Select Jacket A (Noir Moto). Click **Try it with my wardrobe**. Watch the staged progress.
3. Confirm Skip It, high Return Risk, duplication against the vintage leather biker, and the try-on as the largest visual.
4. Expand **Why this result?** and check that factor points sum to Return Risk.
5. Select Jacket B (Harbor Field). Run again. Confirm Worth It, ≥4 outfits, before/after comparison, and office / weekend / rainy-commute thumbnails.
6. If you simulate a live failure, **Use prepared demo result** appears and the badge reads Prepared demo — never a silent swap.
7. Close on: we don’t help shoppers buy more. We help them keep what they buy.

Preflight both jackets before recording.
