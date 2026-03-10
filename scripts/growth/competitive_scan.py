#!/usr/bin/env python3
import json
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass


URL = "https://polymark.et"


@dataclass
class Tool:
    name: str
    href: str
    categories: list[str]
    views: int
    description: str


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; PolymarketPulseBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_tools(html: str) -> list[Tool]:
    m = re.search(r"var allTools = (\[.*?\]);", html, flags=re.S)
    if not m:
        raise RuntimeError("allTools payload not found")
    payload = json.loads(m.group(1))
    tools: list[Tool] = []
    for x in payload:
        tools.append(
            Tool(
                name=str(x.get("name") or "").strip(),
                href="https://polymark.et" + str(x.get("href") or ""),
                categories=[str(c) for c in (x.get("categories") or [])],
                views=int(x.get("views") or 0),
                description=str(x.get("description") or "").strip().replace("\n", " "),
            )
        )
    return tools


def simplify_cluster(categories: list[str]) -> str:
    c = " ".join(categories).lower()
    if "analytics" in c or "dashboard" in c:
        return "analytics/dashboard"
    if "alert" in c:
        return "signals/alerts"
    if "arbitrage" in c:
        return "arbitrage"
    if "portfolio" in c or "whale" in c:
        return "portfolio/whales"
    if "trading" in c or "aggregator" in c:
        return "trading terminal"
    if "ai" in c:
        return "ai agents"
    return "other"


def render_markdown(tools: list[Tool], top_n: int = 30) -> str:
    tools_sorted = sorted(tools, key=lambda t: t.views, reverse=True)
    top = tools_sorted[:top_n]
    clusters = Counter(simplify_cluster(t.categories) for t in tools)

    lines = [
        "# Competitor Sweep (from polymark.et)",
        "",
        f"Total tools parsed: **{len(tools)}**",
        "",
        "## Cluster distribution",
    ]
    for k, v in clusters.most_common():
        lines.append(f"- {k}: {v}")

    lines.extend(
        [
            "",
            "## Top competitors by directory views",
            "",
            "| # | Name | Cluster | Views | Categories | URL |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for i, t in enumerate(top, start=1):
        lines.append(
            f"| {i} | {t.name} | {simplify_cluster(t.categories)} | {t.views} | {', '.join(t.categories)} | {t.href} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    html = fetch_html(URL)
    tools = parse_tools(html)
    print(render_markdown(tools, top_n=30))


if __name__ == "__main__":
    main()
