# Shared interface — version 1.0

Project: **AI project — Smart City Emergency Response Coordinator**.
This document is the agreement between the core and UI builders. Changes must
be agreed before either builder changes signatures, field names, or statuses.

## Setup and imports

Use Python 3.12. Run from the repository root after installing requirements.txt.

```python
from core import load_sample_data, build_graph, find_route, select_vehicle

data = load_sample_data()
graph = build_graph(data["locations"], data["roads"])
incident = data["default_incident"]
selection = select_vehicle(graph, data["vehicles"], incident)
if selection["status"] == "ok":
    comparison = find_route(graph, selection["route"][0], incident["location_id"], "A*")
```

## Input data

`load_sample_data() -> dict` loads a fresh copy of data/sample_city.json.
The dictionary contains schema_version, name, description, locations, roads,
vehicles, and default_incident. The demo coordinates and roads are fictional.
L20 (Island Outpost) is deliberately disconnected; L01–L19 are connected.

| Record | Required fields | Rules |
| --- | --- | --- |
| Location | id, name, lat, lon | Nonempty strings; finite latitude [-90,90] and longitude [-180,180] |
| Road | id, source, target, distance_km, blocked | Unique id and undirected endpoint pair; known distinct locations; positive finite distance; real boolean blocked |
| Vehicle | id, type, location_id, available | Unique nonempty id; type ambulance/fire_engine/police; known location; real boolean available |
| Incident | type, location_id | Type medical/fire/police; known location |

All ids are strings. All distances are kilometres. The data uses an undirected
simple graph: every open road can be traversed in both directions. No parallel
roads or self loops. Inputs are JSON-compatible dictionaries and lists.

Incident mapping: medical -> ambulance; fire -> fire_engine; police -> police.

## Graph

`build_graph(locations: list[dict], roads: list[dict]) -> networkx.Graph`

Creates a new graph without modifying its inputs. Node attributes: name, lat,
lon. Edge attributes: id, distance_km. Blocked roads are omitted, but isolated
locations remain. Keep the original road records separately to draw blocked
roads on the map. Rebuild the graph whenever blocking or distance changes.
Do not modify the resulting graph manually: its A* heuristic metadata depends
on the input distances. Invalid record values raise ValueError.

## Route search

`find_route(graph, start: str, goal: str, algorithm: str = "UCS") -> dict`

Algorithms: BFS, DFS, UCS, A*. Case is normalised. Unknown algorithms and unknown
location ids raise ValueError. The graph must come from build_graph.

Successful result example (illustrative values, not a benchmark):

```json
{"status":"ok","path":["L01","L02"],"distance_km":1.2,"nodes_expanded":2,"runtime_ms":0.1}
```

Unreachable result: status="no_path", path=[], distance_km=null.
The nodes_expanded and runtime_ms fields are still populated.
If start equals goal: status="ok", path=[start], distance_km=0.0,
nodes_expanded=1.

- nodes_expanded counts unique frontier removals processed, including the goal;
  stale priority-queue entries are excluded.
- runtime_ms measures one search with perf_counter, including reconstruction.
  Display it as an observed run; small timings are noisy and are not evidence
  that one algorithm is always faster.
- Paths contain node ids, including both endpoints. Distance is the sum of edge
  distances, with no rounding inside the calculation.
- Sorted neighbor iteration makes paths repeatable; tied priority-queue entries
  use insertion order. Different optimal paths can have identical distance.
- BFS minimises number of edges, not weighted distance. DFS finds a path but
  does not promise the shortest path. UCS and A* minimise weighted distance.
- A* uses great-circle distance scaled by the smallest open-road distance /
  great-circle-distance ratio, capped at 1 and slightly reduced for floating
  point safety. This remains a lower bound even for custom short road weights.

## Vehicle selection

`select_vehicle(graph, vehicles: list[dict], incident: dict) -> dict`

Filters by incident type and availability, runs one multi-source UCS to the
incident, and selects the lowest reachable distance. Equal distances choose
the lexicographically smaller vehicle id.

Successful example (illustrative):

```json
{"status":"ok","vehicle_id":"AMB-01","route":["L01","L02"],"distance_km":1.2}
```

Notice that selection uses **route**, while find_route uses **path**.

Failure statuses:

- no_suitable_vehicle: no available vehicle has the required type.
- no_reachable_vehicle: suitable available vehicles exist, but none can reach
  the incident.

Both failures return vehicle_id=null, route=[], distance_km=null.
Invalid incident/vehicle record values raise ValueError.
Selection is a preview: it does not mutate data, reserve a vehicle, move it, or
change availability. The UI should label its button **Find response vehicle**.

## Simultaneous dispatch planning

`plan_dispatch(graph, vehicles, incidents)` is an optional addition to the v1
API. Each incident uses the same `type` and `location_id` fields, plus a unique,
nonempty string `id`. Invalid record values raise ValueError. The planner
uses one multi-target UCS per distinct available origin and required vehicle type.
It stops when all requested destinations settle or the frontier empties.

The result has `greedy` and `optimized` plans. Greedy serves incidents in input
order, choosing the nearest remaining vehicle (ties by vehicle ID).
Optimized uses min-cost maximum flow to assign as many incidents as possible
and, among those plans, minimize total route distance. Each vehicle and
incident can be assigned at most once. Equally optimal plans may differ.

Both plans have `served_count`, `total_distance_km`, `unassigned_incident_ids`,
and `assignments`. Each assignment has `incident_id`, `vehicle_id`, `route`,
and `distance_km`. Assignments and unassigned IDs follow incident input order.
An empty plan has zero distance. This is a preview that leaves all inputs
unchanged. Severity, travel times, and multi-stop dispatch are outside scope.
When served counts differ, do not present total distance alone as a saving.

## Varanasi road network

`load_varanasi_data()` prefers a local snapshot produced by
`python -m core.varanasi` and falls back to the bundled road archive.
The snapshot contains the standard locations, roads, vehicles, and default
incident, plus `directed`, `map_center` (latitude and longitude),
`showcase_incidents`, and attribution text and URL.

Call `build_graph(locations, roads, directed=data.get("directed", False))`
on every closure change. Directed road records run from source to target.
Routes list every junction along the original street segments. Draw in that
order. Parallel directed roads use the shortest open edge, breaking ties by
ID. The chosen segment ID is available as `graph[source][target]["id"]`.
A closure applies only to selected segment IDs, so a two-way closure must
include both directions when present.

## UI agreement

Dispatch always uses UCS. Compare algorithms separately using the selected
vehicle's current location and the same incident and graph. A comparison must
not change the selected vehicle. Recalculate after input changes or clear stale
results. Show distances; no ETA or live-traffic claims in this foundation.

Laptop 1 owns core/, data/, tests/, CONTRACT.md, requirements.txt, README.md,
and integration. Laptop 2 owns app.py and ui/. Laptop 2 can add a separate
requirements-ui.txt referencing `-r requirements.txt` and its UI dependencies.
Do not send .git or .venv when copying between laptops.
