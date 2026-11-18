# SportZone

Site d'actu sport : actus du jour, résultats, calendriers, classements de 95 compétitions et palmarès depuis 1999.

## Contenu

- `index.html` — le site (une seule page, sans serveur)
- `mentions-legales.html` — page obligatoire, **à compléter** (tout ce qui est entre [crochets])
- `data/` — les données lues par le site :
  - `articles.json` — les actus
  - `results.json` — résultats et matchs à venir
  - `competitions.json` — fiches des compétitions et classements
  - `archive.json` — palmarès 1999–2026
- `scripts/merge.py` — ajoute les nouvelles données du jour dans `data/`

Les données sont mises à jour chaque matin vers 7h45 (heure de Paris) par une tâche automatique de Claude, qui envoie ses modifications dans ce dépôt.

## Mise en ligne avec Netlify

1. Sur [app.netlify.com](https://app.netlify.com) : **Add new site** → **Import an existing project** → **GitHub**.
2. Choisis le dépôt `sportzone`.
3. Laisse **Build command** vide et mets `/` (ou rien) dans **Publish directory**, puis **Deploy**.

Ensuite, chaque mise à jour de ce dépôt met le site en ligne automatiquement.

## Publicité (Google AdSense)

Quand Google a accepté le site, colle son code dans `index.html` aux endroits marqués `ADSENSE`, `PUB 1` et `PUB 2`.

## Attention

Si tu ouvres `index.html` directement sur ton ordinateur (double-clic), les données ne s'affichent pas : c'est normal, il faut passer par l'adresse en ligne.
