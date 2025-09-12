# data_fetcher.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetches animal data from API Ninjas.

Usage:
    from data_fetcher import fetch_data
    animals = fetch_data("Fox")
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests  # pip install requests

API_URL = "https://api.api-ninjas.com/v1/animals"


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure the returned dict has the expected keys/types."""
    name = item.get("name")

    taxonomy = item.get("taxonomy")
    if not isinstance(taxonomy, dict):
        taxonomy = {}

    # locations can be a list or sometimes a single string
    locations = item.get("locations")
    if isinstance(locations, list):
        pass
    elif isinstance(locations, str) and locations.strip():
        locations = [locations.strip()]
    else:
        locations = []

    characteristics = item.get("characteristics")
    if not isinstance(characteristics, dict):
        characteristics = {}

    return {
        "name": name,
        "taxonomy": taxonomy,
        "locations": locations,
        "characteristics": characteristics,
    }


def fetch_data(animal_name: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches the animals data for the animal 'animal_name'.

    Returns: a list of animals, each animal is a dictionary:
    {
      'name': ...,
      'taxonomy': { ... },
      'locations': [ ... ],
      'characteristics': { ... }
    }
    """
    if not isinstance(animal_name, str) or not animal_name.strip():
        raise ValueError("animal_name must be a non-empty string")

    key = (api_key or os.getenv("API_NINJAS_KEY",
                                "yCVFwvLElGXaZ24+Gu0q5Q==YjW5E3z1TR2NEafS")).strip()
    if not key:
        raise RuntimeError("API key missing. Set API_NINJAS_KEY or pass api_key.")

    headers = {"X-Api-Key": key}
    params = {"name": animal_name.strip()}

    resp = requests.get(API_URL, headers=headers, params=params, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        return []

    # normalize each item to the expected shape
    out: List[Dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            out.append(_normalize_item(item))
    return out


if __name__ == "__main__":
    # quick manual test
    try:
        animals = fetch_data("Fox")
        print(f"Fetched {len(animals)} animals.")
        if animals:
            print(animals[0].keys())
    except Exception as e:
        print("Error:", e)
