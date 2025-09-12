#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zootopia with API – Milestone 2
- Fragt den Tiernamen ab (input)
- Holt die Daten von API Ninjas (name=<eingabe>)
- Erzeugt animals.html aus dem Template
"""

from __future__ import annotations
import html, json, os, sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import requests  # pip install requests

PLACEHOLDER = "__REPLACE_ANIMALS_INFO__"
API_URL = "https://api.api-ninjas.com/v1/animals"

# ---------- IO ----------
def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")

def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")

# ---------- utils ----------
def get_ci(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    for k in keys:
        if k in d: return d[k]
    lm = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = lm.get(k.lower())
        if v is not None: return v
    return None

def get_field(animal: Dict[str, Any], *keys: str) -> Optional[Any]:
    v = get_ci(animal, *keys)
    if v is None:
        ch = get_ci(animal, "characteristics")
        if isinstance(ch, dict):
            v = get_ci(ch, *keys)
    if isinstance(v, str):
        v = v.strip()
        if not v: return None
    return v

def format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(x).strip() for x in value if str(x).strip())
    return html.escape(str(value))

# ---------- API ----------
def fetch_animals_from_api(name_query: str, api_key: str) -> List[Dict[str, Any]]:
    headers = {"X-Api-Key": api_key}
    resp = requests.get(API_URL, headers=headers, params={"name": name_query}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError("Unexpected API response (expected a list).")
    return [x for x in data if isinstance(x, dict)]

# ---------- serialization ----------
def serialize_animal(animal: Dict[str, Any]) -> str:
    name = get_field(animal, "name")
    title_html = f'  <div class="card__title">{html.escape(str(name))}</div>\n' if name else ""

    facts: List[tuple[str, Any]] = []
    for label, keys in [
        ("Diet", ("diet",)),
        ("Location", ("locations", "location")),
        ("Type", ("type",)),
        ("Skin type", ("skin_type", "skin type", "skintype")),
        ("Scientific name", ("scientific_name", "latin_name")),
        ("Family", ("family",)),
        ("Order", ("order",)),
        ("Class", ("class", "class_name")),
        ("Habitat", ("habitat",)),
        ("Geo range", ("geo_range", "native_region", "range")),
        ("Conservation status", ("conservation_status", "status")),
        ("Description", ("description",)),
    ]:
        val = get_field(animal, *keys)
        if label == "Location":
            if isinstance(val, list) and val:
                val = val[0]
        if val is not None:
            facts.append((label, val))

    if not (title_html or facts): return ""

    facts_html = "\n".join(
        f'        <li class="card__fact"><span class="label">{html.escape(label)}:</span> {format_value(val)}</li>'
        for label, val in facts
    )

    item = '  <li class="cards__item">\n'
    if title_html: item += title_html
    item += '  <div class="card__text">\n'
    item += '    <ul class="card__facts">\n' + facts_html + "\n"
    item += "    </ul>\n  </div>\n  </li>\n"
    return item

def build_cards(animals: Iterable[Dict[str, Any]]) -> str:
    return "".join(serialize_animal(a) for a in animals if isinstance(a, dict))

# ---------- main ----------
def main() -> None:
    template_path = sys.argv[1] if len(sys.argv) > 1 else "animals_template.html"
    out_path      = sys.argv[2] if len(sys.argv) > 2 else "animals.html"

    # 1) Nutzer-Eingabe (nicht leer)
    query = ""
    while not query:
        query = input("Enter a name of an animal: ").strip()

    # 2) Template laden
    template_html = read_text(template_path)

    # 3) API-Key (ENV bevorzugt, sonst bereitgestellter Key)
    api_key = os.getenv("API_NINJAS_KEY", "yCVFwvLElGXaZ24+Gu0q5Q==YjW5E3z1TR2NEafS").strip()
    if not api_key:
        print("Missing API key. Set API_NINJAS_KEY."); sys.exit(1)

    # 4) Daten holen & Seite erzeugen
    try:
        animals = fetch_animals_from_api(query, api_key)
    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} {e.response.text}"); sys.exit(1)
    except Exception as e:
        print(f"Error fetching data: {e}"); sys.exit(1)

    cards_html = build_cards(animals)
    final_html = template_html.replace(PLACEHOLDER, cards_html if cards_html else "<p>No results.</p>")
    write_text(out_path, final_html)

    print("Website was successfully generated to the file animals.html.")

if __name__ == "__main__":
    main()
