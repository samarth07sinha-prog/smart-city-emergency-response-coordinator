"""Compare simultaneous dispatch plans on the same road network."""

from math import fsum

import networkx as nx

from .dispatch import _available_vehicles, _incident_target
from .graph import _identifier
from .routing import find_route


def plan_dispatch(graph: nx.Graph, vehicles: list[dict], incidents: list[dict]) -> dict:
    """Return greedy and optimized previews without changing vehicles or roads."""
    available = _available_vehicles(graph, vehicles)
    targets = {}
    for incident in incidents:
        incident_id = _identifier(incident.get("id"), "Incident id")
        if incident_id in targets:
            raise ValueError(f"Duplicate incident: {incident_id}")
        targets[incident_id] = _incident_target(graph, incident)

    options = {incident_id: {} for incident_id in targets}
    route_cache = {}
    for incident_id, (vehicle_type, goal) in targets.items():
        for vehicle in available:
            if vehicle["type"] != vehicle_type:
                continue
            pair = (vehicle["location_id"], goal)
            if pair not in route_cache:
                route_cache[pair] = find_route(graph, *pair, "UCS")
            route = route_cache[pair]
            if route["status"] == "ok":
                options[incident_id][vehicle["id"]] = route

    greedy, used = {}, set()
    for incident_id, routes in options.items():
        candidates = routes.keys() - used
        if candidates:
            chosen = min(candidates, key=lambda v: (routes[v]["distance_km"], v))
            greedy[incident_id] = chosen
            used.add(chosen)

    return {
        "greedy": _summarize(options, greedy),
        "optimized": _summarize(options, _optimal_assignment(options)),
    }


def _optimal_assignment(options):
    source, sink = ("source",), ("sink",)
    network = nx.DiGraph()
    network.add_nodes_from([source, sink])
    costs = {}
    for incident_id, routes in options.items():
        incident = ("incident", incident_id)
        network.add_edge(incident, sink, capacity=1, weight=0)
        for vehicle_id, route in routes.items():
            vehicle = ("vehicle", vehicle_id)
            network.add_edge(source, vehicle, capacity=1, weight=0)
            costs[vehicle, incident] = route["distance_km"].as_integer_ratio()
    if not costs:
        return {}

    # Float denominators are powers of two. A common denominator gives the flow
    # solver integer edge weights while preserving the computed UCS distances.
    scale = max(denominator for _, denominator in costs.values())
    for (vehicle, incident), (numerator, denominator) in costs.items():
        network.add_edge(vehicle, incident, capacity=1,
                         weight=numerator * (scale // denominator))
    flow = nx.max_flow_min_cost(network, source, sink)
    return {
        incident[1]: vehicle[1]
        for vehicle, incident in costs
        if flow[vehicle][incident]
    }


def _summarize(options, assignment):
    assignments = []
    unassigned = []
    for incident_id, routes in options.items():
        if incident_id not in assignment:
            unassigned.append(incident_id)
            continue
        vehicle_id = assignment[incident_id]
        route = routes[vehicle_id]
        assignments.append({
            "incident_id": incident_id,
            "vehicle_id": vehicle_id,
            "route": list(route["path"]),
            "distance_km": route["distance_km"],
        })
    return {
        "assignments": assignments,
        "unassigned_incident_ids": unassigned,
        "served_count": len(assignments),
        "total_distance_km": fsum(item["distance_km"] for item in assignments),
    }
