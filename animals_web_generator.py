#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate animals.html by injecting serialized animal cards into a template.

New:
- Show available skin_type values from the JSON.
- Ask the user to choose a skin_type (by number or name).
- Render the website only for animals matching the chosen skin_type.
- Animals without skin_type are grouped under "Unknown".
"""

from __future__ import annotations

import html
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PLACEHOLDER = "__REPLACE_ANIMALS_INFO__"
UNKNOWN_SKIN = "Unknown"  # label for animals missing skin_type


# ---------- IO helpers ----------
def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


# ---------- data helpers ----------
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
    """
    Try top-level first, then 'characteristics'. Return None for empty strings.
    """
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


def iter_animals(data: Any) -> List[Dict[str, Any]]:
    """Accepts a list of animals or a dict containing key 'animals'."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("animals"), list):
        return [x for x in data["animals"] if isinstance(x, dict)]
    return []


# ---------- skin_type utilities ----------
def animal_skin_type(animal: Dict[str, Any]) -> str:
    """Return normalized skin_type or UNKNOWN_SKIN if missing."""
    v = get_field(animal, "skin_type", "skin type", "skintype")
    if v is None:
        return UNKNOWN_SKIN
    return str(v).strip()


def collect_skin_types(animals: Iterable[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """
    Return a list of (skin_type, count) sorted alphabetically (case-insensitive).
    Includes UNKNOWN_SKIN if any animal lacks skin_type.
    """
    counter: Counter[str] = Counter()
    for a in animals:
        counter[animal_skin_type(a)] += 1
    # sort case-insensitively, but keep Unknown at the end for better UX
    items = sorted(
        ((k, n) for k, n in counter.items() if k != UNKNOWN_SKIN),
        key=lambda x: x[0].lower(),
    )
    if counter.get(UNKNOWN_SKIN):
        items.append((UNKNOWN_SKIN, counter[UNKNOWN_SKIN]))
    return items


def prompt_skin_choice(skin_counts: List[Tuple[str, int]]) -> str:
    """Prompt user to choose a skin_type by number or name."""
    print("\nAvailable skin_type values:\n")
    for i, (skin, cnt) in enumerate(skin_counts, start=1):
        print(f"  {i}. {skin} ({cnt})")
    print()

    # Map for quick lookup (case-insensitive)
    name_map = {skin.lower(): skin for skin, _ in skin_counts}

    choice = input("Choose a skin_type (name or number): ").strip()

    # number?
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(skin_counts):
            return skin_counts[idx - 1][0]

    # name?
    if choice.lower() in name_map:
        return name_map[choice.lower()]

    print("Invalid choice. Defaulting to showing all animals.")
    return "ALL"


def filter_by_skin(animals: List[Dict[str, Any]], chosen: str) -> List[Dict[str, Any]]:
    """Filter animals by chosen skin_type. 'ALL' shows all animals."""
    if chosen == "ALL":
        return animals
    if chosen == UNKNOWN_SKIN:
        return [a for a in animals if animal_skin_type(a) == UNKNOWN_SKIN]
    return [a for a in animals if animal_skin_type(a).lower() == chosen.lower()]


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
        f'  <div class="card__title">{html.escape(str(name))}</div>\n'
        if name
        else ""
    )

    # Facts list (core first, then extras)
    facts: List[Tuple[str, Any]] = []

    # Core
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

    skin = animal_skin_type(animal)
    if skin != UNKNOWN_SKIN:
        facts.append(("Skin type", skin))
    else:
        # Optional: zeige Unknown explizit
        facts.append(("Skin type", UNKNOWN_SKIN))

    # Extras
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
    json_path = sys.argv[1] if len(sys.argv) > 1 else "animals_data.json"
    template_path = sys.argv[2] if len(sys.argv) > 2 else "animals_template.html"
    out_path = sys.argv[3] if len(sys.argv) > 3 else "animals.html"

    # Read inputs
    try:
        template_html = read_text(template_path)
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Read error: {e}")
        sys.exit(1)

    animals = iter_animals(data)

    # Show available skin types and ask user
    skin_counts = collect_skin_types(animals)
    chosen_skin = prompt_skin_choice(skin_counts)

    # Filter animals
    filtered = filter_by_skin(animals, chosen_skin)
    if not filtered:
        print(f"No animals found for skin_type '{chosen_skin}'. Exiting.")
        sys.exit(0)

    # Build and write HTML
    cards_html = build_cards(filtered)
    final_html = template_html.replace(PLACEHOLDER, cards_html)

    try:
        write_text(out_path, final_html)
    except Exception as e:
        print(f"❌ Write error: {e}")
        sys.exit(1)

    print(f"✅ Wrote {out_path} with {len(filtered)} animals (skin_type = {chosen_skin}).")


if __name__ == "__main__":
    main()
