# AI project

## Smart City Emergency Response Coordinator

Working Python foundation for a college emergency response simulation.
The interface and map are the next task for Antigravity. No UI is included yet.

Included: a fictional city with 20 locations, 33 undirected roads, and seven
vehicles; explicit BFS, DFS, UCS, and A*; UCS vehicle selection; blocked-road
support; unreachable-case handling; and automated tests.

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

The functions do not write these changes back to JSON. The future UI will keep
edits in Streamlit session state and provide a reset option.

This is classical graph-search AI using synthetic data. It does not train a
machine-learning model, connect to emergency services, model traffic, or
estimate arrival times. Runtime values are local measurements, not benchmarks.

## Collaboration

Give Laptop 2 the entire source folder (or source ZIP), especially CONTRACT.md
and ANTIGRAVITY_HANDOFF.md. Use separate Git branches if sharing one remote.
Laptop 2 edits app.py, ui/, and requirements-ui.txt. Laptop 1 owns core and tests.
No remote repository has been configured by this setup.
