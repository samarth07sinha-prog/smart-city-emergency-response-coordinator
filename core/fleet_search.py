"""Uniform-cost searches shared across vehicles and incident destinations."""

from heapq import heappop, heappush


def fleet_routes(graph, origins, goals):
    """Find the nearest named origin for each goal, breaking ties by origin ID.

    Seeding multiple origins handles one dispatch in a single forward search.
    Seeding one origin and multiple goals builds one tree for a batch. Stop
    once every requested destination is settled; unreachable goals are omitted.
    """
    remaining = set(goals)
    frontier, labels, parent, result = [], {}, {}, {}
    for owner, node in origins:
        label = (0.0, owner)
        if node not in labels or label < labels[node]:
            labels[node] = label
            parent[node] = None
            heappush(frontier, (*label, node))

    while frontier and remaining:
        distance, owner, node = heappop(frontier)
        if (distance, owner) != labels[node]:
            continue
        if node in remaining:
            path = [node]
            while parent[path[-1]] is not None:
                path.append(parent[path[-1]])
            path.reverse()
            length = sum(graph[a][b]["distance_km"] for a, b in zip(path, path[1:]))
            result[node] = {"vehicle_id": owner, "path": path, "distance_km": float(length)}
            remaining.remove(node)
            if not remaining:
                break
        for neighbor, road in graph[node].items():
            label = (distance + road["distance_km"], owner)
            if neighbor not in labels or label < labels[neighbor]:
                labels[neighbor] = label
                parent[neighbor] = node
                heappush(frontier, (*label, neighbor))
    return result
