# data_fetcher.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch animal data from API Ninjas.

Public API:
    fetch_data(animal_name: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]

Returns a list of dicts shaped like:
{
  "name": str | None,
  "taxonomy": dict,
  "locations": list[str],
  "characteristics": dict,
}
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests  # pip install requests
from dotenv import load_dotenv  # pip install python-dotenv

# --- Load .env (once per process) ---
load_dotenv()

# --- Constants ---
API_URL = "https://api.api-ninjas.com/v1/animals"
TIMEOUT = 20  # seconds
# Prefer API_NINJAS_KEY; fall back to generic API_KEY
API_KEY = (os.getenv("API_NINJAS_KEY") or os.getenv("API_KEY") or "").strip()


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a single API item to the expected structure."""
    name = item.get("name")

    taxonomy = item.get("taxonomy")
    if not isinstance(taxonomy, dict):
        taxonomy = {}

    locations_raw = item.get("locations")
    if isinstance(locations_raw, list):
        locations = [str(x).strip() for x in locations_raw if str(x).strip()]
    elif isinstance(locations_raw, str) and locations_raw.strip():
        locations = [locations_raw.strip()]
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

    Args:
        animal_name: Search term (e.g., "Fox", "Monkey").
        api_key: Optional override for the API key (otherwise taken from .env).

    Returns:
        A list of normalized animal dictionaries. Empty list if no results.

    Raises:
        ValueError: if animal_name is empty.
        RuntimeError: if API key is missing.
        requests.HTTPError: if the HTTP request fails (non-2xx).
        requests.RequestException: for network-related errors.
    """
    if not isinstance(animal_name, str) or not animal_name.strip():
        raise ValueError("animal_name must be a non-empty string")

    key = (api_key or API_KEY).strip()
    if not key:
        raise RuntimeError("API key missing. Add API_NINJAS_KEY (or API_KEY) to your .env")

    headers = {"X-Api-Key": key}
    params = {"name": animal_name.strip()}

    resp = requests.get(API_URL, headers=headers, params=params, timeout=TIMEOUT)
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        return []

    return [_normalize_item(item) for item in data if isinstance(item, dict)]


if __name__ == "__main__":
    # Quick manual test
    try:
        animals = fetch_data("Fox")
        print(f"Fetched {len(animals)} animals")
        if animals:
            print(animals[0])
    except Exception as e:
        print("Error:", e)
