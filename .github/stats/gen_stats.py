"""Generates assets/langs-card.svg and assets/activity-card.svg in the site's style.
Run by .github/workflows/stats.yml. Env: GH_TOKEN, GH_USER. Flags: --demo (sample data), --placeholder."""
import base64, json, os, sys, urllib.request
from collections import defaultdict
from xml.sax.saxutils import escape as esc

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "assets"))
BASE, ACC, DEEP, SOFT, INK, INK2, FAINT, TEAL, EDGE, CELL = "#0d0d14", "#6d5fe8", "#4b3dc4", "#a79ff0", "#f2f1f8", "#a8a4c0", "#5c5878", "#4ecdc4", "#2a2840", "#1a1a26"
PAL = [SOFT, ACC, TEAL, DEEP, "#8b83e8", "#2f9e97", "#c9c5ee", FAINT]
LEVELS = [CELL, "#3a3470", DEEP, ACC, SOFT]
FD = os.path.join(os.getcwd(), "node_modules", "@fontsource")
b64 = lambda n: base64.b64encode(open(os.path.join(FD, n), "rb").read()).decode()
CSS = ("@font-face{font-family:'P';font-weight:700;src:url(data:font/woff2;base64,%s) format('woff2')}"
       "@font-face{font-family:'I';font-weight:500;src:url(data:font/woff2;base64,%s) format('woff2')}"
       ".t{font-family:'P',Poppins,Arial,sans-serif;font-weight:700}.b{font-family:'I',Inter,Arial,sans-serif;font-weight:500}"
       ) % (b64("poppins/files/poppins-latin-700-normal.woff2"), b64("inter/files/inter-latin-500-normal.woff2"))

def card(name, w, h, label, body):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
         f'<title>{esc(label)}</title><style>{CSS}</style>'
         f'<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{SOFT}"/><stop offset="1" stop-color="{DEEP}"/></linearGradient></defs>'
         f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="16" fill="{BASE}" stroke="{EDGE}"/>{body}</svg>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, name), "w").write(s)

def title(t, x=28, y=40): return f'<text class="t" x="{x}" y="{y}" font-size="18" fill="url(#g)">{esc(t)}</text>'
def fmt(n): return f"{n:,}"

def build(d):
    langs = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:8]; tot = sum(v for _, v in langs)
    b = [title("Top languages")]
    if not tot:
        b.append(f'<text class="b" x="28" y="100" font-size="14" fill="{INK2}">Updating, check back in a minute.</text>')
    else:
        x = 28; bw = 439
        b.append(f'<clipPath id="c"><rect x="28" y="60" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#c)">')
        for i, (n, v) in enumerate(langs):
            w = bw * v / tot; b.append(f'<rect x="{x:.1f}" y="60" width="{w+.5:.1f}" height="10" fill="{PAL[i]}"/>'); x += w
        b.append("</g>")
        for i, (n, v) in enumerate(langs):
            cx = 28 + (i % 2) * 220; cy = 102 + (i // 2) * 24
            b.append(f'<circle cx="{cx+5}" cy="{cy-4}" r="5" fill="{PAL[i]}"/><text class="b" x="{cx+18}" y="{cy}" font-size="13" fill="{INK}">{esc(n)}</text><text class="b" x="{cx+196}" y="{cy}" font-size="13" fill="{INK2}" text-anchor="end">{100*v/tot:.1f}%</text>')
    card("langs-card.svg", 495, 195, "Top languages", "".join(b))
    # contribution calendar
    weeks = d["days"][-53:]; W = 1000; gap = 3; cw = (W - 56 - gap * (len(weeks) - 1)) / len(weeks); H = int(84 + 7 * (cw + gap) + 24)
    mx = max([c for wk in weeks for c in wk] + [1]); total = sum(c for wk in weeks for c in wk)
    b = [title("Contribution activity"), f'<text class="b" x="{W-28}" y="40" font-size="13" fill="{INK2}" text-anchor="end">{fmt(total)} contributions in the last year</text>']
    for i, wk in enumerate(weeks):
        for j, c in enumerate(wk):
            lv = 0 if c == 0 else 1 + min(3, int(4 * c / (mx + 1)))
            b.append(f'<rect x="{28+i*(cw+gap):.1f}" y="{64+j*(cw+gap):.1f}" width="{cw:.1f}" height="{cw:.1f}" rx="3" fill="{LEVELS[lv]}"/>')
    ly = 64 + 7 * (cw + gap) + 18
    b.append(f'<text class="b" x="{W-28-5*17-34}" y="{ly}" font-size="11" fill="{FAINT}" text-anchor="end">Less</text>')
    for k in range(5): b.append(f'<rect x="{W-28-5*17-26+k*17}" y="{ly-10}" width="12" height="12" rx="3" fill="{LEVELS[k]}"/>')
    b.append(f'<text class="b" x="{W-28}" y="{ly}" font-size="11" fill="{FAINT}" text-anchor="end">More</text>')
    card("activity-card.svg", W, H, "Contribution activity over the last year", "".join(b))

Q = """query($u:String!){user(login:$u){
contributionsCollection{contributionCalendar{weeks{contributionDays{contributionCount}}}}
repositories(ownerAffiliations:OWNER,isFork:false,first:100){nodes{languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""

def fetch(user, token):
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": Q, "variables": {"u": user}}).encode(),
                                 {"Authorization": "bearer " + token, "Content-Type": "application/json", "User-Agent": "stats"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]; langs = defaultdict(int)
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]: langs[e["node"]["name"]] += e["size"]
    days = [[x["contributionCount"] for x in w["contributionDays"]] + [0] * (7 - len(w["contributionDays"])) for w in u["contributionsCollection"]["contributionCalendar"]["weeks"]]
    return dict(langs=dict(langs), days=days)

if __name__ == "__main__":
    if "--placeholder" in sys.argv: d = dict(langs={}, days=[[0] * 7 for _ in range(53)])
    elif "--demo" in sys.argv:
        import random; random.seed(3)
        d = dict(langs=dict(TypeScript=40, Python=30, Java=14, Go=8, Rust=5, HTML=3), days=[[random.choice([0, 0, 1, 3, 6, 12]) for _ in range(7)] for _ in range(53)])
    else: d = fetch(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    build(d)
