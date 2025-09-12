#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import html, os, sys
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
        return []
    return [x for x in data if isinstance(x, dict)]

# ---------- renderers ----------
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
    item += '  <div class="card__text">\n    <ul class="card__facts">\n'
    item += facts_html + "\n    </ul>\n  </div>\n  </li>\n"
    return item

def build_cards(animals: Iterable[Dict[str, Any]]) -> str:
    return "".join(serialize_animal(a) for a in animals if isinstance(a, dict))

def render_empty(query: str, details: str | None = None) -> str:
    q = html.escape(query)
    det = f"<p class=\"empty__hint\">{html.escape(details)}</p>" if details else ""
    return (
        f'<section class="empty">'
        f'<h2>The animal "{q}" doesn\'t exist.</h2>'
        f'<p>Try a different name (e.g., "Fox", "Bear", "Eagle").</p>'
        f'{det}'
        f"</section>"
    )

# ---------- main ----------
def main() -> None:
    template_path = sys.argv[1] if len(sys.argv) > 1 else "animals_template.html"
    out_path      = sys.argv[2] if len(sys.argv) > 2 else "animals.html"

    query = ""
    while not query:
        query = input("Enter a name of an animal: ").strip()

    template_html = read_text(template_path)

    api_key = os.getenv("API_NINJAS_KEY", "yCVFwvLElGXaZ24+Gu0q5Q==YjW5E3z1TR2NEafS").strip()
    if not api_key:
        write_text(out_path, template_html.replace(PLACEHOLDER, render_empty(query, "Missing API key.")))
        print("Website was generated with an error message (missing API key)."); return

    try:
        animals = fetch_animals_from_api(query, api_key)
    except requests.HTTPError as e:
        msg = f"API error: {e.response.status_code}"
        try:
            msg += f" • {e.response.json()}"
        except Exception:
            msg += f" • {e.response.text[:200]}"
        html_content = template_html.replace(PLACEHOLDER, render_empty(query, msg))
        write_text(out_path, html_content)
        print("Website was generated with an API error message."); return
    except Exception as e:
        html_content = template_html.replace(PLACEHOLDER, render_empty(query, f"Unexpected error: {e}"))
        write_text(out_path, html_content)
        print("Website was generated with an error message."); return

    # Ergebnis schreiben – leerer Treffer => hübsche Nachricht
    if not animals:
        html_content = template_html.replace(PLACEHOLDER, render_empty(query))
    else:
        html_content = template_html.replace(PLACEHOLDER, build_cards(animals))

    write_text(out_path, html_content)
    print("Website was successfully generated to the file animals.html.")

if __name__ == "__main__":
    main()
