#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zootopia with API — Website Generator
- Fragt den Tiernamen ab
- Holt die Daten via data_fetcher.fetch_data()
- Rendert Cards oder eine leere-State-Meldung
"""

from __future__ import annotations
import html, sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import data_fetcher  # <— Wichtig: nutzt dein neues Modul

PLACEHOLDER = "__REPLACE_ANIMALS_INFO__"


# ---------- IO ----------
def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")

def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


# ---------- helpers ----------
def get_ci(d: Dict[str, Any], *keys: str) -> Optional[Any]:
    for k in keys:
        if k in d:
            return d[k]
    lm = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = lm.get(k.lower())
        if v is not None:
            return v
    return None

def get_field(animal: Dict[str, Any], *keys: str) -> Optional[Any]:
    v = get_ci(animal, *keys)
    if v is None:
        ch = get_ci(animal, "characteristics")
        if isinstance(ch, dict):
            v = get_ci(ch, *keys)
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return None
    return v

def format_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(x).strip() for x in value if str(x).strip())
    return html.escape(str(value))


# ---------- rendering ----------
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
        if label == "Location" and isinstance(val, list) and val:
            val = val[0]
        if val is not None:
            facts.append((label, val))

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
    item += '    <ul class="card__facts">\n' + facts_html + "\n"
    item += "    </ul>\n  </div>\n  </li>\n"
    return item

def build_cards(animals: Iterable[Dict[str, Any]]) -> str:
    return "".join(serialize_animal(a) for a in animals if isinstance(a, dict))

def render_empty(query: str, details: str | None = None) -> str:
    q = html.escape(query)
    det = f'<p class="empty__hint">{html.escape(details)}</p>' if details else ""
    return (
        f'<section class="empty">'
        f'<h2>The animal "{q}" doesn\'t exist.</h2>'
        f'<p>Try a different name (e.g., "Fox", "Bear", "Eagle").</p>'
        f"{det}</section>"
    )


# ---------- main ----------
def main() -> None:
    template_path = sys.argv[1] if len(sys.argv) > 1 else "animals_template.html"
    out_path      = sys.argv[2] if len(sys.argv) > 2 else "animals.html"

    animal_name = ""
    while not animal_name:
        animal_name = input("Please enter an animal: ").strip()

    template_html = read_text(template_path)

    try:
        data = data_fetcher.fetch_data(animal_name)
    except Exception as e:
        html_out = template_html.replace(PLACEHOLDER, render_empty(animal_name, f"Error: {e}"))
        write_text(out_path, html_out)
        print("Website was generated with an error message.")
        return

    html_block = build_cards(data) if data else render_empty(animal_name)
    write_text(out_path, template_html.replace(PLACEHOLDER, html_block))
    print("Website was successfully generated to the file animals.html.")

if __name__ == "__main__":
    main()
