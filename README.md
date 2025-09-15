# Zootopia (with API)

Eine kleine Python-App, die aus Live-Daten der **API Ninjas – Animals API** eine Website mit Tierkarten generiert.  
Die Nutzer:innen geben einen Tiernamen ein (z. B. `Fox`, `Monkey`) und das Script erzeugt eine HTML-Seite mit Ergebnissen.  
Fehler- und Leerzustände (keine Treffer) werden freundlich angezeigt.

---

## Inhaltsverzeichnis
- [Features](#features)
- [Technik & Architektur](#technik--architektur)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Konfiguration (.env)](#konfiguration-env)
- [Projektstruktur](#projektstruktur)
- [Benutzung](#benutzung)
- [Template-Hinweis](#template-hinweis)
- [Styling](#styling)
- [Troubleshooting](#troubleshooting)
- [Quality Guidelines](#quality-guidelines)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [Lizenz](#lizenz)

---

## Features
- Live-Datenabruf über **API Ninjas** (`/v1/animals?name=<query>`).
- Klare Trennung:
  - `data_fetcher.py` – API-Client (Requests + Dotenv)
  - `animals_web_generator.py` – erzeugt HTML aus den Daten
- Kartenlayout für Tierinfos (Name, Diet, Location, Type, u. a.).
- **Empty State**: Bei 0 Treffern wird eine freundliche Meldung ins Template gerendert.
- Robust gegen fehlende Felder (defensive Serialisierung).

---

## Technik & Architektur
- **Python**: 3.9+ (läuft meist auch ab 3.8)
- **Abhängigkeiten**:  
  - `requests` (HTTP)  
  - `python-dotenv` (lädt `.env`)
- **Datenquelle**: API Ninjas Animals API (API-Key erforderlich)
- **Trennung von Concerns**:
  - Der Generator **importiert** den Fetcher und kümmert sich nur um Darstellung.
  - Der Fetcher kapselt Auth, Endpunkt, Normalisierung.

---

## Voraussetzungen
- Python 3.9 oder neuer
- Internetzugang
- API-Key von **API Ninjas – Animals API**

---

## Installation
```bash
# 1) Repository klonen oder Projektordner öffnen
# 2) Abhängigkeiten installieren
python3 -m pip install -r requirements.txt


   ```
4. `data_fetcher.py` lädt die Variablen automatisch über **python-dotenv**.

## Konfiguration (.env)

1. Erstelle im Projektroot eine Datei **`.env`**.
2. Trage deinen API-Key ein:
   ```dotenv
   # .env
   API_NINJAS_KEY=DEIN_API_KEY_HIER
   # optionaler Alias:
   # API_KEY=DEIN_API_KEY_HIER
   ```
3. **Nicht committen** – füge `.env` in die `.gitignore` ein:
   ```gitignore
   # secrets
   .env
   ```
4. `data_fetcher.py` lädt die Variablen automatisch über **python-dotenv**.

## Projektstruktur
.
├─ animals_web_generator.py   # CLI: fragt nach Tiernamen, rendert HTML
├─ data_fetcher.py            # API-Client (requests + dotenv)
├─ animals_template.html      # Template mit Platzhalter __REPLACE_ANIMALS_INFO__
├─ style.css                  # Karten- & Empty-State-Styling
├─ requirements.txt
└─ README.md

## Benutzung

python3 animals_web_generator.py
- Please enter an animal: Fox
- Website was successfully generated to the file animals.html.

## Template-Hinweis

Dein animals_template.html muss den Platzhalter enthalten, damit die Karten injiziert werden können:

<ul class="cards">
  __REPLACE_ANIMALS_INFO__
</ul>


Bei 0 Treffern (z. B. Fantasiebegriff) rendert der Generator einen Empty-State:

<section class="empty">
  <h2>The animal "goadohjasgfas" doesn't exist.</h2>
  <p>Try a different name (e.g., "Fox", "Bear", "Eagle").</p>
  <!-- optionaler Hinweis -->
  <p class="empty__hint">…</p>
</section>

## Styling

Das Styling liegt in style.css (Cards & Empty-State).
Passe Farben/Abstände dort an, das HTML bleibt unverändert (semantische Klassen wie .cards__item, .card__title, .card__facts usw.).

## Troubleshooting

401 – Invalid API key

```401
Prüfe .env (richtiger Key? keine Anführungszeichen/Zeilenumbrüche).

Ist die Variable korrekt benannt? API_NINJAS_KEY (oder API_KEY als Fallback).

Teste schnell im REPL:

from data_fetcher import fetch_data
print(len(fetch_data("Fox", api_key="DEIN_KEY")))
```
```keine_ergenisse
0 Ergebnisse

Benutze einen allgemeineren Suchbegriff (Fox statt Arctic Fox).

API gerade down? Versuche später erneut.
```
```429
429 – Rate limit

 Warte kurz und versuche erneut.

Optional: Backoff/Retry im data_fetcher.py ergänzen.

.env wird nicht geladen

Liegt .env wirklich im Projektroot (wo du das Script startest)?

python-dotenv installiert?

Alternativ Key als Env setzen:

export API_NINJAS_KEY='DEIN_KEY'
python3 animals_web_generator.py
```
## Quality Guidlines

- Keine Secrets im Code: .env verwenden, .gitignore enthält .env.
- Saubere Imports: requests nur im Fetcher, nicht im Generator.
- Konstanten im data_fetcher.py: API_URL, TIMEOUT, (indirekt) API_KEY via .env.
- Fehlertoleranz: Beim Rendern nur vorhandene Felder ausgeben; leere Strings vermeiden.
- PEP 8: Einrückungen, Zeilenlängen, Funktionen mit klaren Namen.

## Contributing

Pull Requests willkommen!
1. Forken & Branch erstellen: git checkout -b feat/dein-feature
2. Änderungen committen, Tests/Manu-Checks durchführen.
3. PR mit Beschreibung eröffnen.

## Lizenz

MIT — nutze frei und passe nach Bedarf an.