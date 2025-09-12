#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zootopia with API – Milestone 1
- Fetch animals from API Ninjas (search name='fox')
- Inject into template and write animals.html
"""

from __future__ import annotations

import html
import json
import os
import sys
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


# ---------- small utils ----------
def get_ci(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    """Case-insensitive getter for any of the provided keys."""
    for k in keys:
        if k in d:
            return d[k]
    lower_map = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = lower_map.get(k.lower())
        if v is not None:
            return v
    return None


def get_field(animal: Dict[str, Any], *keys: str) -> Optional[Any]:
    """Try top-level first, then 'characteristics'. Return None for empty strings."""
    v = get_ci(animal, *keys)
    if v is None:
        ch = get_ci(animal, "characteristics")
        if isinstance(ch, dict):
            v = get_ci(ch, *keys)
    if isinstance(v, str):
        v = v.strip()
        if v == "":
            return None
    return v


def format_value(value: Any) -> str:
    """Render lists as comma-separated text and escape HTML."""
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(x).strip() for x in value if str(x).strip())
    return html.escape(str(value))


# ---------- API ----------
def fetch_animals_from_api(name_query: str, api_key: str) -> List[Dict[str, Any]]:
    headers = {"X-Api-Key": api_key}
    params = {"name": name_query}
    resp = requests.get(API_URL, headers=headers, params=params, timeout=20)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        raise SystemExit(f"API error {resp.status_code}: {resp.text}") from e
    data = resp.json()
    if not isinstance(data, list):
        raise SystemExit("Unexpected API response format (expected a list).")
    return [x for x in data if isinstance(x, dict)]


# ---------- serialization ----------
def serialize_animal(animal: Dict[str, Any]) -> str:
    """
    <li class="cards__item">
      <div class="card__title">Name</div>
      <div class="card__text">
        <ul class="card__facts">
          <li class="card__fact"><span class="label">Diet:</span> ...</li>
          ...
        </ul>
      </div>
    </li>
    """
    name = get_field(animal, "name")
    title_html = (
        f'  <div class="card__title">{html.escape(str(name))}</div>\n' if name else ""
    )

    facts: List[tuple[str, Any]] = []

    # Core facts
    diet = get_field(animal, "diet")
    if diet:
        facts.append(("Diet", diet))

    locs = get_field(animal, "locations", "location")
    first_loc = None
    if isinstance(locs, list) and locs:
        first_loc = str(locs[0]).strip()
    elif isinstance(locs, str) and locs.strip():
        first_loc = locs.strip()
    if first_loc:
        facts.append(("Location", first_loc))

    typ = get_field(animal, "type")
    if typ:
        facts.append(("Type", typ))

    skin = get_field(animal, "skin_type", "skin type", "skintype")
    if skin:
        facts.append(("Skin type", skin))

    # Extras (optional)
    extras = [
        ("Lifespan", ("lifespan", "lifespan_in_wild", "lifespan_in_captivity")),
        ("Weight", ("weight", "avg_weight", "weight_range")),
        ("Length", ("length", "avg_length", "length_range")),
        ("Height", ("height", "avg_height", "height_range")),
        ("Top speed", ("top_speed", "speed", "max_speed")),
        ("Habitat", ("habitat",)),
        ("Temperament", ("temperament", "behavior")),
        ("Color(s)", ("color", "colors")),
        ("Scientific name", ("scientific_name", "latin_name")),
        ("Family", ("family",)),
        ("Order", ("order",)),
        ("Class", ("class", "class_name")),
        ("Geo range", ("geo_range", "native_region", "range")),
        ("Conservation status", ("conservation_status", "status")),
        ("Fun fact", ("fun_fact", "funfact")),
        ("Description", ("description",)),
    ]
    for label, keys in extras:
        v = get_field(animal, *keys)
        if v is not None:
            facts.append((label, v))

    if not (title_html or facts):
        return ""

    facts_html = "\n".join(
        f'        <li class="card__fact"><span class="label">{html.escape(label)}:</span> {format_value(val)}</li>'
        for label, val in facts
    )

    item = '  <li class="cards__item">\n'
    if title_html:
        item += title_html
    item += '  <div class="card__text">\n'
    item += '    <ul class="card__facts">\n'
    item += facts_html + "\n"
    item += "    </ul>\n"
    item += "  </div>\n"
    item += "  </li>\n"
    return item


def build_cards(animals: Iterable[Dict[str, Any]]) -> str:
    return "".join(serialize_animal(a) for a in animals if isinstance(a, dict))


# ---------- main ----------
def main() -> None:
    template_path = sys.argv[1] if len(sys.argv) > 1 else "animals_template.html"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "animals.html"

    # 1) Template laden
    template_html = read_text(template_path)

    # 2) API-Key laden (ENV bevorzugt, sonst Default aus Aufgabe)
    api_key = os.getenv(
        "API_NINJAS_KEY",
        "yCVFwvLElGXaZ24+Gu0q5Q==YjW5E3z1TR2NEafS",
    )
    if not api_key.strip():
        raise SystemExit("API key missing. Set env var API_NINJAS_KEY.")

    # 3) Daten von der API holen (Fox)
    animals = fetch_animals_from_api("fox", api_key)

    # 4) HTML bauen & schreiben
    cards_html = build_cards(animals)
    final_html = template_html.replace(PLACEHOLDER, cards_html)
    write_text(out_path, final_html)
    print(f"✅ Wrote {out_path} with {len(animals)} animals from API ‘fox’ search.")


if __name__ == "__main__":
    main()
