# AI project

## Smart City Emergency Response Coordinator

Working Python foundation for a college emergency response simulation.
Dispatch Atlas is the integrated Streamlit map and fleet-planning dashboard.

Included: a fictional city with 20 locations, 33 undirected roads, and seven
vehicles; explicit BFS, DFS, UCS, and A*; UCS vehicle selection; blocked-road
support; unreachable-case handling; and automated tests.

The core can also compare two plans for simultaneous incidents. Nearest-first
chooses a vehicle for each incident in order. Min-cost maximum flow plans all
assignments together, maximizing incidents served before minimizing distance.
Run the CLI demo to see two medical calls served in **2.5404 km** with the
optimized plan versus **5.7962 km** with nearest-first on the same sample city.

## Run on Windows

Open a terminal **inside this project folder**. Use Python 3.12.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m core.demo
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Using the interpreter directly avoids PowerShell activation-policy changes.
If the `py` launcher is unavailable, use `python -m venv .venv` after confirming
`python --version` is 3.12.

## Launch the dashboard

From the project folder with the virtual environment created above:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-ui.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit. Switch between nearest-first and
optimized assignment, add or resolve calls, change vehicle availability, and
close a route segment to recalculate dispatch. To enable the Varanasi option
on a fresh checkout, generate the snapshot below and reload the app.

## Varanasi road network

The optional Varanasi scenario uses real streets from a bounded central-city
extract around the old city. The incidents and vehicle locations are simulated.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-map.txt
.\.venv\Scripts\python.exe -m core.varanasi
```

This downloads a bounded OpenStreetMap extract, imports its driving streets
with OSMnx, and generates `data/varanasi.local.json`.
Keep that local snapshot for repeat demos. Routing after import needs no
network access. Online background tiles are separate. The sample scenario
remains available without an import. Varanasi routing respects one-way
segments represented in the extract, without modeling turn restrictions,
live traffic, or emergency vehicle exemptions.

Road data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).

## Files

| Path | Purpose |
| --- | --- |
| CONTRACT.md | Stable shared API and field definitions; read this first |
| data/sample_city.json | Locations, roads, vehicles, default incident |
| core/graph.py | Validated graph and safe heuristic metadata |
| core/routing.py | Four explicit search implementations |
| core/dispatch.py | Suitable available vehicle selection |
| core/demo.py | Runnable command-line demonstration |
| tests/test_core.py | Behaviour checks and NetworkX reference comparisons |
| ANTIGRAVITY_HANDOFF.md | Copy/paste instructions for Laptop 2 |

## Suggested demo

1. Run `python -m core.demo` for medical incident L14. AMB-03 is already at
   L14 but unavailable; another reachable ambulance must be chosen.
2. Compare all four algorithms from the selected vehicle to L14.
3. Block a road on the selected route in an in-memory copy, rebuild the graph,
   and run selection again. Never reuse the graph after editing roads.
4. Set incident location_id to L20 to demonstrate no_reachable_vehicle.
5. Set all ambulance availability values to false to demonstrate
   no_suitable_vehicle.

The functions do not write these changes back to JSON. The dashboard keeps edits in Streamlit session state and provides a reset option.

This is classical graph-search AI using synthetic data. It does not train a
machine-learning model, connect to emergency services, model traffic, or
estimate arrival times. Runtime values are local measurements, not benchmarks.

## Collaboration

Share the [GitHub repository](https://github.com/samarth07sinha-prog/smart-city-emergency-response-coordinator)
and the [team handoff](TEAM_HANDOFF.md) with everyone. Each laptop clones the
same repository, works on its assigned branch, and opens a pull request into
`main`. Laptop 2 uses [the Antigravity prompt](ANTIGRAVITY_HANDOFF.md).
