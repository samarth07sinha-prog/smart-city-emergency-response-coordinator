# Laptop 2 — Antigravity handoff

The emergency response dashboard, routing algorithms, and Varanasi street map
are already implemented. Your task is to **review and polish the existing
interface**. Work from the latest version of the shared repository:

https://github.com/samarth07sinha-prog/smart-city-emergency-response-coordinator

Create a UI branch from `main` and open a pull request when finished. Read
`README.md`, `CONTRACT.md`, and `data/ATTRIBUTION.md` before editing.

## Run the app

Use Python 3.12 from the repository root on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The bundled Varanasi road network loads without downloading
another map extract. The fictional sample city is available from the road
network selector.

## Your assignment

1. Check that routes, markers, incident labels, and the map legend remain
   readable while panning and zooming.
2. Confirm a map click selects a road junction for a new incident. Check
   that adding and resolving a call updates both the queue and the map.
3. Compare **Optimized** and **Nearest-first** plans. Change a vehicle's
   availability under **Fleet & settings**, close a route segment, and verify
   the displayed routes and totals update. Use **Reset scenario** to restore
   the preset.
4. Review the layout at a desktop width and a phone width. Improve spacing,
   typography, controls, legend placement, and route contrast where the
   actual interface needs it. Check keyboard focus and readable labels.
5. Verify that the bundled road data and street map load on a clean clone.

The interface lives in `app.py`, `ui/maps.py`, `ui/theme.py`, and
`.streamlit/config.toml`. Adjust these files for presentation and UI
behavior. Report a core routing or dispatch issue with exact reproduction
steps to Laptop 1. Keep map-data attribution visible. The vehicles and calls are simulated.

Finish with a short report listing files changed, screen sizes checked,
interactions tested, commands run, and any remaining issues. If the
interface already meets a check, report the result without rewriting it.
