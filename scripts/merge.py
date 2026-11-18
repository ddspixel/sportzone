#!/usr/bin/env python3
"""Fusionne de nouvelles données dans data/*.json.

Usage : python3 scripts/merge.py nouveau.json

nouveau.json contient un objet avec une ou plusieurs de ces listes :
  {"articles": [...], "results": [...], "competitions": [...], "players": [...]}
Chaque élément doit avoir un "id" (le dernier morceau de son chemin dans la base,
par ex. "2026-11-18-foot-psg-om" ou "ligue-1").
- articles et results : l'élément remplace celui qui a le même id.
- competitions et players : les champs donnés sont fusionnés dans la compétition existante
  (pratique pour ne mettre à jour que "standings" et "standingsUpdated").
Les vieux résultats (plus de 60 jours) et les vieilles actus (au-delà des 2000
plus récentes) sont retirés pour garder le site léger.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    p = DATA / f"{name}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(name, items):
    (DATA / f"{name}.json").write_text(
        json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def main():
    new = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    counts = {}
    for name in ("articles", "results", "competitions", "players"):
        incoming = new.get(name) or []
        if not incoming:
            continue
        current = {item["id"]: item for item in load(name) if "id" in item}
        for item in incoming:
            if "id" not in item:
                continue
            if name in ("competitions", "players") and item["id"] in current:
                current[item["id"]].update(item)
            else:
                current[item["id"]] = item
        items = list(current.values())
        if name == "results":
            limit = (date.today() - timedelta(days=60)).isoformat()
            items = [r for r in items if r.get("status") == "soon" or (r.get("date") or "") >= limit]
            items.sort(key=lambda r: (r.get("date") or "", r.get("time") or ""), reverse=True)
        elif name == "articles":
            items.sort(key=lambda a: a.get("createdAt") or 0, reverse=True)
            items = items[:2000]
        elif name == "players":
            items.sort(key=lambda p: (p.get("sport") or "", p.get("name") or ""))
        else:
            items.sort(key=lambda c: (c.get("sport") or "", c.get("order") or 99))
        save(name, items)
        counts[name] = len(incoming)
    print("Fusionné :", counts or "rien")


if __name__ == "__main__":
    main()
