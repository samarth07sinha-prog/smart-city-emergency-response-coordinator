"""Validated road graphs with distances in kilometres."""

from math import asin, cos, isfinite, radians, sin, sqrt

import networkx as nx


def _number(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _identifier(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def straight_line_km(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * asin(min(1.0, sqrt(max(0.0, h))))


def build_graph(locations: list[dict], roads: list[dict], *, directed: bool = False) -> nx.Graph:
    """Build a new graph; never mutate input. Blocked roads are omitted.

    Directed records allow travel from source to target only. For parallel
    directed roads, use the shortest open edge (ties by road ID). Self-loops
    and parallel undirected roads are rejected.
    The heuristic scale makes A* safe even for custom distances shorter than
    the geographical straight line. Call again whenever road state changes.
    """
    graph = nx.DiGraph() if directed else nx.Graph()
    for location in locations:
        node = _identifier(location.get("id"), "Location id")
        if node in graph:
            raise ValueError(f"Duplicate location: {node}")
        name = _identifier(location.get("name"), "Location name")
        lat = _number(location.get("lat"), "Latitude")
        lon = _number(location.get("lon"), "Longitude")
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError("Coordinates out of range")
        graph.add_node(node, name=name, lat=lat, lon=lon)

    seen_ids, seen_pairs = set(), set()
    scale = 1.0
    for road in roads:
        road_id = _identifier(road.get("id"), "Road id")
        source = _identifier(road.get("source"), "Road source")
        target = _identifier(road.get("target"), "Road target")
        if source not in graph or target not in graph:
            raise ValueError(f"Unknown endpoint for road {road_id}")
        pair = frozenset((source, target))
        if road_id in seen_ids or (not directed and pair in seen_pairs):
            raise ValueError(f"Duplicate road id or endpoints: {road_id}")
        if source == target:
            raise ValueError("Self-loop roads are not supported")
        seen_ids.add(road_id)
        if not directed:
            seen_pairs.add(pair)
        distance = _number(road.get("distance_km"), "Road distance")
        if distance <= 0:
            raise ValueError("Road distance must be positive")
        if type(road.get("blocked")) is not bool:
            raise ValueError("Road blocked must be a boolean")
        if not road["blocked"]:
            previous = graph.get_edge_data(source, target)
            if previous and (previous["distance_km"], previous["id"]) <= (distance, road_id):
                continue
            graph.add_edge(source, target, id=road_id, distance_km=distance)
            direct = straight_line_km(graph.nodes[source], graph.nodes[target])
            if direct > 0:
                scale = min(scale, distance / direct)
    graph.graph["heuristic_scale"] = scale * (1 - 1e-12)
    graph.graph["contract_version"] = "1.0"
    return graph
