from pathlib import Path
from types import SimpleNamespace

from clienthealth.cli import qbr, report
from clienthealth.scoring import Account, load, portfolio, score

DATA = Path(__file__).parent.parent / "data" / "accounts.csv"


def acc(**kw):
    base = dict(name="A", industry="x", retainer_eur=5000, months_active=12, results_vs_kpi_pct=110, on_time_pct=95, nps=9,
                response_hours=4, meetings_90d=5, invoice_days_late=0, scope_requests_90d=0, stakeholder_changes_90d=0)
    base.update(kw)
    return Account(**base)


def test_healthy_account():
    h = score(acc())
    assert h.band == "healthy" and not h.drivers


def test_problems_become_drivers_and_actions():
    h = score(acc(results_vs_kpi_pct=70, nps=5, invoice_days_late=30, stakeholder_changes_90d=1, meetings_90d=1))
    assert h.band == "at risk"
    assert len(h.drivers) == len(h.actions) >= 4


def test_upsell_signal():
    assert score(acc(results_vs_kpi_pct=125, scope_requests_90d=3)).upsell


def test_sample_portfolio():
    hs = [score(a) for a in load(DATA)]
    bands = {h.account.name: h.band for h in hs}
    assert bands["Studio Lumen"] == "at risk" and bands["Grünraum"] == "healthy"
    assert any(h.upsell for h in hs if h.account.name == "Nordlys Skin")
    p = portfolio(hs)
    assert p["at_risk_revenue"] > 0 and "This week's actions" in report(hs)


def test_qbr_uses_structured_output():
    out = {"slides": [{"title": "Results", "points": ["124% of KPI"]}], "talk_track": "Thanks for the quarter."}
    fake = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=out)])))
    assert qbr(score(acc()), client=fake)["slides"][0]["title"] == "Results"
