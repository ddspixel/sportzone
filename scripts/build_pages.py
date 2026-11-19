#!/usr/bin/env python3
"""Crée une vraie page HTML par joueur (joueurs/<id>.html), la liste des joueurs
(joueurs/index.html) et le sitemap.xml, à partir de data/players.json.

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
@media(max-width:480px){.logo{font-size:28px}header nav a{font-size:13px}h1{font-size:42px}}
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


def page(title, desc, canonical, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="SportZone">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
{extra_head}</head>
<body>
<header><div class="wrap"><a class="logo" href="/">SPORT<span>ZONE</span></a><nav><a href="/">Actus</a><a href="/joueurs/">Joueurs</a><a href="/#results">Résultats</a></nav></div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">© {date.today().year} SportZone · <a href="/">Accueil</a> · <a href="/joueurs/">Tous les joueurs</a> · <a href="/mentions-legales.html">Mentions légales</a></div></footer>
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
    h += f'<div class="sub">{sport_e} {escape(sport_n)}{" · " + escape(club) if club else ""}</div>'
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


def sitemap(players):
    today = date.today().isoformat()
    urls = [(f"{SITE}/", today, "daily", "1.0"), (f"{SITE}/joueurs/", today, "daily", "0.8")]
    urls += [(f"{SITE}/joueurs/{p['id']}.html", p.get("updated") or today, "weekly", "0.7") for p in players]
    urls.append((f"{SITE}/mentions-legales.html", None, "yearly", "0.2"))
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, freq, prio in urls:
        lm = f"<lastmod>{mod}</lastmod>" if mod else ""
        out.append(f"  <url><loc>{loc}</loc>{lm}<changefreq>{freq}</changefreq><priority>{prio}</priority></url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def main():
    players = json.loads((ROOT / "data" / "players.json").read_text(encoding="utf-8"))
    players = [p for p in players if re.fullmatch(r"[a-z0-9-]+", str(p.get("id", ""))) and p.get("name")]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for p in players:
        (OUT / f"{p['id']}.html").write_text(player_page(p), encoding="utf-8")
    (OUT / "index.html").write_text(index_page(players), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(players), encoding="utf-8")
    print(f"OK : {len(players)} pages joueurs + joueurs/index.html + sitemap.xml")


if __name__ == "__main__":
    main()
