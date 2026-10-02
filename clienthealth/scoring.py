"""Client health scoring for agency and account teams.

Five pillars, each 0-100, weighted into one health score. Every point lost is traced
to a driver with a recommended next action, so the score is something an account
manager can act on, not just a colour on a dashboard.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

WEIGHTS = {"results": 0.30, "relationship": 0.25, "delivery": 0.20, "commercial": 0.15, "stability": 0.10}


@dataclass
class Account:
    name: str
    industry: str
    retainer_eur: float
    months_active: int
    results_vs_kpi_pct: float  # 100 = exactly on target
    on_time_pct: float
    nps: float  # 0-10, last survey
    response_hours: float  # our average reply time
    meetings_90d: int
    invoice_days_late: float
    scope_requests_90d: int  # extra asks from the client
    stakeholder_changes_90d: int  # new decision-makers on the client side

    @classmethod
    def from_row(cls, r: dict) -> "Account":
        f = lambda k: float(r[k])
        return cls(r["account"], r["industry"], f("retainer_eur"), int(f("months_active")), f("results_vs_kpi_pct"),
                   f("on_time_pct"), f("nps"), f("response_hours"), int(f("meetings_90d")), f("invoice_days_late"),
                   int(f("scope_requests_90d")), int(f("stakeholder_changes_90d")))


@dataclass
class Health:
    account: Account
    score: float
    pillars: dict[str, float]
    drivers: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    upsell: list[str] = field(default_factory=list)

    @property
    def band(self) -> str:
        return "healthy" if self.score >= 75 else "watch" if self.score >= 55 else "at risk"


def clamp(x: float) -> float:
    return max(0.0, min(100.0, x))


def score(a: Account) -> Health:
    drivers, actions, upsell = [], [], []
    results = clamp(a.results_vs_kpi_pct - 20)  # 120% of KPI scores 100, 70% scores 50
    if a.results_vs_kpi_pct < 85:
        drivers.append(f"Results at {a.results_vs_kpi_pct:.0f}% of KPI")
        actions.append("Book a results review: agree what's realistic, show the recovery plan with dates")
    relationship = clamp(a.nps * 10 * 0.6 + min(a.meetings_90d, 6) / 6 * 25 + clamp(100 - a.response_hours * 2) * 0.15)
    if a.nps <= 6:
        drivers.append(f"NPS {a.nps:.0f}/10 (detractor)")
        actions.append("Call the main stakeholder this week; ask what one thing would change their score")
    if a.meetings_90d < 2:
        drivers.append(f"Only {a.meetings_90d} meeting(s) in 90 days")
        actions.append("Set a fixed monthly check-in and a quarterly business review")
    if a.response_hours > 24:
        drivers.append(f"Our replies take {a.response_hours:.0f}h on average")
        actions.append("Agree a same-day response promise and a backup contact")
    delivery = clamp((a.on_time_pct - 50) * 2)
    if a.on_time_pct < 85:
        drivers.append(f"Only {a.on_time_pct:.0f}% of deliverables on time")
        actions.append("Review the workflow: brief to approval timings, owner per step, buffer days")
    commercial = clamp(100 - a.invoice_days_late * 2.5)
    if a.invoice_days_late > 15:
        drivers.append(f"Invoices paid {a.invoice_days_late:.0f} days late on average")
        actions.append("Raise payment timing with finance contact; late payment is often an early churn signal")
    stability = clamp(100 - a.stakeholder_changes_90d * 40)
    if a.stakeholder_changes_90d:
        drivers.append(f"{a.stakeholder_changes_90d} new decision-maker(s) on the client side")
        actions.append("Run an onboarding session for the new stakeholder: goals, results so far, what's next")
    pillars = {"results": results, "relationship": relationship, "delivery": delivery, "commercial": commercial, "stability": stability}
    total = sum(pillars[k] * w for k, w in WEIGHTS.items())
    if a.results_vs_kpi_pct >= 110 and a.scope_requests_90d >= 2 and total >= 70:
        upsell.append(f"Beating KPI ({a.results_vs_kpi_pct:.0f}%) and asking for {a.scope_requests_90d} extras: propose a scope expansion")
    elif a.results_vs_kpi_pct >= 110 and a.nps >= 9:
        upsell.append("Promoter with strong results: ask for a case study and a referral")
    return Health(a, round(total, 1), {k: round(v) for k, v in pillars.items()}, drivers, actions, upsell)


def load(path: Path) -> list[Account]:
    with open(path, newline="", encoding="utf-8") as f:
        return [Account.from_row(r) for r in csv.DictReader(f)]


def portfolio(hs: list[Health]) -> dict:
    total = sum(h.account.retainer_eur for h in hs)
    risk = sum(h.account.retainer_eur for h in hs if h.band == "at risk")
    watch = sum(h.account.retainer_eur for h in hs if h.band == "watch")
    return {"accounts": len(hs), "monthly_revenue": total, "at_risk_revenue": risk, "watch_revenue": watch,
            "upsell_candidates": sum(bool(h.upsell) for h in hs)}
