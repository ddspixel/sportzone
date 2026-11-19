#!/usr/bin/env python3
"""Crée de vraies pages HTML pour Google, à partir de data/*.json :
- joueurs/<id>.html + joueurs/index.html  (une page par joueur)
- actus/<id>.html + actus/index.html      (une page par actu)
- equipes/<sport>-<nom>.html + equipes/index.html (une page par équipe)
- sitemap.xml (toutes les pages)

Usage : python3 scripts/build_pages.py

Netlify lance ce script à chaque mise en ligne (voir netlify.toml), donc les
pages suivent toutes seules les nouvelles fiches ajoutées dans data/players.json.
"""
import json
import re
import shutil
import unicodedata
from datetime import date
from html import escape
from pathlib import Path

SITE = "https://sportzone-8lam.netlify.app"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "joueurs"
OUT_A = ROOT / "actus"
OUT_E = ROOT / "equipes"
TEAM_SPORTS = {"foot", "basket", "rugby", "hand", "hockey", "amfoot", "baseball", "volley"}

SPORTS = {
    "foot": ("Football", "⚽"), "basket": ("Basket", "🏀"), "tennis": ("Tennis", "🎾"),
    "rugby": ("Rugby", "🏉"), "f1": ("F1", "🏎️"), "velo": ("Cyclisme", "🚴"),
    "hand": ("Handball", "🤾"), "mma": ("MMA", "🥋"), "combat": ("Boxe", "🥊"),
    "hockey": ("Hockey sur glace", "🏒"), "amfoot": ("Football américain", "🏈"),
    "baseball": ("Baseball", "⚾"), "volley": ("Volley", "🏐"), "auto": ("Auto / Moto", "🏁"),
    "golf": ("Golf", "⛳"), "athle": ("Athlétisme", "🏃"), "ski": ("Sports d'hiver", "⛷️"),
    "autre": ("Omnisport", "🏅"),
}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]

CSS = """
:root{--bg:#0a0c11;--panel:#12161f;--panel2:#1a1f2c;--line:#232a3a;--text:#f2f4f8;--muted:#8a93a8;--accent:#c6ff3d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6}
a{color:var(--accent)}
.wrap{max-width:900px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--line);background:#05070a}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:60px;gap:12px}
.logo{font-family:'Bebas Neue',Impact,sans-serif;font-size:34px;color:var(--text);text-decoration:none;letter-spacing:.5px}
.logo span{color:var(--accent)}
header nav{display:flex;gap:12px;flex-wrap:wrap;justify-content:flex-end}
header nav a{color:var(--muted);text-decoration:none;font-size:14px}
@media(max-width:480px){.logo{font-size:26px}header nav{gap:8px}header nav a{font-size:12px}h1{font-size:40px}.res{grid-template-columns:70px 1fr auto 1fr;font-size:13px}}
.crumbs{color:var(--muted);font-size:13px;margin:18px 0 6px}
.crumbs a{color:var(--muted)}
h1{font-family:'Bebas Neue',Impact,sans-serif;font-size:52px;line-height:1;letter-spacing:.5px;margin:6px 0}
h2{font-size:18px;margin:26px 0 10px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.sub{color:var(--muted);font-size:15px}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.tags span{background:var(--panel2);border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
.kpi small{display:block;color:var(--muted);font-size:12px}
.kpi b{font-size:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:14px}
ul.pal{padding-left:20px}
ul.pal li{margin:4px 0}
.btn{display:inline-block;background:var(--accent);color:#0a0c11;font-weight:800;border-radius:999px;padding:10px 18px;text-decoration:none;margin-top:22px}
.src{color:var(--muted);font-size:12px;margin-top:22px;word-break:break-word}
.list{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}
.list a{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none;color:var(--text)}
.list a span{display:block;color:var(--muted);font-size:13px}
.res{display:grid;grid-template-columns:90px 1fr auto 1fr;gap:8px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin-top:6px;font-size:14px}
.res .d{color:var(--muted);font-size:12px}.res .s{font-weight:800;text-align:center;min-width:56px}.res .r{text-align:right}
.res a{color:var(--text);text-decoration:none}.res .w{font-weight:800}
.art{font-size:17px}.art p{margin:14px 0}
.al a{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;text-decoration:none;color:var(--text);margin-top:8px}
.al a span{display:block;color:var(--muted);font-size:13px}
table.st{width:100%;border-collapse:collapse;font-size:14px}table.st td,table.st th{padding:6px;border-bottom:1px solid var(--line);text-align:left}table.st tr.me{background:var(--panel2);font-weight:800}
footer{border-top:1px solid var(--line);margin-top:40px;padding:20px 0;color:var(--muted);font-size:13px}
footer a{color:var(--muted)}
"""


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")


def app_id(p):
    """Même identifiant que la fiche dans index.html (#j-<sport>-<nom>)."""
    name = re.sub(r"\s*\(.*\)\s*$", "", str(p.get("name") or "")).strip()
    return "j-" + p.get("sport", "autre") + "-" + slug(name)


def fr_date(iso):
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        return f"{d}{'er' if d == 1 else ''} {MOIS[m - 1]} {y}"
    except Exception:
        return ""


def age(iso):
    try:
        b = date.fromisoformat(iso)
    except Exception:
        return ""
    t = date.today()
    return f"{t.year - b.year - ((t.month, t.day) < (b.month, b.day))} ans"


def linkify(text):
    return re.sub(r"(https?://[^\s<;]+)", r'<a href="\1" rel="nofollow noopener" target="_blank">\1</a>', escape(text))


def page(title, desc, canonical, body, extra_head="", og="profile"):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og}">
<meta property="og:site_name" content="SportZone">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
<meta name="google-adsense-account" content="ca-pub-8641114671838839">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8641114671838839" crossorigin="anonymous"></script>
{extra_head}</head>
<body>
<header><div class="wrap"><a class="logo" href="/">SPORT<span>ZONE</span></a><nav><a href="/actus/">Actus</a><a href="/equipes/">Équipes</a><a href="/joueurs/">Joueurs</a><a href="/#results">Résultats</a></nav></div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">© {date.today().year} SportZone · <a href="/">Accueil</a> · <a href="/actus/">Toutes les actus</a> · <a href="/equipes/">Équipes</a> · <a href="/joueurs/">Joueurs</a> · <a href="/mentions-legales.html">Mentions légales</a> · <a href="/confidentialite.html">Confidentialité</a> · <a href="/contact.html">Contact</a></div></footer>
</body>
</html>
"""


def player_page(p):
    sport_n, sport_e = SPORTS.get(p.get("sport"), SPORTS["autre"])
    name, club = p.get("name", ""), p.get("club", "")
    url = f"{SITE}/joueurs/{p['id']}.html"
    tags = [p.get("poste"), p.get("nationalite")]
    if p.get("naissance"):
        tags.append(f"{age(p['naissance'])} (né le {fr_date(p['naissance'])})")
    tags += [p.get("taille"), ("N° " + p["numero"]) if p.get("numero") else None]
    tags = [t for t in tags if t]

    h = f'<div class="crumbs"><a href="/">SportZone</a> › <a href="/joueurs/">Joueurs</a> › {escape(sport_n)}</div>'
    h += f"<h1>{escape(name)}</h1>"
    h += f'<div class="sub">{sport_e} {escape(sport_n)}{" · " + team_link(p.get("sport"), club) if club else ""}</div>'
    if tags:
        h += '<div class="tags">' + "".join(f"<span>{escape(t)}</span>" for t in tags) + "</div>"
    if p.get("stats"):
        h += f"<h2>Stats {escape(p.get('statsLabel') or 'de la saison')}</h2><div class=\"kpis\">"
        h += "".join(f'<div class="kpi"><small>{escape(str(k))}</small><b>{escape(str(v))}</b></div>' for k, v in p["stats"])
        h += "</div>"
    if p.get("bio"):
        h += f'<div class="card"><p>{escape(p["bio"])}</p>'
        if p.get("updated"):
            h += f'<p class="sub" style="margin-top:8px;font-size:13px">Fiche mise à jour le {fr_date(p["updated"])}</p>'
        h += "</div>"
    if p.get("palmares"):
        h += "<h2>Palmarès</h2><ul class=\"pal\">" + "".join(f"<li>{escape(t)}</li>" for t in p["palmares"]) + "</ul>"
    keys = [norm(name)] + [norm(x) for x in (p.get("aliases") or []) if len(str(x)) >= 5]
    arts = [a for a in CTX["articles"] if any(norm(x) == norm(name) for x in (a.get("players") or []))
            or any(k in norm(a.get("title", "") + " " + a.get("summary", "")) for k in keys)]
    if arts:
        h += f"<h2>Actus {escape(name)}</h2>" + art_list(arts, 8)
    h += f'<a class="btn" href="/#{app_id(p)}">Voir ses matchs et les actus sur SportZone</a>'
    if p.get("sources"):
        h += f'<div class="src">Sources : {linkify(p["sources"])}</div>'

    bits = [p.get("poste"), club]
    title = f"{name} : fiche, stats et palmarès ({club})" if club else f"{name} : fiche, stats et palmarès"
    desc = f"{name}, {' – '.join(b for b in bits if b)}. " if any(bits) else f"{name}. "
    desc += (p.get("bio") or "")
    desc = desc[:155].rsplit(" ", 1)[0] + "…" if len(desc) > 158 else desc

    ld = {"@context": "https://schema.org", "@type": "Person", "name": name, "url": url}
    if p.get("nationalite"): ld["nationality"] = p["nationalite"]
    if p.get("naissance"): ld["birthDate"] = p["naissance"]
    if p.get("taille"): ld["height"] = p["taille"]
    if p.get("poste"): ld["jobTitle"] = p["poste"]
    if club and club.lower() != "retraité": ld["memberOf"] = {"@type": "SportsTeam", "name": club}
    if p.get("aliases"): ld["alternateName"] = p["aliases"]
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    return page(f"{title} | SportZone", desc, url, h, head)


def index_page(players):
    by = {}
    for p in players:
        by.setdefault(p.get("sport", "autre"), []).append(p)
    h = '<div class="crumbs"><a href="/">SportZone</a> › Joueurs</div><h1>Les joueurs</h1>'
    h += f'<div class="sub">{len(players)} fiches : stats de la saison, palmarès et parcours.</div>'
    for k in SPORTS:
        if k not in by:
            continue
        n, e = SPORTS[k]
        h += f"<h2>{e} {escape(n)}</h2><div class=\"list\">"
        for p in sorted(by[k], key=lambda x: x.get("name", "")):
            info = " · ".join(x for x in (p.get("poste"), p.get("club")) if x)
            h += f'<a href="/joueurs/{p["id"]}.html">{escape(p.get("name", ""))}<span>{escape(info)}</span></a>'
        h += "</div>"
    return page("Fiches joueurs : football, basket, tennis, rugby… | SportZone",
                f"Les fiches de {len(players)} sportifs sur SportZone : club, poste, stats de la saison et palmarès.",
                f"{SITE}/joueurs/", h)


# ---------------------------------------------------------------- équipes & actus

CTX = {"aliases": {}, "teams": {}, "articles": [], "players": []}


def load_aliases():
    """Reprend la table des surnoms d'équipes de index.html (PSG = Paris SG…)."""
    try:
        s = (ROOT / "index.html").read_text(encoding="utf-8")
        m = re.search(r"const ALIASES = (\{.*?\n\});", s, re.S)
        js = re.sub(r"(^|\n|\{)\s*(\w+):\[", lambda x: x.group(1) + '"' + x.group(2) + '":[', m.group(1))
        out = {}
        for sp, groups in json.loads(js).items():
            for g in groups:
                for a in g:
                    out[sp + "|" + norm(a)] = g[0]
        return out
    except Exception as e:  # la page reste utilisable sans surnoms
        print("surnoms non chargés :", e)
        return {}


def clean_team(n):
    return re.sub(r"\s*\((est|ouest)\)\s*$", "", str(n or ""), flags=re.I).strip()


def canon(sport, name):
    c = clean_team(name)
    return CTX["aliases"].get(sport + "|" + norm(c), c)


def team_id(sport, name):
    return sport + "-" + slug(canon(sport, name))


def team_url(sport, name):
    tid = team_id(sport, name)
    return f"/equipes/{tid}.html" if tid in CTX["teams"] else None


def team_link(sport, name, cls=""):
    u = team_url(sport, name)
    c = f' class="{cls}"' if cls else ""
    return f'<a href="{u}"{c}>{escape(name)}</a>' if u else f"<span{c}>{escape(name)}</span>"


def player_url(name):
    k = norm(re.sub(r"\s*\(.*\)\s*$", "", str(name or "")).strip())
    for p in CTX["players"]:
        if norm(p.get("name")) == k:
            return f"/joueurs/{p['id']}.html"
    return None


def fr_ms(ms):
    try:
        from datetime import datetime, timezone, timedelta
        d = datetime.fromtimestamp(ms / 1000, tz=timezone(timedelta(hours=1)))
        return fr_date(d.date().isoformat()), d.date().isoformat(), d.isoformat()
    except Exception:
        return "", "", ""


def collect_teams(results, articles, comps, players):
    teams = {}

    def add(sport, name):
        if sport not in TEAM_SPORTS or not clean_team(name):
            return None
        tid = team_id(sport, name)
        t = teams.setdefault(tid, {"id": tid, "sport": sport, "name": canon(sport, name),
                                   "results": [], "articles": [], "standings": [], "players": []})
        return t

    for r in results:
        for side in ("home", "away"):
            t = add(r.get("sport"), r.get(side))
            if t:
                t["results"].append(r)
    for a in articles:
        for n in a.get("teams") or []:
            t = add(a.get("sport"), n)
            if t:
                t["articles"].append(a)
    for c in comps:
        for row in c.get("standings") or []:
            tid = team_id(c.get("sport"), row.get("team"))
            if tid in teams:
                teams[tid]["standings"].append((c, row))
    for p in players:
        tid = team_id(p.get("sport"), p.get("club"))
        if tid in teams:
            teams[tid]["players"].append(p)
    # une page seulement si l'équipe a de la matière
    return {k: v for k, v in teams.items() if len(v["results"]) + 2 * len(v["articles"]) + len(v["standings"]) >= 2}


def res_row(r, team=None):
    sport = r.get("sport")
    fin = r.get("status") == "fin"
    hs, as_ = r.get("homeScore", ""), r.get("awayScore", "")
    win = None
    try:
        win = "home" if float(hs) > float(as_) else "away" if float(as_) > float(hs) else None
    except Exception:
        pass
    score = f"{escape(hs)} - {escape(as_)}" if fin else escape(r.get("time") or "à venir")
    d = fr_date(r.get("date", "")).rsplit(" ", 1)[0]
    return (f'<div class="res"><span class="d">{escape(d)}<br>{escape(r.get("competition", ""))[:28]}</span>'
            f'<span class="r">{team_link(sport, r.get("home", ""), "w" if win == "home" else "")}</span>'
            f'<span class="s">{score}</span>{team_link(sport, r.get("away", ""), "w" if win == "away" else "")}</div>')


def art_list(arts, n=10):
    h = '<div class="al">'
    for a in arts[:n]:
        h += f'<a href="/actus/{a["id"]}.html">{escape(a.get("title", ""))}<span>{fr_ms(a.get("createdAt", 0))[0]} · {escape(a.get("summary", ""))[:140]}</span></a>'
    return h + "</div>"


def team_page(t):
    sport_n, sport_e = SPORTS.get(t["sport"], SPORTS["autre"])
    name = t["name"]
    url = f"{SITE}/equipes/{t['id']}.html"
    res = sorted(t["results"], key=lambda r: (r.get("date", ""), r.get("time", "")))
    past = [r for r in res if r.get("status") == "fin"][::-1]
    nxt = [r for r in res if r.get("status") != "fin"]
    arts = sorted(t["articles"], key=lambda a: -a.get("createdAt", 0))

    h = f'<div class="crumbs"><a href="/">SportZone</a> › <a href="/equipes/">Équipes</a> › {escape(sport_n)}</div>'
    h += f"<h1>{escape(name)}</h1><div class=\"sub\">{sport_e} {escape(sport_n)}"
    if t["standings"]:
        c, row = t["standings"][0]
        h += f" · {row.get('pos')}<sup>e</sup> de {escape(c.get('name', ''))} ({row.get('pts')} pts)"
    h += "</div>"
    if past:
        form = []
        for r in past[:5]:
            me = "home" if team_id(t["sport"], r.get("home")) == t["id"] else "away"
            try:
                a, b = float(r.get("homeScore")), float(r.get("awayScore"))
                if me == "away":
                    a, b = b, a
                form.append("V" if a > b else "D" if a < b else "N")
            except Exception:
                pass
        if form:
            h += '<div class="tags">' + "".join(f"<span>{x}</span>" for x in form) + "</div>"
    if nxt:
        h += "<h2>Prochains matchs</h2>" + "".join(res_row(r) for r in nxt[:6])
    if past:
        h += "<h2>Derniers résultats</h2>" + "".join(res_row(r) for r in past[:10])
    for c, row in t["standings"]:
        st = c.get("standings") or []
        i = next((k for k, x in enumerate(st) if x is row), 0)
        part = st[max(0, i - 3): i + 4]
        h += f"<h2>Classement — {escape(c.get('name', ''))}</h2><table class=\"st\"><tr><th>#</th><th>Équipe</th><th>J</th><th>Pts</th></tr>"
        for x in part:
            me = ' class="me"' if x is row else ""
            h += f"<tr{me}><td>{x.get('pos')}</td><td>{team_link(c.get('sport'), x.get('team', ''))}</td><td>{x.get('j', '')}</td><td>{x.get('pts', '')}</td></tr>"
        h += "</table>"
    if arts:
        h += f"<h2>Actus {escape(name)}</h2>" + art_list(arts)
    if t["players"]:
        h += "<h2>Joueurs</h2><div class=\"list\">" + "".join(
            f'<a href="/joueurs/{p["id"]}.html">{escape(p.get("name", ""))}<span>{escape(p.get("poste", ""))}</span></a>'
            for p in sorted(t["players"], key=lambda p: p.get("name", ""))) + "</div>"
    h += f'<a class="btn" href="/#t-{t["id"]}">Fiche complète de {escape(name)} sur SportZone</a>'

    title = f"{name} : résultats, calendrier, classement et actus | SportZone"
    bits = []
    if t["standings"]:
        c, row = t["standings"][0]
        bits.append(f"{row.get('pos')}e de {c.get('name')}")
    if nxt:
        r = nxt[0]
        bits.append(f"prochain match {r.get('home')} - {r.get('away')} le {fr_date(r.get('date', ''))}")
    desc = f"{name} ({sport_n}) : derniers résultats, prochains matchs, classement et actus. " + (", ".join(bits) + "." if bits else "")
    ld = {"@context": "https://schema.org", "@type": "SportsTeam", "name": name, "sport": sport_n, "url": url}
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    return page(title, desc[:160], url, h, head, og="website")


def article_page(a):
    sport_n, sport_e = SPORTS.get(a.get("sport"), SPORTS["autre"])
    url = f"{SITE}/actus/{a['id']}.html"
    when, iso, full = fr_ms(a.get("createdAt", 0))
    content = a.get("content", "")
    src = ""
    m = re.search(r"\n\s*Sources?\s*:\s*(.*)$", content, re.S)
    if m:
        src, content = m.group(1).strip(), content[: m.start()]
    paras = [x.strip() for x in re.split(r"\n\s*\n", content) if x.strip()]

    h = f'<div class="crumbs"><a href="/">SportZone</a> › <a href="/actus/">Actus</a> › {escape(sport_n)}</div>'
    h += f'<h1 style="font-size:42px">{escape(a.get("title", ""))}</h1>'
    h += f'<div class="sub">{sport_e} {escape(sport_n)} · {when}</div>'
    if a.get("summary"):
        h += f'<p class="card" style="font-weight:600">{escape(a["summary"])}</p>'
    h += '<div class="art">' + "".join(f"<p>{escape(x)}</p>" for x in paras) + "</div>"
    links = []
    for n in a.get("teams") or []:
        u = team_url(a.get("sport"), n)
        if u:
            links.append(f'<a href="{u}">{escape(canon(a.get("sport"), n))}</a>')
    for n in a.get("players") or []:
        u = player_url(n)
        if u:
            links.append(f'<a href="{u}">{escape(n)}</a>')
    if links:
        h += "<h2>Dans cet article</h2><div class=\"tags\">" + "".join(f"<span>{l}</span>" for l in links) + "</div>"
    same = [x for x in CTX["articles"] if x is not a and x.get("sport") == a.get("sport")][:5]
    if same:
        h += f"<h2>Autres actus {escape(sport_n)}</h2>" + art_list(same, 5)
    if src:
        h += f'<div class="src">Sources : {linkify(src)}</div>'

    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": a.get("title", "")[:110],
          "description": a.get("summary", ""), "url": url, "mainEntityOfPage": url,
          "author": {"@type": "Organization", "name": "SportZone"},
          "publisher": {"@type": "Organization", "name": "SportZone"}, "articleSection": sport_n}
    if full:
        ld["datePublished"] = full
        ld["dateModified"] = full
    head = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    if full:
        head += f'<meta property="article:published_time" content="{full}">\n'
    return page(f"{a.get('title', '')} | SportZone", (a.get("summary") or "")[:160], url, h, head, og="article")


def actus_index(articles):
    h = '<div class="crumbs"><a href="/">SportZone</a> › Actus</div><h1>Toutes les actus</h1>'
    h += f'<div class="sub">{len(articles)} articles : foot, basket, tennis, rugby, F1, MMA…</div>'
    by = {}
    for a in articles:
        by.setdefault(a.get("sport", "autre"), []).append(a)
    h += "<h2>Les plus récentes</h2>" + art_list(articles, 30)
    for k in SPORTS:
        if k in by and len(by[k]) > 0:
            n, e = SPORTS[k]
            h += f"<h2>{e} {escape(n)}</h2>" + art_list(by[k], 20)
    return page("Actus sport du jour : foot, basket, tennis, rugby, F1 | SportZone",
                "Toutes les actus sport de SportZone : Ligue 1, PSG, OM, NBA, Top 14, tennis, F1, MMA, mises à jour chaque jour.",
                f"{SITE}/actus/", h, og="website")


def equipes_index(teams):
    by = {}
    for t in teams.values():
        by.setdefault(t["sport"], []).append(t)
    h = '<div class="crumbs"><a href="/">SportZone</a> › Équipes</div><h1>Les équipes</h1>'
    h += f'<div class="sub">{len(teams)} équipes : résultats, calendrier, classement et actus.</div>'
    for k in SPORTS:
        if k not in by:
            continue
        n, e = SPORTS[k]
        h += f"<h2>{e} {escape(n)}</h2><div class=\"list\">"
        for t in sorted(by[k], key=lambda x: x["name"]):
            info = f"{len(t['articles'])} actu(s) · {len(t['results'])} match(s)"
            h += f'<a href="/equipes/{t["id"]}.html">{escape(t["name"])}<span>{info}</span></a>'
        h += "</div>"
    return page("Équipes : PSG, OM, Real, NBA, Top 14… résultats et actus | SportZone",
                f"Les fiches de {len(teams)} équipes sur SportZone : derniers résultats, prochains matchs, classement et actus.",
                f"{SITE}/equipes/", h, og="website")


def sitemap(players, articles, teams):
    today = date.today().isoformat()
    urls = [(f"{SITE}/", today, "hourly", "1.0"), (f"{SITE}/actus/", today, "hourly", "0.9"),
            (f"{SITE}/equipes/", today, "daily", "0.8"), (f"{SITE}/joueurs/", today, "daily", "0.8")]
    urls += [(f"{SITE}/actus/{a['id']}.html", fr_ms(a.get("createdAt", 0))[1] or today, "weekly", "0.8") for a in articles]
    urls += [(f"{SITE}/equipes/{t}.html", today, "daily", "0.7") for t in sorted(teams)]
    urls += [(f"{SITE}/joueurs/{p['id']}.html", p.get("updated") or today, "weekly", "0.7") for p in players]
    urls += [(f"{SITE}/{x}.html", None, "yearly", "0.2") for x in ("mentions-legales", "confidentialite", "contact")]
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, freq, prio in urls:
        lm = f"<lastmod>{mod}</lastmod>" if mod else ""
        out.append(f"  <url><loc>{loc}</loc>{lm}<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def load(name):
    try:
        return json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))
    except Exception as e:
        print(f"data/{name}.json illisible :", e)
        return []


def fresh(d):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()


def main():
    ok = lambda x: re.fullmatch(r"[a-z0-9-]+", str(x.get("id", "")))
    players = [p for p in load("players") if ok(p) and p.get("name")]
    articles = sorted([a for a in load("articles") if ok(a) and a.get("title")], key=lambda a: -a.get("createdAt", 0))
    results, comps = load("results"), load("competitions")
    CTX["aliases"] = load_aliases()
    CTX["players"], CTX["articles"] = players, articles
    CTX["teams"] = teams = collect_teams(results, articles, comps, players)

    fresh(OUT)
    for p in players:
        (OUT / f"{p['id']}.html").write_text(player_page(p), encoding="utf-8")
    (OUT / "index.html").write_text(index_page(players), encoding="utf-8")
    fresh(OUT_A)
    for a in articles:
        (OUT_A / f"{a['id']}.html").write_text(article_page(a), encoding="utf-8")
    (OUT_A / "index.html").write_text(actus_index(articles), encoding="utf-8")
    fresh(OUT_E)
    for t in teams.values():
        (OUT_E / f"{t['id']}.html").write_text(team_page(t), encoding="utf-8")
    (OUT_E / "index.html").write_text(equipes_index(teams), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(players, articles, teams), encoding="utf-8")
    print(f"OK : {len(players)} joueurs, {len(articles)} actus, {len(teams)} équipes + sitemap.xml")


if __name__ == "__main__":
    main()
