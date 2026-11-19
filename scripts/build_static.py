#!/usr/bin/env python3
"""Transforme la page Claude (sportzone.html) en page du site Internet (index.html du dépôt)."""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()

s = re.sub(r'<!-- Publier -->.*?<!-- Lire un article -->', '<!-- Lire un article -->', s, flags=re.S)
s = s.replace('<button class="publish" id="publishBtn">+ Publier</button>', '')
s = re.sub(r'/\* ---------- Publier ---------- \*/.*?function showNotice', "function showNotice", s, flags=re.S)
s = re.sub(r'/\* ---------- Données ---------- \*/.*?</script>', r'''/* ---------- Données (fichiers data/*.json) ---------- */
const h0=location.hash.slice(1); if(validView(h0)) state.view=h0;
render();
async function getJSON(p){ try{ const r=await fetch(p+"?v="+Date.now()); if(!r.ok) return []; return await r.json(); }catch(e){ return null; } }
(async()=>{
  const [a,r,ar,c,pl]=await Promise.all([getJSON("data/articles.json"),getJSON("data/results.json"),getJSON("data/archive.json"),getJSON("data/competitions.json"),getJSON("data/players.json")]);
  if(a===null) showNotice("Impossible de charger les données. Mets le site en ligne pour qu'il fonctionne (voir README).");
  const o={live:0,fin:1,soon:2};
  state.articles=(a||[]).sort((x,y)=>y.createdAt-x.createdAt);
  state.results=(r||[]).sort((x,y)=>(y.date||"").localeCompare(x.date||"")||(o[x.status]-o[y.status])||((x.competition||"").localeCompare(y.competition||"")));
  state.archive=ar||[]; state.comps=c||[]; state.players=pl||[];
  state.loadedA=state.loadedR=true; render();
})();

/* ---------- Bannière cookies ---------- */
(function(){
  let ok=null; try{ ok=localStorage.getItem("cookies"); }catch(e){}
  if(ok) return;
  const b=document.createElement("div"); b.className="cookie";
  b.innerHTML='<span>Ce site utilise des cookies pour la publicité et la mesure d\\'audience. <a href="confidentialite.html">En savoir plus</a></span><span style="display:flex;gap:8px"><button data-c="refuse">Refuser</button><button data-c="accept" class="ok">Accepter</button></span>';
  document.body.appendChild(b);
  b.addEventListener("click",e=>{ const c=e.target.closest("[data-c]"); if(!c) return; try{ localStorage.setItem("cookies",c.dataset.c); }catch(err){} b.remove(); });
})();
</script>''', s, flags=re.S)
s = s.replace('footer{border-top', '''.cookie{position:fixed;left:12px;right:12px;bottom:12px;z-index:60;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;font-size:14px;box-shadow:0 10px 30px rgba(0,0,0,.5)}
.cookie a{color:var(--accent)} .cookie button{padding:8px 14px;border-radius:8px;font-weight:700;border:1px solid var(--line)} .cookie .ok{background:var(--accent);color:#0a0c11;border:0}
.pub{margin:22px 0}
footer{border-top''', 1)
s = s.replace("h+=`<div class=\"layout\"><div>`;\n    if(rest.length){", "h+=`<div class=\"pub\"><!-- PUB 1 : bloc AdSense horizontal --></div>`;\n    h+=`<div class=\"layout\"><div>`;\n    if(rest.length){", 1)
s = s.replace('${state.archive.length?`<div class="box" style="cursor:pointer" data-go="palmares">', '<div class="pub"><!-- PUB 2 : bloc AdSense carré --></div>\n      ${state.archive.length?`<div class="box" style="cursor:pointer" data-go="palmares">', 1)
s = s.replace("<p style=\"margin-top:8px\">© 2026 SportZone. Tous droits réservés.</p>",
              "<p style=\"margin-top:8px\">© 2026 SportZone. Tous droits réservés.</p><p style=\"margin-top:8px\"><a href=\"actus/\">Toutes les actus</a> · <a href=\"equipes/\">Équipes</a> · <a href=\"joueurs/\">Fiches joueurs</a> · <a href=\"mentions-legales.html\">Mentions légales</a> · <a href=\"confidentialite.html\">Confidentialité</a> · <a href=\"contact.html\">Contact</a></p>", 1)
s = s.replace('<title>SportZone — Actus & Résultats</title>', '''<title>SportZone — Actus & Résultats sport</title>
<meta name="google-site-verification" content="RBlbmXCUW-cRgolkeX1qeiO9EuIS8cJRNfKQuTHO4Us" />
<meta name="description" content="SportZone : l'actu sport du jour, les résultats, calendriers, classements et fiches de 95 compétitions et de centaines d'équipes, plus le palmarès depuis 1999.">
<meta name="google-adsense-account" content="ca-pub-8641114671838839">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8641114671838839" crossorigin="anonymous"></script>''')
assert 'claude.use' not in s, "il reste du code Claude"
open(dst, "w", encoding="utf-8").write(s)
print("OK ->", dst)
