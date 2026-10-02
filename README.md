# Client Health Score

**Know which clients you're about to lose, and which ones want to buy more, before the renewal call.**

Agencies rarely lose clients by surprise. The signals are there weeks earlier: results slipping, a new decision-maker nobody has met, invoices paid later and later, meetings quietly cancelled. This tool turns those signals into one health score per account, explains every point lost, and says what to do this week.

```
$ clienthealth data/accounts.csv

6 accounts · EUR 42,700/month · at risk EUR 12,100 · watch EUR 12,000 · 2 upsell candidates

| Account         | Health | Results | Relationship | Delivery | Commercial | Stability |
| 🔴 Studio Lumen |     46 |      64 |           40 |       40 |         20 |        60 |
| 🔴 Kaffeekult   |     52 |      51 |           54 |       58 |         40 |        60 |
| 🟠 Pixelpay     |     74 |      83 |           66 |       82 |         92 |        20 |
| 🟢 Velo Urban   |     79 |      72 |           78 |       76 |         88 |       100 |
| 🟢 Nordlys Skin |     97 |     100 |           93 |       92 |       100 |       100 |
```

Pixelpay looks fine on results, but two new decision-makers joined in 90 days. That's the account that gets an onboarding session this week. Full report: [`reports/portfolio_health.md`](reports/portfolio_health.md). Accounts are fictional.

## The five pillars

| Pillar | Weight | Signals |
|---|---:|---|
| **Results** | 30% | Performance against the agreed KPI |
| **Relationship** | 25% | Latest NPS, meeting cadence, how fast *we* reply |
| **Delivery** | 20% | Share of deliverables on time |
| **Commercial** | 15% | How late invoices are paid, often the earliest churn signal |
| **Stability** | 10% | New decision-makers on the client side |

Bands: **healthy** 75+, **watch** 55-74, **at risk** below 55.

Every lost point becomes a **driver** ("Invoices paid 32 days late on average") paired with a **next action** ("Raise payment timing with the finance contact"). Accounts beating their KPI and asking for extras are flagged as **expansion candidates**; promoters with strong results are flagged for **case studies and referrals**.

## QBR drafts with Claude (optional)

```bash
pip install -e ".[ai]"
export ANTHROPIC_API_KEY=sk-...
clienthealth data/accounts.csv --qbr "Pixelpay"
```

Claude returns a 6-8 slide quarterly business review outline plus an opening talk track, as **structured JSON through tool use**. It leads with results, owns the problems, ends with next quarter's plan, and uses only the account's real numbers.

## Run it

```bash
git clone https://github.com/Vishwajeetkumbhar379/client-health-score
cd client-health-score
pip install -e ".[dev]"
clienthealth data/accounts.csv
pytest
```

## Why I built it

As a senior account manager I led a 12-person team across 20+ brand accounts. The hardest part was never one client. It was seeing the whole portfolio clearly enough to know where to spend Monday morning. This is the view I wanted.

---

Built by [Vishwajeet Kumbhar](https://www.linkedin.com/in/vishwajeetkumbhar379) with Claude Code. MIT licence.
