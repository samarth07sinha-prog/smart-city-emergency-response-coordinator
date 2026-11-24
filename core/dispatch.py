"""Select the available suitable vehicle with the smallest reachable distance."""

import networkx as nx

from .graph import _identifier
from .fleet_search import fleet_routes

INCIDENT_VEHICLES = {"medical": "ambulance", "fire": "fire_engine", "police": "police"}


def select_vehicle(graph: nx.Graph, vehicles: list[dict], incident: dict) -> dict:
    """Pure preview: does not mark a vehicle busy or change its location.

    Equal distances are resolved by lexicographically smaller vehicle id.
    Invalid incidents or vehicle records raise ValueError.
    """
    required_type, goal = _incident_target(graph, incident)
    candidates = [v for v in _available_vehicles(graph, vehicles)
                  if v["type"] == required_type]
    empty = {"vehicle_id": None, "route": [], "distance_km": None}
    if not candidates:
        return {"status": "no_suitable_vehicle", **empty}
    origins = [(v["id"], v["location_id"]) for v in candidates]
    best = fleet_routes(graph, origins, [goal]).get(goal)
    if best is None:
        return {"status": "no_reachable_vehicle", **empty}
    return {"status": "ok", "vehicle_id": best["vehicle_id"], "route": best["path"],
            "distance_km": best["distance_km"]}


def _incident_target(graph, incident):
    incident_type = incident.get("type")
    if incident_type not in INCIDENT_VEHICLES:
        raise ValueError("Incident type must be medical, fire, or police")
    goal = incident.get("location_id")
    if goal not in graph:
        raise ValueError("Incident must have a known location_id")
    return INCIDENT_VEHICLES[incident_type], goal


def _available_vehicles(graph, vehicles):
    available, ids = [], set()
    for vehicle in vehicles:
        vehicle_id = _identifier(vehicle.get("id"), "Vehicle id")
        if vehicle_id in ids:
            raise ValueError(f"Duplicate vehicle: {vehicle_id}")
        ids.add(vehicle_id)
        if vehicle.get("type") not in INCIDENT_VEHICLES.values():
            raise ValueError(f"Unknown vehicle type for {vehicle_id}")
        if vehicle.get("location_id") not in graph:
            raise ValueError(f"Unknown vehicle location for {vehicle_id}")
        if type(vehicle.get("available")) is not bool:
            raise ValueError("Vehicle available must be a boolean")
        if vehicle["available"]:
            available.append(vehicle)
    return sorted(available, key=lambda v: v["id"])
