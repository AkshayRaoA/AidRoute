import argparse
import csv
from pathlib import Path

from allocator import (
    FairnessFirstStrategy,
    StrictUrgencyStrategy,
    allocate_tier_one,
    allocate_tier_three,
    simulate_tier_two,
)
from graph import RoadGraph
from models import Request, Road, Warehouse


DATA_DIRECTORY = (
    Path(__file__).parent / "data"
)


def load_warehouses(
    path: Path,
) -> list[Warehouse]:

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:

        return [
            Warehouse(
                id=row["id"],
                location=row["location"],
                stock={
                    "WATER": int(row["water"]),
                    "MEDICINE": int(row["medicine"]),
                    "FOOD": int(row["food"]),
                },
            )
            for row in csv.DictReader(file)
        ]


def load_roads(
    path: Path,
) -> list[Road]:

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:

        return [
            Road(
                start=row["from"],
                end=row["to"],
                distance=int(row["distance"]),
                status=row["status"],
            )
            for row in csv.DictReader(file)
        ]


def load_requests(
    path: Path,
) -> list[Request]:

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:

        return [
            Request(
                order=int(row["order"]),
                request_id=row["request_id"],
                zone=row["zone"],
                resource=row["resource"],
                quantity=int(row["quantity"]),
                urgency=int(row["urgency"]),
                tick=int(row["tick"]),
            )
            for row in csv.DictReader(file)
        ]


def run_tier_one() -> None:

    warehouses = load_warehouses(
        DATA_DIRECTORY / "warehouses.csv"
    )

    roads = load_roads(
        DATA_DIRECTORY / "roads.csv"
    )

    requests = load_requests(
        DATA_DIRECTORY / "requests.csv"
    )

    # Tier 1:
    # DAMAGED roads are treated as normally passable.
    graph = RoadGraph(
        roads,
        damaged_penalty=1,
    )

    for line in allocate_tier_one(
        requests,
        warehouses,
        graph,
    ):
        print(line)


def run_tier_two(
    strategy_name: str = "strict",
) -> None:

    warehouses = load_warehouses(
        DATA_DIRECTORY / "warehouses.csv"
    )

    roads = load_roads(
        DATA_DIRECTORY / "roads.csv"
    )

    requests = load_requests(
        DATA_DIRECTORY / "requests.csv"
    )

    # Tier 2:
    # DAMAGED roads have a 3x distance penalty.
    graph = RoadGraph(
        roads,
        damaged_penalty=3,
    )

    if strategy_name.lower() == "fairness":

        strategy = FairnessFirstStrategy()
        display_name = "FAIRNESS"

    else:

        strategy = StrictUrgencyStrategy()
        display_name = "STRICT"

    print(
        f"========== TIER 2 ({display_name}) =========="
    )

    for line in simulate_tier_two(
        requests,
        warehouses,
        graph,
        strategy,
        final_tick=5,
    ):
        print(line)


def run_tier_three() -> None:
    print("========== TIER 3 ==========")

    warehouses = load_warehouses(DATA_DIRECTORY / "warehouses.csv")
    roads = load_roads(DATA_DIRECTORY / "roads.csv")
    requests = load_requests(DATA_DIRECTORY / "requests.csv")
    graph = RoadGraph(roads, damaged_penalty=3)

    for line in allocate_tier_three(requests, warehouses, graph):
        print(line)


def main(
    tier: int = 1,
    strategy_name: str = "strict",
) -> None:

    if tier == 1:
        run_tier_one()

    elif tier == 2:
        run_tier_two(strategy_name)

    elif tier == 3:
        run_tier_three()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Relief resource allocator"
    )

    parser.add_argument(
        "--tier",
        type=int,
        choices=(1, 2, 3),
        default=1,
        help="Run Tier 1, Tier 2, or Tier 3",
    )

    parser.add_argument(
        "--strategy",
        choices=("strict", "fairness"),
        default="strict",
        help="Tier 2 allocation strategy",
    )

    args = parser.parse_args()

    main(
        args.tier,
        args.strategy,
    )