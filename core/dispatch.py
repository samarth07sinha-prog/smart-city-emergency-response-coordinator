"""Select the available suitable vehicle with the smallest reachable distance."""

import networkx as nx

from .graph import _identifier
from .routing import find_route

INCIDENT_VEHICLES = {"medical": "ambulance", "fire": "fire_engine", "police": "police"}


def select_vehicle(graph: nx.Graph, vehicles: list[dict], incident: dict) -> dict:
    """Pure preview: does not mark a vehicle busy or change its location.

    Equal distances are resolved by lexicographically smaller vehicle id.
    Invalid incidents or vehicle records raise ValueError.
    """
    incident_type = incident.get("type")
    if incident_type not in INCIDENT_VEHICLES:
        raise ValueError("Incident type must be medical, fire, or police")
    goal = incident.get("location_id")
    if goal not in graph:
        raise ValueError("Incident must have a known location_id")
    candidates, ids = [], set()
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
        if vehicle["available"] and vehicle["type"] == INCIDENT_VEHICLES[incident_type]:
            candidates.append(vehicle)

    empty = {"vehicle_id": None, "route": [], "distance_km": None}
    if not candidates:
        return {"status": "no_suitable_vehicle", **empty}
    best = None
    for vehicle in sorted(candidates, key=lambda v: v["id"]):
        route = find_route(graph, vehicle["location_id"], goal, "UCS")
        if route["status"] == "ok":
            if best is None or route["distance_km"] < best["distance_km"]:
                best = {
                    "status": "ok", "vehicle_id": vehicle["id"],
                    "route": route["path"], "distance_km": route["distance_km"],
                }
    return best if best is not None else {"status": "no_reachable_vehicle", **empty}
