"""Run from the repository root: python -m core.demo"""

import json

from . import build_graph, find_route, load_sample_data, plan_dispatch, select_vehicle


def main():
    data = load_sample_data()
    graph = build_graph(data["locations"], data["roads"])
    incident = data["default_incident"]
    selected = select_vehicle(graph, data["vehicles"], incident)
    comparisons = {}
    if selected["status"] == "ok":
        start = selected["route"][0]
        comparisons = {
            name: find_route(graph, start, incident["location_id"], name)
            for name in ("BFS", "DFS", "UCS", "A*")
        }
    simultaneous = [
        {"id": "MED-1", "type": "medical", "location_id": "L12"},
        {"id": "MED-2", "type": "medical", "location_id": "L16"},
    ]
    print(json.dumps({"incident": incident, "dispatch": selected,
                      "algorithm_comparison": comparisons,
                      "simultaneous_incidents": simultaneous,
                      "dispatch_comparison": plan_dispatch(
                          graph, data["vehicles"], simultaneous
                      )}, indent=2))


if __name__ == "__main__":
    main()
