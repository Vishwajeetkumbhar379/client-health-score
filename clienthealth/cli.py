"""clienthealth data/accounts.csv  →  portfolio report;  --qbr "Account" drafts a QBR outline with Claude."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .scoring import load, portfolio, score

MODEL = os.environ.get("CLIENTHEALTH_MODEL", "claude-sonnet-4-5")
DOT = {"healthy": "🟢", "watch": "🟠", "at risk": "🔴"}


def report(hs) -> str:
    p = portfolio(hs)
    hs = sorted(hs, key=lambda h: h.score)
    L = ["# Client portfolio health", "",
         f"**{p['accounts']} accounts · EUR {p['monthly_revenue']:,.0f}/month** · "
         f"at risk EUR {p['at_risk_revenue']:,.0f} · watch EUR {p['watch_revenue']:,.0f} · {p['upsell_candidates']} upsell candidate(s)", "",
         "| Account | Health | Results | Relationship | Delivery | Commercial | Stability | Retainer |",
         "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for h in hs:
        pl = h.pillars
        L.append(f"| {DOT[h.band]} {h.account.name} | **{h.score:.0f}** | {pl['results']} | {pl['relationship']} | {pl['delivery']} | "
                 f"{pl['commercial']} | {pl['stability']} | EUR {h.account.retainer_eur:,.0f} |")
    L += ["", "## This week's actions", ""]
    for h in hs:
        if h.band == "healthy" and not h.upsell:
            continue
        L += [f"### {DOT[h.band]} {h.account.name} · {h.score:.0f} · {h.band}", ""]
        L += [f"- **Why:** {d}" for d in h.drivers]
        L += [f"- **Do:** {x}" for x in h.actions[:3]]
        L += [f"- **Grow:** {u}" for u in h.upsell]
        L.append("")
    L.append("<sub>Weights: results 30%, relationship 25%, delivery 20%, commercial 15%, stability 10%. Accounts are fictional.</sub>")
    return "\n".join(L) + "\n"


QBR_TOOL = {
    "name": "qbr_outline",
    "description": "Outline a quarterly business review deck.",
    "input_schema": {"type": "object", "properties": {
        "slides": {"type": "array", "items": {"type": "object", "properties": {
            "title": {"type": "string"}, "points": {"type": "array", "items": {"type": "string"}}}, "required": ["title", "points"]}},
        "talk_track": {"type": "string", "description": "How to open the meeting, 3 sentences"}},
        "required": ["slides", "talk_track"]},
}


def qbr(h, client=None) -> dict:
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    data = {"account": h.account.__dict__, "health": h.score, "band": h.band, "pillars": h.pillars,
            "drivers": h.drivers, "actions": h.actions, "upsell": h.upsell}
    msg = client.messages.create(
        model=MODEL, max_tokens=1200, tools=[QBR_TOOL], tool_choice={"type": "tool", "name": "qbr_outline"},
        system="You are a senior account director. Outline an honest, client-friendly QBR in 6-8 slides. "
               "Lead with results, own the problems, end with next quarter's plan. Use only the numbers provided.",
        messages=[{"role": "user", "content": json.dumps(data, indent=1)}])
    return dict(next(b for b in msg.content if getattr(b, "type", "") == "tool_use").input)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="clienthealth")
    ap.add_argument("csv", type=Path)
    ap.add_argument("--out", type=Path, default=Path("reports/portfolio_health.md"))
    ap.add_argument("--qbr", metavar="ACCOUNT", help="Draft a QBR outline for one account with Claude")
    a = ap.parse_args(argv)
    hs = [score(x) for x in load(a.csv)]
    md = report(hs)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(md, encoding="utf-8")
    print(md)
    if a.qbr:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Set ANTHROPIC_API_KEY for --qbr", file=sys.stderr)
            return 1
        h = next(h for h in hs if h.account.name.lower() == a.qbr.lower())
        print(json.dumps(qbr(h), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
