# India-Flight-Visualization-Dashboard

*COMPANY*: CODETECH IT SOLUTION

*NAME*: SOLANKI MEET

*INTERN ID*: CTIS9796

*DOMAIN*: PYTHON

*DURATION*: 6 WEEKS

*MENTOR*: NEELA SHANTOSH


Real-time aviation tracking and India flight visualization dashboard using FlightRadar24 API, Python, Pandas and Matplotlib.
This project finds aircraft details and answers aviation questions using a local JSON cache plus live online retrieval. Enter an aircraft such as `Airbus A380` to get its specifications, image, sources, and follow-up suggestions. You can also ask broader aviation questions such as `How do aircraft wings create lift?` or still compare aircraft when needed.

## Features

- Find aircraft details from simple names such as `Airbus A380`, `Concorde`, or `Boeing 787`.
- Ask aviation questions such as `How was the Airbus A380 developed and built?`
- Follow-up suggestions after each answer, including "how it was made" style prompts.
- Comparison support from natural-language questions such as `Compare A350 vs B787` or `Which is bigger A380 or 747?`
- Finder welcome message with suggested questions at startup.
- Numbered suggestions in terminal mode, for example enter `3` to run the third suggested question.
- Tkinter suggestion buttons for quick aircraft searches and comparisons.
- Retrieve and normalize aircraft specs:
  - Manufacturer
  - Aircraft category
  - Seating capacity
  - Maximum capacity
  - Range
  - Cruise speed
  - Maximum speed
  - Wingspan
  - Length
  - Height
  - Maximum takeoff weight
  - Engine type
  - First flight date
  - Status
  - Description
- Automatically generate aircraft detail tables.
- Identify comparison winners for range, capacity, speed, size, wingspan, length, height, and MTOW.
- Generate Matplotlib charts for comparison range, speed, capacity, and wingspan.
- Cache all successful lookups in `aircraft_cache.json`.
- Tkinter GUI for searching, comparing, viewing aircraft images, and viewing charts.

## Online Data Sources

The system uses the best available source for the query and gracefully skips sources that require keys or do not apply.

- Wikipedia API: broad aircraft descriptions, images, infobox values, and specification template parsing.
- AviationStack API: optional enrichment when `AVIATIONSTACK_API_KEY` is set.
- OpenSky Network API: optional live state enrichment when an ICAO24 hex address is supplied.
- FAA Aircraft Registry: optional registration/model enrichment when `ENABLE_FAA_REGISTRY=1`.
- ICAO Aircraft Type Designators: optional enrichment when `ICAO_API_KEY` is set.

Official references:

- https://www.mediawiki.org/wiki/API:Main_page
- https://api.wikimedia.org/wiki/API_reference
- https://aviationstack.com/documentation
- https://openskynetwork.github.io/opensky-api/rest.html
- https://registry.faa.gov/aircraftinquiry/
- https://www.icao.int/publications/DOC8643/Pages/default.aspx

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional spaCy language model:

```powershell
python -m spacy download en_core_web_sm
```

The finder still works without the model by using spaCy's blank English tokenizer plus rule-based aircraft extraction. On Windows, `requirements.txt` includes `msvc-runtime` because spaCy/Thinc wheels may need Microsoft C++ runtime DLLs.

## Optional API Keys

```powershell
$env:AVIATIONSTACK_API_KEY="your_key_here"
$env:ICAO_API_KEY="your_key_here"
$env:OPENSKY_CLIENT_ID="your_client_id"
$env:OPENSKY_CLIENT_SECRET="your_client_secret"
$env:ENABLE_FAA_REGISTRY="1"
```

You can force cache-only mode:

```powershell
$env:AIRCRAFT_COMPARE_OFFLINE="1"
```

## Command-Line Usage

```powershell
python chatbot.py "Airbus A380"
python chatbot.py "How was the Airbus A380 developed and built?"
python chatbot.py "How do aircraft wings create lift?"
python chatbot.py "Compare Airbus A320 and Boeing 737-800"
python chatbot.py "Compare A350 vs B787"
```

Interactive mode:

```powershell
python chatbot.py
```

Show the welcome screen and suggested questions:

```powershell
python chatbot.py help
```

Charts are written to the `charts` folder.

## GUI Usage

```powershell
python gui.py
```

The GUI lets you:

- Search aircraft by name.
- Ask aviation questions.
- Compare aircraft using natural language or comma-separated names.
- View aircraft images when the selected source provides one.
- View generated range, speed, capacity, and wingspan charts.

## Web App Usage

```powershell
python web_app.py
```

The app opens automatically in your default browser at `http://127.0.0.1:5000`.

The web app provides the smoothest finder experience:

- Suggested prompts at the start.
- Non-blocking browser UI while online lookups run.
- Aircraft detail pages with follow-up questions.
- Aviation Q&A answers with source links.
- Comparison tables, winner summaries, charts, aircraft images, sources, and data-quality notes.
- Double-checking for missing fields before values are shown as unavailable.

## Notes On Data Quality

Aircraft specifications vary by variant, engine option, payload, seating layout, certification basis, and source. For example, `B787` may mean the whole 787 family or a specific 787-8/787-9/787-10. The cache includes common aliases that resolve examples to specific variants, and unknown aircraft are looked up online through Wikipedia first.

For comparisons, the table can include up to 1000 aircraft. Charts default to the top 50 values per metric so the image remains readable.
