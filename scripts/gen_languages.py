#!/usr/bin/env python3
"""gen_languages — the animated language bars card for the profile README.

Driven by repository language byte counts from the GitHub API (private
repositories included when the token allows it, forks excluded):

  assets/languages.svg   horizontal bars — top 8 + "other"

Monochrome hacker-terminal aesthetic (cardlib: BG/TEXT/DIM/TRACK greys, no
chromatic color). Every language gets its own grey via grey_ramp().

ARCHIVE_REPOS (the static CTFd archive) is always excluded from the stats:
its ~62 MB of generated/vendor HTML does not represent actual work and, when
it was previously merged, it pushed HTML to #1 on the profile. It is skipped
like forks (this rationale lives here in code, never on the rendered cards).

Run plain for the animated card. CARDS_QA=1 emits the final static frame
plus a languages-meta.json geometry sidecar into .tmp/qa/ for the pixel QA
loop (.tmp/qa/render.mjs + .tmp/qa/inspect.py).

Token resolution: METRICS_TOKEN env var, else `gh auth token` when running
locally. With neither, the committed card is left untouched (exit 0).
"""

import json
import os
import subprocess
import urllib.error
import urllib.request

import cardlib as C

USER = os.environ.get("GITHUB_USER", "1nv1sibl3")
ARCHIVE_REPOS = {"BlitzCTF-2025"}  # static CTFd archive — always skipped (see
#                                  module docstring: 62 MB of generated HTML,
#                                  not representative of actual work)
BARS_TOP = 8
OTHER_MIN = 0.5  # % — smaller remainders are dropped entirely
MIN_SHARE = OTHER_MIN  # % — a language must clear the same bar as "other"
#                      to earn its own row: below 0.5% a bar collapses to
#                      the 9px floor, so such languages fold into "other".
API = "https://api.github.com"

# ── bars card geometry ───────────────────────────────────────────────────
W = 760
PROMPT_Y = 64
ROW_Y0, ROW_STEP = 92, 26
DOT_CX, NAME_X = 34, 50
BAR_X, BAR_W, BAR_H, BAR_RX = 210, 466, 9, 4.5
PCT_X = 736
INFO_GAP, BOT_GAP, BOT_PAD = 30, 28, 30


def fmt(v):
    """Trim a number for SVG output (466.0 → 466, 434.23 → 434.23)."""
    s = f"{float(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


# ── data pipeline ────────────────────────────────────────────────────────

def resolve_token():
    tok = (os.environ.get("METRICS_TOKEN") or "").strip()
    if tok:
        return tok
    if os.environ.get("GITHUB_ACTIONS"):
        return ""  # no PAT secret configured — keep the committed cards
    try:  # local fallback: the authenticated gh CLI
        return subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return ""


def api(path, tok):
    req = urllib.request.Request(
        API + path,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-language-cards",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def owned_repos(tok):
    """Every non-fork repo owned by USER (paginated)."""
    repos, page = [], 1
    while True:
        batch = api(
            f"/user/repos?per_page=100&page={page}&affiliation=owner&sort=pushed",
            tok,
        )
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return [
        repo for repo in repos
        if repo["owner"]["login"] == USER and not repo["fork"]
    ]


def language_bytes(repos, tok):
    totals = {}
    for repo in repos:
        try:
            langs = api(f"/repos/{repo['full_name']}/languages", tok)
        except urllib.error.HTTPError as err:
            print(f"skipping {repo['name']}: HTTP {err.code}")
            continue
        for lang, nbytes in langs.items():
            totals[lang] = totals.get(lang, 0) + nbytes
    return totals


def build_rows(totals, top):
    """[(name, share%, is_other)] — top N (each ≥ MIN_SHARE) plus "other"
    if the remainder is big enough to deserve a row."""
    total = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    kept = [(lang, nbytes / total * 100.0) for lang, nbytes in ranked
            if nbytes / total * 100.0 >= MIN_SHARE]
    rows = [(lang, share, False) for lang, share in kept[:top]]
    other = 100.0 - sum(share for _, share, _ in rows)
    if other >= OTHER_MIN:
        rows.append(("other", other, True))
    return rows


# ── bars card ────────────────────────────────────────────────────────────

def bars_card(rows, n_repos, n_priv):
    nr = len(rows)
    n = sum(1 for _, _, is_other in rows if not is_other)  # ramp length
    max_share = max(share for _, share, _ in rows)
    info_y = ROW_Y0 + (nr - 1) * ROW_STEP + INFO_GAP
    bot_y = info_y + BOT_GAP
    height = bot_y + BOT_PAD

    note = f"// {n_repos} repositories · {n_priv} private · forks excluded"

    p = [C.txt(24, PROMPT_Y, "$ languages --top 8 --all",
               fill=C.ACCENT, appear=0.1)]
    meta_rows = []
    for i, (name, share, is_other) in enumerate(rows):
        y = ROW_Y0 + i * ROW_STEP
        t = 0.15 + 0.09 * i
        grey = C.DIM if is_other else C.grey_ramp(i, n)
        fill_w = max(9.0, BAR_W * share / max_share)
        if not is_other:
            p.append(f'<circle cx="{DOT_CX}" cy="{y - 4}" r="4.5" fill="{grey}"/>')
        p.append(C.txt(NAME_X, y, name,
                       fill=C.DIM if is_other else C.TEXT, appear=t))
        p.append(f'<rect x="{BAR_X}" y="{y - 8.5}" width="{BAR_W}" '
                 f'height="{BAR_H}" rx="{BAR_RX}" fill="{C.TRACK}"/>')
        if C.QA:
            p.append(f'<rect x="{BAR_X}" y="{y - 8.5}" width="{fmt(fill_w)}" '
                     f'height="{BAR_H}" rx="{BAR_RX}" fill="{grey}"/>')
        else:
            p.append(
                f'<rect x="{BAR_X}" y="{y - 8.5}" width="9" height="{BAR_H}" '
                f'rx="{BAR_RX}" fill="{grey}">'
                f'<animate attributeName="width" values="9;{fmt(fill_w)}" '
                f'keyTimes="0;1" calcMode="spline" keySplines="0.3 0 0.2 1" '
                f'dur="0.7s" begin="{fmt(t)}s" fill="freeze"/></rect>')
        p.append(C.txt(PCT_X, y, f"{share:.1f}%", anchor="end",
                       fill=C.DIM if is_other else C.ACCENT, appear=t))
        meta_rows.append({
            "name": name, "pct": f"{share:.1f}%", "share": share,
            "baseline": y, "is_other": is_other, "color": grey,
            "fill_w": fill_w,
        })

    p.append(C.txt(24, info_y, note, size=11, fill=C.DIM,
                   appear=0.15 + 0.09 * (nr - 1) + 0.35))
    p.append(C.txt(24, bot_y, "$", fill=C.ACCENT,
                   appear=0.15 + 0.09 * (nr - 1) + 0.95))
    p.append(C.blink(40, bot_y - 11))

    svg = C.window(W, height, "inv1s1bl3@github:~ — languages", "".join(p),
                   aria=(f"language statistics for {USER} — "
                         f"top {nr} across {n_repos} repositories"),
                   scan=True)
    meta = {"kind": "bars", "width": W, "height": height, "n_rows": nr,
            "info": note, "info_y": info_y, "bot_y": bot_y, "rows": meta_rows}
    return svg, meta


# ── driver ───────────────────────────────────────────────────────────────

def main():
    tok = resolve_token()
    if not tok:
        print("no token available — keeping existing cards")
        return
    try:
        repos = owned_repos(tok)
    except urllib.error.HTTPError as err:
        raise SystemExit(f"github api error while listing repos: HTTP {err.code}")

    # ARCHIVE_REPOS are skipped like forks — never fetched, never counted
    # (the static CTFd archive's generated HTML is not representative work)
    counted = [r for r in repos if r["name"] not in ARCHIVE_REPOS]

    totals = language_bytes(counted, tok)
    if not totals:
        raise SystemExit("no language data found")

    n_repos = len(counted)
    n_priv = sum(1 for r in counted if r["private"])
    print(f"repositories: {n_repos} total · {n_priv} private · forks excluded")

    bar_rows = build_rows(totals, BARS_TOP)

    C.OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg, meta = bars_card(bar_rows, n_repos, n_priv)
    out = C.OUT_DIR / "languages.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"wrote {out} ({len(svg.encode('utf-8'))} bytes)")
    if C.QA:
        (C.OUT_DIR / "languages-meta.json").write_text(
            json.dumps(meta, indent=1), encoding="utf-8")

    top = ", ".join(f"{name} {share:.1f}%"
                    for name, share, _ in bar_rows if name != "other")
    print(f"top languages: {top}")


if __name__ == "__main__":
    main()
