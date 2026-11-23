"""Explicit educational search implementations (no NetworkX search wrappers)."""

from collections import deque
from heapq import heappop, heappush
from itertools import count
from time import perf_counter

import networkx as nx

from .graph import straight_line_km


def find_route(graph: nx.Graph, start: str, goal: str, algorithm: str = "UCS") -> dict:
    """Return contract v1 route data. Unknown nodes/algorithms raise ValueError.

    Use an unmodified graph returned by build_graph. Rebuild after road edits.
    Expanded = unique nodes removed from the frontier for processing, goal
    included; stale heap entries are excluded. Runtime covers this search only.
    """
    began = perf_counter()
    if not isinstance(algorithm, str):
        raise ValueError("Algorithm must be BFS, DFS, UCS, or A*")
    algorithm = algorithm.strip().upper()
    if algorithm not in {"BFS", "DFS", "UCS", "A*"}:
        raise ValueError("Algorithm must be BFS, DFS, UCS, or A*")
    if start not in graph or goal not in graph:
        raise ValueError("Start and goal must be known location ids")

    parent = {start: None}
    expanded = 0
    found = False
    if algorithm in {"BFS", "DFS"}:
        frontier = deque([start])
        while frontier:
            node = frontier.popleft() if algorithm == "BFS" else frontier.pop()
            expanded += 1
            if node == goal:
                found = True
                break
            neighbors = sorted(graph.neighbors(node), reverse=algorithm == "DFS")
            for neighbor in neighbors:
                if neighbor not in parent:
                    parent[neighbor] = node
                    frontier.append(neighbor)
    else:
        serial = count()
        costs = {start: 0.0}
        closed = set()

        def heuristic(node):
            if algorithm == "UCS":
                return 0.0
            return graph.graph["heuristic_scale"] * straight_line_km(
                graph.nodes[node], graph.nodes[goal]
            )

        frontier = [(heuristic(start), next(serial), 0.0, start)]
        while frontier:
            _, _, cost, node = heappop(frontier)
            if node in closed or cost > costs[node]:
                continue
            closed.add(node)
            expanded += 1
            if node == goal:
                found = True
                break
            for neighbor in sorted(graph.neighbors(node)):
                new_cost = cost + graph[node][neighbor]["distance_km"]
                if new_cost < costs.get(neighbor, float("inf")):
                    costs[neighbor] = new_cost
                    parent[neighbor] = node
                    heappush(frontier, (
                        new_cost + heuristic(neighbor), next(serial), new_cost, neighbor
                    ))

    path = []
    if found:
        node = goal
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
    distance = sum(graph[a][b]["distance_km"] for a, b in zip(path, path[1:])) if found else None
    return {
        "status": "ok" if found else "no_path",
        "path": path,
        "distance_km": float(distance) if found else None,
        "nodes_expanded": expanded,
        "runtime_ms": (perf_counter() - began) * 1000,
    }
