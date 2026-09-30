from dataclasses import dataclass, field


@dataclass
class Warehouse:
    id: str
    location: str
    stock: dict[str, int] = field(default_factory=dict)

    def available(self, resource: str) -> int:
        return self.stock.get(resource, 0)

    def remove(self, resource: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if quantity > self.available(resource):
            raise ValueError(
                f"Insufficient {resource} in warehouse {self.id}"
            )

        self.stock[resource] -= quantity


@dataclass(frozen=True)
class Road:
    start: str
    end: str
    distance: int
    status: str


@dataclass(frozen=True)
class Request:
    order: int
    request_id: str
    zone: str
    resource: str
    quantity: int
    urgency: int
    tick: int