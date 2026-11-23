import copy
import unittest

import networkx as nx

from core import build_graph, find_route, load_sample_data, select_vehicle


def fixture():
    locations = [{"id": n, "name": n, "lat": 12 + i * 0.001, "lon": 77}
                 for i, n in enumerate("ABCDE")]
    roads = [{"id": str(i), "source": a, "target": b,
              "distance_km": cost, "blocked": False}
             for i, (a, b, cost) in enumerate([
                 ("A", "C", 10), ("A", "B", 1), ("B", "C", 1), ("C", "D", 1)])]
    vehicles = [
        {"id": "AMB-1", "type": "ambulance", "location_id": "A", "available": True},
        {"id": "AMB-2", "type": "ambulance", "location_id": "D", "available": True},
        {"id": "POL-1", "type": "police", "location_id": "C", "available": True},
    ]
    return locations, roads, vehicles


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.locations, self.roads, self.vehicles = fixture()
        self.graph = build_graph(self.locations, self.roads)
        self.incident = {"type": "medical", "location_id": "C"}

    def test_weighted_search_versus_bfs(self):
        self.assertEqual(find_route(self.graph, "A", "C", "BFS")["distance_km"], 10)
        for alg in ("UCS", "A*"):
            result = find_route(self.graph, "A", "C", alg)
            self.assertEqual(result["path"], ["A", "B", "C"])
            self.assertEqual(result["distance_km"], 2)

    def test_dispatch_and_unavailable_nearest(self):
        self.assertEqual(select_vehicle(self.graph, self.vehicles, self.incident)["vehicle_id"], "AMB-2")
        self.vehicles[1]["available"] = False
        result = select_vehicle(self.graph, self.vehicles, self.incident)
        self.assertEqual(result["vehicle_id"], "AMB-1")
        self.assertEqual(result["distance_km"], 2)

    def test_vehicle_type_and_no_suitable(self):
        result = select_vehicle(self.graph, self.vehicles, {"type": "police", "location_id": "C"})
        self.assertEqual(result["vehicle_id"], "POL-1")
        self.assertEqual(result["distance_km"], 0)
        self.assertEqual(select_vehicle(self.graph, self.vehicles, {"type": "fire", "location_id": "C"})["status"], "no_suitable_vehicle")

    def test_blocked_road_detour_all_algorithms(self):
        self.roads[2]["blocked"] = True
        graph = build_graph(self.locations, self.roads)
        self.assertFalse(graph.has_edge("B", "C"))
        for alg in ("BFS", "DFS", "UCS", "A*"):
            result = find_route(graph, "A", "C", alg)
            self.assertEqual(result["path"], ["A", "C"])
            self.assertEqual(result["distance_km"], 10)

    def test_no_path_and_unreachable_vehicles(self):
        for alg in ("BFS", "DFS", "UCS", "A*"):
            result = find_route(self.graph, "A", "E", alg)
            self.assertEqual(result["status"], "no_path")
            self.assertEqual(result["path"], [])
            self.assertIsNone(result["distance_km"])
        result = select_vehicle(self.graph, self.vehicles, {"type": "medical", "location_id": "E"})
        self.assertEqual(result["status"], "no_reachable_vehicle")

    def test_same_start_goal(self):
        for alg in ("BFS", "DFS", "UCS", "A*"):
            result = find_route(self.graph, "A", "A", alg)
            self.assertEqual(result["path"], ["A"])
            self.assertEqual(result["distance_km"], 0)
            self.assertEqual(result["nodes_expanded"], 1)

    def test_tie_break_and_no_mutation(self):
        self.vehicles[1]["location_id"] = "A"
        before = copy.deepcopy(self.vehicles)
        result = select_vehicle(self.graph, list(reversed(self.vehicles)), self.incident)
        self.assertEqual(result["vehicle_id"], "AMB-1")
        self.assertEqual(self.vehicles, before)

    def test_invalid_inputs(self):
        for alg in ("bad", "Dijkstra", None):
            with self.assertRaises(ValueError):
                find_route(self.graph, "A", "C", alg)
        with self.assertRaises(ValueError):
            find_route(self.graph, "missing", "C")
        with self.assertRaises(ValueError):
            select_vehicle(self.graph, self.vehicles, {"type": "unknown", "location_id": "A"})

    def test_invalid_roads(self):
        for value in (0, -1, float("nan"), float("inf"), True):
            roads = copy.deepcopy(self.roads)
            roads[0]["distance_km"] = value
            with self.assertRaises(ValueError):
                build_graph(self.locations, roads)
        with self.assertRaises(ValueError):
            build_graph(self.locations, self.roads + [self.roads[0]])

    def test_short_geographic_edges_still_optimal(self):
        for road in self.roads:
            road["distance_km"] *= 0.0001
        graph = build_graph(self.locations, self.roads)
        self.assertLess(graph.graph["heuristic_scale"], 1)
        expected = nx.dijkstra_path_length(graph, "A", "D", weight="distance_km")
        self.assertAlmostEqual(find_route(graph, "A", "D", "A*")["distance_km"], expected)

    def test_sample_all_pairs_against_reference(self):
        data = load_sample_data()
        self.assertEqual(len(data["locations"]), 20)
        graph = build_graph(data["locations"], data["roads"])
        for start in graph:
            lengths = nx.single_source_dijkstra_path_length(graph, start, weight="distance_km")
            for goal in graph:
                for alg in ("UCS", "A*"):
                    result = find_route(graph, start, goal, alg)
                    if goal in lengths:
                        self.assertAlmostEqual(result["distance_km"], lengths[goal])
                        self.assertTrue(nx.is_path(graph, result["path"]))
                    else:
                        self.assertEqual(result["status"], "no_path")

    def test_loader_is_fresh(self):
        first = load_sample_data()
        first["vehicles"][0]["available"] = False
        self.assertTrue(load_sample_data()["vehicles"][0]["available"])


if __name__ == "__main__":
    unittest.main()
