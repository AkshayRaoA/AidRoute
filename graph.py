import heapq

from models import Road, Warehouse


class RoadGraph:
    def __init__(
        self,
        roads: list[Road],
        damaged_penalty: int = 1,
    ) -> None:
        self._adjacency: dict[str, list[tuple[str, int]]] = {}

        for road in roads:
            status = road.status.upper()

            # BLOCKED roads cannot be used.
            if status == "BLOCKED":
                continue

            distance = road.distance

            # Apply penalty to DAMAGED roads.
            if status == "DAMAGED":
                distance *= damaged_penalty

            # Roads are undirected.
            self._adjacency.setdefault(
                road.start, []
            ).append((road.end, distance))

            self._adjacency.setdefault(
                road.end, []
            ).append((road.start, distance))

    def warehouses_by_distance(
        self,
        zone: str,
        warehouses: list[Warehouse],
    ) -> list[Warehouse]:
        distances = self._shortest_paths(zone)

        reachable = [
            warehouse
            for warehouse in warehouses
            if warehouse.id in distances
        ]

        return sorted(
            reachable,
            key=lambda warehouse: (
                distances[warehouse.id],
                warehouse.id,
            ),
        )

    def nearest_warehouse(
        self,
        zone: str,
        warehouses: list[Warehouse],
    ) -> Warehouse | None:
        ordered = self.warehouses_by_distance(zone, warehouses)

        if not ordered:
            return None

        return ordered[0]

    def route_to(self, start: str, target: str) -> tuple[int, list[str]] | None:
        distances = {start: 0}
        previous: dict[str, str] = {}
        pending = [(0, start)]

        while pending:
            distance, node = heapq.heappop(pending)
            if distance != distances[node]:
                continue
            if node == target:
                break

            for neighbor, edge_distance in self._adjacency.get(node, []):
                new_distance = distance + edge_distance
                if new_distance < distances.get(neighbor, float("inf")):
                    distances[neighbor] = new_distance
                    previous[neighbor] = node
                    heapq.heappush(pending, (new_distance, neighbor))

        if target not in distances:
            return None

        path = [target]
        while path[-1] != start:
            path.append(previous[path[-1]])
        path.reverse()
        return distances[target], path

    def _shortest_paths(
        self,
        start: str,
    ) -> dict[str, int]:
        distances = {start: 0}
        pending = [(0, start)]

        while pending:
            distance, node = heapq.heappop(pending)

            if distance != distances[node]:
                continue

            for neighbor, edge_distance in self._adjacency.get(
                node, []
            ):
                new_distance = distance + edge_distance

                if new_distance < distances.get(
                    neighbor,
                    float("inf"),
                ):
                    distances[neighbor] = new_distance

                    heapq.heappush(
                        pending,
                        (new_distance, neighbor),
                    )

        return distances