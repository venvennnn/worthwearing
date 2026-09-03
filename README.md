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

The judges demo is a **single Streamlit app**. Scoring and Perfect Corp live in Python — no Node, Vercel, or CORS.

```
streamlit_app.py              Streamlit UI
backend/app/scoring.py        deterministic Worth Score / Return Risk
backend/app/providers/        Perfect Corp cloth-v4 + prepared fallback
backend/data/                 closet, products, prepared assets
```

- `PerfectCorpProvider` keeps `PERFECT_CORP_API_KEY` server-side, uploads images through the File API, and starts cloth-v4 with `garment_category` mapped from the garment (`outer` for jackets, `upper` for shirts, `lower` for bottoms).
- If the live call fails or exceeds 45 seconds, the UI offers **Use prepared demo result** instead of silently swapping it in.
- **Add to your wardrobe** and **Try a shirt or other garment** accept a photo plus tags. Uploads stay in the Streamlit session (not a shared catalog) and are included in scoring.

## Setup

Python 3.12:

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env          # add PERFECT_CORP_API_KEY, DEMO_MODE=false
streamlit run streamlit_app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## Deploy for judges (Streamlit Community Cloud)

1. Push this repo to GitHub (this branch or `main`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app**.
3. Repository: `venvennnn/worthwearing`. Branch: `main`. Main file: `streamlit_app.py`.
4. **Advanced settings → Python version: 3.12**.
5. **App settings → Secrets** (same keys as `.streamlit/secrets.toml.example`):

```toml
DEMO_MODE = "false"
PERFECT_CORP_API_KEY = "your-key"
PERFECT_CORP_BASE_URL = "https://yce-api-01.makeupar.com"
PERFECT_CORP_TRYON_PATH = "/s2s/v2.0/task/cloth-v4"
PERFECT_CORP_STATUS_PATH = "/s2s/v2.0/task/cloth-v4/{task_id}"
```

6. Deploy. Share the `*.streamlit.app` URL with judges.

Disconnect the Vercel project so it stops building the old Next.js app.

Render also works: root of repo, `PYTHON_VERSION=3.12.11`, start command  
`streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`.

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

## Tests

```bash
cd backend && python3 -m pytest
```

## Two-minute presentation check

1. Open the Streamlit app. Confirm Maya’s photo and the twelve-item closet.
2. Select Jacket A (Noir Moto). Click **Try it with my wardrobe**.
3. Confirm Skip It, high Return Risk, duplication against the vintage leather biker, and the try-on as the largest visual.
4. Expand **Why this result?** and check that factor points sum to Return Risk.
5. Select Jacket B (Harbor Field). Run again. Confirm Worth It, ≥4 outfits, before-and-after, and office / weekend / rainy-commute images.
6. If live try-on fails, **Use prepared demo result** is explicit — never a silent swap.
7. Choose **Add to wardrobe**, upload a photo, and confirm it appears in Maya’s closet labeled *yours*. Re-run Jacket A or B so scoring includes the extra piece.
8. Choose **Try a shirt**, upload a shirt, and confirm a Worth It / Think Again / Skip It result against the closet. A second white oxford should show high duplication.
9. Close on: we don’t help shoppers buy more. We help them keep what they buy.
