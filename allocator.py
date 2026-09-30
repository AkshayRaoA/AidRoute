from abc import ABC, abstractmethod
from dataclasses import dataclass

from graph import RoadGraph
from models import Request, Warehouse


@dataclass
class PendingRequest:
    request: Request
    remaining: int
    urgency: int
    escalated: bool = False


class AllocationStrategy(ABC):

    @abstractmethod
    def allocate(
        self,
        pending: list[PendingRequest],
        warehouses: list[Warehouse],
        graph: RoadGraph,
    ) -> list[str]:
        pass


def _allocate_from_warehouses(
    pending_request: PendingRequest,
    warehouses: list[Warehouse],
    graph: RoadGraph,
    quantity: int,
) -> tuple[int, list[tuple[str, int]]]:
    """
    Allocate a quantity from reachable warehouses in nearest-first order.

    Returns:
        allocated amount
        list of (warehouse_id, allocated_amount)
    """

    request = pending_request.request

    allocated = 0
    sources: list[tuple[str, int]] = []

    ordered_warehouses = graph.warehouses_by_distance(
        request.zone,
        warehouses,
    )

    for warehouse in ordered_warehouses:

        if allocated == quantity:
            break

        available = warehouse.available(
            request.resource
        )

        amount = min(
            quantity - allocated,
            available,
        )

        if amount > 0:
            warehouse.remove(
                request.resource,
                amount,
            )

            allocated += amount

            sources.append(
                (warehouse.id, amount)
            )

    pending_request.remaining -= allocated

    return allocated, sources


def _format_result(
    pending_request: PendingRequest,
    allocated: int,
    sources: list[tuple[str, int]],
) -> str:

    request = pending_request.request

    # Status is based on cumulative allocation.
    if pending_request.remaining == 0:
        status = "FULFILLED"

    elif pending_request.remaining < request.quantity:
        status = "PARTIAL"

    else:
        status = "UNFULFILLED"

    if sources:
        source_text = " + ".join(
            f"{warehouse_id}({amount})"
            for warehouse_id, amount in sources
        )
    else:
        source_text = "NONE"

    return (
        f"[Zone {request.zone}] "
        f"requested {request.quantity} "
        f"{request.resource} "
        f"(urgency {pending_request.urgency}) "
        f"-> allocated {allocated} "
        f"from {source_text} "
        f"({status}, "
        f"remaining {pending_request.remaining})"
    )


class StrictUrgencyStrategy(AllocationStrategy):

    def allocate(
        self,
        pending: list[PendingRequest],
        warehouses: list[Warehouse],
        graph: RoadGraph,
    ) -> list[str]:

        output = []

        ordered = sorted(
            pending,
            key=lambda item: (
                -item.urgency,
                item.request.order,
            ),
        )

        for item in ordered:

            if item.remaining <= 0:
                continue

            allocated, sources = _allocate_from_warehouses(
                item,
                warehouses,
                graph,
                item.remaining,
            )

            output.append(
                _format_result(
                    item,
                    allocated,
                    sources,
                )
            )

        return output


class FairnessFirstStrategy(AllocationStrategy):

    def allocate(
        self,
        pending: list[PendingRequest],
        warehouses: list[Warehouse],
        graph: RoadGraph,
    ) -> list[str]:

        allocated_by_request = {
            id(item): 0
            for item in pending
        }

        sources_by_request = {
            id(item): []
            for item in pending
        }

        active = [
            item
            for item in pending
            if item.remaining > 0
        ]

        # Round-robin: one unit at a time.
        while active:

            next_round = []

            for item in active:

                if item.remaining <= 0:
                    continue

                allocated, sources = (
                    _allocate_from_warehouses(
                        item,
                        warehouses,
                        graph,
                        1,
                    )
                )

                allocated_by_request[
                    id(item)
                ] += allocated

                sources_by_request[
                    id(item)
                ].extend(sources)

                if item.remaining > 0 and allocated > 0:
                    next_round.append(item)

            active = next_round

        output = []

        for item in pending:

            if (
                item.remaining == item.request.quantity
                and allocated_by_request[id(item)] == 0
            ):
                # Still show requests that received nothing.
                output.append(
                    _format_result(
                        item,
                        0,
                        [],
                    )
                )

            elif allocated_by_request[id(item)] > 0:

                # Combine repeated warehouse allocations.
                combined: dict[str, int] = {}

                for warehouse_id, amount in sources_by_request[
                    id(item)
                ]:
                    combined[warehouse_id] = (
                        combined.get(warehouse_id, 0)
                        + amount
                    )

                sources = list(
                    combined.items()
                )

                output.append(
                    _format_result(
                        item,
                        allocated_by_request[id(item)],
                        sources,
                    )
                )

        return output


def allocate_tier_one(
    requests: list[Request],
    warehouses: list[Warehouse],
    graph: RoadGraph,
) -> list[str]:

    output = []

    ordered_requests = sorted(
        requests,
        key=lambda item: (
            -item.urgency,
            item.order,
        ),
    )

    for request in ordered_requests:

        warehouse = graph.nearest_warehouse(
            request.zone,
            warehouses,
        )

        allocated = 0
        warehouse_id = "NONE"

        if warehouse is not None:

            warehouse_id = warehouse.id

            allocated = min(
                request.quantity,
                warehouse.available(
                    request.resource
                ),
            )

            if allocated > 0:
                warehouse.remove(
                    request.resource,
                    allocated,
                )

        if allocated == request.quantity:
            status = "FULFILLED"

        elif allocated == 0:
            status = "UNFULFILLED"

        else:
            status = "PARTIAL"

        output.append(
            f"[Zone {request.zone}] "
            f"requested {request.quantity} "
            f"{request.resource} "
            f"(urgency {request.urgency}) "
            f"-> allocated {allocated} "
            f"from {warehouse_id}"
            f"({status})"
        )

    return output


def simulate_tier_two(
    requests: list[Request],
    warehouses: list[Warehouse],
    graph: RoadGraph,
    strategy: AllocationStrategy,
    final_tick: int = 5,
) -> list[str]:

    pending: list[PendingRequest] = []

    output: list[str] = []

    requests_by_tick: dict[
        int,
        list[Request],
    ] = {}

    for request in requests:
        requests_by_tick.setdefault(
            request.tick,
            [],
        ).append(request)

    for tick in range(
        1,
        final_tick + 1,
    ):

        # Submit requests scheduled for this tick.
        new_requests = requests_by_tick.get(
            tick,
            [],
        )

        for request in new_requests:

            pending.append(
                PendingRequest(
                    request=request,
                    remaining=request.quantity,
                    urgency=request.urgency,
                )
            )

            output.append(
                f"[Tick {tick}] "
                f"{request.request_id} submitted"
            )

        # Escalate requests that have remained unresolved
        # for at least 3 ticks.
        for item in pending:

            if (
                item.remaining > 0
                and not item.escalated
                and tick - item.request.tick >= 3
            ):

                old_urgency = item.urgency

                item.urgency = min(
                    5,
                    item.urgency + 1,
                )

                # Mark as escalated even when already at 5,
                # so escalation is never repeated.
                item.escalated = True

                if item.urgency != old_urgency:

                    output.append(
                        f"[Tick {tick}] "
                        f"{item.request.request_id} "
                        f"urgency escalated "
                        f"from {old_urgency} "
                        f"to {item.urgency}"
                    )

        if pending:

            output.append(
                f"[Tick {tick}] allocations:"
            )

            output.extend(
                strategy.allocate(
                    pending,
                    warehouses,
                    graph,
                )
            )

        # Remove fulfilled requests.
        pending = [
            item
            for item in pending
            if item.remaining > 0
        ]

    # Final report.
    if pending:

        output.append(
            "[Final] Unfulfilled requests:"
        )

        for item in pending:

            output.append(
                f"{item.request.request_id}: "
                f"{item.remaining} remaining"
            )

    else:

        output.append(
            "[Final] All requests fulfilled."
        )

    return output


def allocate_tier_three(
    requests: list[Request],
    warehouses: list[Warehouse],
    graph: RoadGraph,
) -> list[str]:
    results: list[tuple[Request, int, str, list[str]]] = []
    output: list[str] = []

    for request in sorted(requests, key=lambda item: (-item.urgency, item.order)):
        routes = [
            (warehouse, graph.route_to(request.zone, warehouse.id))
            for warehouse in warehouses
        ]
        reachable_routes = [
            (warehouse, route)
            for warehouse, route in routes
            if route is not None
        ]

        if not reachable_routes:
            results.append((request, 0, "UNREACHABLE", []))
            output.append(
                f"[Zone {request.zone}] {request.resource} "
                f"0/{request.quantity} (UNREACHABLE) path NONE"
            )
            continue

        reachable_routes.sort(key=lambda item: (item[1][0], item[0].id))
        allocated = 0
        paths: list[str] = []

        for warehouse, route in reachable_routes:
            if allocated == request.quantity:
                break
            amount = min(
                request.quantity - allocated,
                warehouse.available(request.resource),
            )
            if amount:
                warehouse.remove(request.resource, amount)
                allocated += amount
                distance, nodes = route
                paths.append(
                    f"{warehouse.id}: {' -> '.join(nodes)} ({distance} km, {amount})"
                )

        status = (
            "FULFILLED"
            if allocated == request.quantity
            else "PARTIAL"
            if allocated > 0
            else "UNFULFILLED"
        )
        results.append((request, allocated, status, paths))
        output.append(
            f"[Zone {request.zone}] {request.resource} "
            f"{allocated}/{request.quantity} ({status}) "
            f"path {' | '.join(paths) if paths else 'NONE'}"
        )

    output.append("=== FINAL ALLOCATION REPORT ===")
    fulfilled = partial = unfulfilled = unreachable = 0
    for request, allocated, status, _ in results:
        if status == "FULFILLED":
            fulfilled += 1
        elif status == "PARTIAL":
            partial += 1
        elif status == "UNREACHABLE":
            unreachable += 1
        else:
            unfulfilled += 1
        output.append(
            f"{request.zone}: {request.resource} {allocated}/{request.quantity} "
            f"({status})"
        )

    output.append(
        f"Total requests: {len(results)} | Fulfilled: {fulfilled} | "
        f"Partial: {partial} | Unfulfilled: {unfulfilled} | "
        f"Unreachable: {unreachable}"
    )
    return output