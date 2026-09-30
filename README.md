# Relief Resource Allocation

A Python console application that allocates limited relief resources from warehouses to affected zones while considering urgency, fairness, stock limits, and road damage.

## Source Files

- `main.py` - CSV loading, command-line interface, and tier runners.
- `models.py` - Warehouse, road, and request data models.
- `graph.py` - Undirected road graph and Dijkstra shortest-path routing.
- `allocator.py` - Allocation strategies and tier simulations.
- `data/` - Warehouse, road, zone, and request CSV files.

## Implemented Strategies

- **Strict urgency first**: processes requests by descending urgency, then input order. Tier 2 can combine stock from the nearest reachable warehouses.
- **Fairness first**: allocates one unit at a time in round-robin order across pending requests, preventing one request from consuming all available stock immediately.

Tier 3 reports the actual shortest route and distance for each warehouse used, including routes through intermediate nodes.

## Assumptions

- Roads are undirected.
- `BLOCKED` roads are impassable.
- In Tier 1, damaged roads remain passable at their listed distance.
- In Tiers 2 and 3, damaged-road distance is multiplied by 3.
- A request may receive stock from multiple reachable warehouses in nearest-first order.
- A reachable request with insufficient stock is `PARTIAL` or `UNFULFILLED`; a request with no route to any warehouse is `UNREACHABLE`.
- Requests unresolved after three processing ticks have urgency increased by one, capped at five.
- Input CSV headers and resource names are expected to match the supplied files.

## Running

From the project directory:

```powershell
python main.py --tier 1
python main.py --tier 2 --strategy strict
python main.py --tier 2 --strategy fairness
python main.py --tier 3
```

Tier 3 prints a final allocation report with fulfilled, partial, unfulfilled, and unreachable totals.

## Future Improvements

With more time, I would:

- Add automated tests.
- Check CSV data for errors before running.
- Let users change the road penalty and number of simulation ticks.
- Save results as JSON or CSV files.
- Add truck capacity and delivery times.
- Support roads that change status during the simulation.
- Support new stock arriving at warehouses.

### Submission package

```text
Relief Resource Allocation/
│
├── main.py
├── models.py
├── graph.py
├── allocator.py
├── README.md
│
└── data/
    ├── warehouses.csv
    ├── zones.csv
    ├── roads.csv
    └── requests.csv