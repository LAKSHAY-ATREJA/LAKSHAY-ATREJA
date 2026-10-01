from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class InvalidTransition(ValueError):
    pass


@dataclass(frozen=True)
class OrderItem:
    sku: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError("sku must not be empty")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.unit_price < 0:
            raise ValueError("unit_price must not be negative")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class OrderEvent:
    order_id: str
    event_type: str
    occurred_at: datetime
    status: OrderStatus


@dataclass
class Order:
    id: str
    customer_id: str
    items: list[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.customer_id.strip():
            raise ValueError("id and customer_id are required")
        if not self.items:
            raise ValueError("an order requires at least one item")

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), start=Decimal("0"))

    def transition(self, target: OrderStatus) -> None:
        allowed = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
            OrderStatus.CONFIRMED: {OrderStatus.FULFILLED, OrderStatus.CANCELLED},
            OrderStatus.FULFILLED: set(),
            OrderStatus.CANCELLED: set(),
        }
        if target not in allowed[self.status]:
            raise InvalidTransition(f"cannot transition {self.status} -> {target}")
        self.status = target
