#!/usr/bin/env python3
"""Render profile stat cards from the GitHub GraphQL API into assets/*.svg.

All data is fetched before any file is written, so a failed run leaves the
previously committed cards untouched.
"""
import json
import os
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "LucdeMarillacStJulien")
OUT = Path(os.environ.get("OUT_DIR", "assets"))

BG = "#1a1b27"
TITLE = "#70a5fd"
VALUE = "#38bdae"
LABEL = "#a9b1d6"
ACCENT = "#fe428e"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"

PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    repositoriesContributedTo(first: 1, includeUserRepositories: true,
                              contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {
      totalCount
    }
  }
}
"""

YEAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": USER,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    user = (body.get("data") or {}).get("user")
    if body.get("errors") or not user:
        raise RuntimeError(f"GraphQL request failed: {body.get('errors')}")
    return user


def fetch():
    profile = gql(PROFILE_QUERY, {"login": USER})
    now = datetime.now(timezone.utc)
    today = now.date()

    days, commits = {}, 0
    for year in range(int(profile["createdAt"][:4]), today.year + 1):
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if year == today.year else f"{year}-12-31T23:59:59Z"
        coll = gql(YEAR_QUERY, {"login": USER, "from": f"{year}-01-01T00:00:00Z", "to": end})
        coll = coll["contributionsCollection"]
        commits += coll["totalCommitContributions"]
        for week in coll["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                day = date.fromisoformat(d["date"])
                if day <= today:
                    days[day] = d["contributionCount"]

    longest, run_start, run_len = (0, None, None), None, 0
    for day in sorted(days):
        if days[day] > 0:
            run_start = day if run_len == 0 else run_start
            run_len += 1
            if run_len > longest[0]:
                longest = (run_len, run_start, day)
        else:
            run_len = 0

    # Today not having a contribution yet doesn't break the streak.
    end = today if days.get(today, 0) > 0 else today - timedelta(days=1)
    cursor, current_len = end, 0
    while days.get(cursor, 0) > 0:
        current_len += 1
        cursor -= timedelta(days=1)
    current = (current_len, cursor + timedelta(days=1), end)

    sizes, colors = defaultdict(int), {}
    for repo in profile["repositories"]["nodes"]:
        if repo["name"].lower() == USER.lower():
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] += edge["size"]
            colors[name] = edge["node"]["color"] or "#858585"
    total_size = sum(sizes.values())
    languages = [
        (name, colors[name], size / total_size * 100)
        for name, size in sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)[:6]
    ]

    return {
        "contributions": sum(days.values()),
        "commits": commits,
        "repos": profile["repositories"]["totalCount"],
        "contributed": profile["repositoriesContributedTo"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in profile["repositories"]["nodes"]),
        "languages": languages,
        "current": current,
        "longest": longest,
        "first_day": min((d for d, c in days.items() if c > 0), default=today),
        "today": today,
    }


def fmt_day(d, today):
    return f"{d:%b} {d.day}" if d.year == today.year else f"{d:%b} {d.day}, {d.year}"


def fmt_range(start, end, today):
    if start is None:
        return "No streak yet"
    if start == end:
        return fmt_day(start, today)
    return f"{fmt_day(start, today)} – {fmt_day(end, today)}"


def card(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
<style>
.t {{ font: 600 18px {FONT}; fill: {TITLE}; }}
.l {{ font: 400 14px {FONT}; fill: {LABEL}; }}
.v {{ font: 700 14px {FONT}; fill: {VALUE}; }}
.big {{ font: 700 28px {FONT}; fill: {VALUE}; }}
.s {{ font: 400 12px {FONT}; fill: {LABEL}; }}
.f {{ font: 400 10px {FONT}; fill: {LABEL}; opacity: .55; }}
</style>
<rect width="{width}" height="{height}" rx="6" fill="{BG}"/>
{body}
</svg>
"""


def render_stats(d):
    rows = [
        ("Total contributions", d["contributions"]),
        ("Commits", d["commits"]),
        ("Public repositories", d["repos"]),
        ("Repositories contributed to", d["contributed"]),
        ("Stars earned", d["stars"]),
    ]
    body = ['<text x="25" y="38" class="t">GitHub Stats</text>']
    for i, (label, value) in enumerate(rows):
        y = 72 + i * 26
        body.append(f'<text x="25" y="{y}" class="l">{label}</text>')
        body.append(f'<text x="365" y="{y}" class="v" text-anchor="end">{value:,}</text>')
    body.append(f'<text x="365" y="200" class="f" text-anchor="end">Updated {d["today"]:%Y-%m-%d}</text>')
    return card(390, 212, "GitHub stats", "\n".join(body))


def render_languages(d):
    langs = d["languages"]
    body = ['<text x="25" y="38" class="t">Top Languages</text>']
    if not langs:
        body.append('<text x="25" y="80" class="l">No public code yet</text>')
        return card(390, 212, "Top languages", "\n".join(body))

    body.append('<clipPath id="bar"><rect x="25" y="55" width="340" height="10" rx="5"/></clipPath>')
    body.append('<g clip-path="url(#bar)">')
    x = 25.0
    for name, color, pct in langs:
        w = 340 * pct / 100
        body.append(f'<rect x="{x:.2f}" y="55" width="{w + 0.5:.2f}" height="10" fill="{color}"/>')
        x += w
    body.append("</g>")

    for i, (name, color, pct) in enumerate(langs):
        col, row = i % 2, i // 2
        cx, cy = 30 + col * 175, 98 + row * 30
        body.append(f'<circle cx="{cx}" cy="{cy - 5}" r="5" fill="{color}"/>')
        body.append(f'<text x="{cx + 12}" y="{cy}" class="l">{escape(name)} <tspan class="s">{pct:.1f}%</tspan></text>')
    body.append(f'<text x="365" y="200" class="f" text-anchor="end">By code size, public repos</text>')
    return card(390, 212, "Top languages", "\n".join(body))


def render_streak(d):
    today = d["today"]
    cur_len, cur_start, cur_end = d["current"]
    long_len, long_start, long_end = d["longest"]
    columns = [
        (130, f"{d['contributions']:,}", "Total Contributions", f"{fmt_day(d['first_day'], today)} – Present"),
        (390, f"{cur_len:,}", "Current Streak", fmt_range(cur_start, cur_end, today) if cur_len else "Start one today"),
        (650, f"{long_len:,}", "Longest Streak", fmt_range(long_start, long_end, today)),
    ]
    body = [
        f'<line x1="260" y1="30" x2="260" y2="170" stroke="{LABEL}" stroke-opacity=".25"/>',
        f'<line x1="520" y1="30" x2="520" y2="170" stroke="{LABEL}" stroke-opacity=".25"/>',
        f'<circle cx="390" cy="72" r="40" fill="none" stroke="{ACCENT}" stroke-width="5"/>',
    ]
    for x, number, label, sub in columns:
        body.append(f'<text x="{x}" y="{82}" class="big" text-anchor="middle">{number}</text>')
        body.append(f'<text x="{x}" y="140" class="l" text-anchor="middle">{label}</text>')
        body.append(f'<text x="{x}" y="163" class="s" text-anchor="middle">{sub}</text>')
    return card(780, 195, "GitHub contribution streak", "\n".join(body))


def main():
    data = fetch()
    cards = {
        "stats.svg": render_stats(data),
        "languages.svg": render_languages(data),
        "streak.svg": render_streak(data),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in cards.items():
        (OUT / name).write_text(svg, encoding="utf-8")
    print(f"Wrote {', '.join(cards)} to {OUT}/")


if __name__ == "__main__":
    main()
