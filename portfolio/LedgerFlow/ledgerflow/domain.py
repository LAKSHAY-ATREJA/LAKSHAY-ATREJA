from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from threading import RLock
from time import time
from uuid import uuid4


@dataclass(frozen=True)
class Posting:
    account_id: str
    amount: Decimal


@dataclass(frozen=True)
class JournalEntry:
    id: str
    reference: str
    postings: tuple[Posting, ...]
    created_at: float = field(default_factory=time)


class LedgerError(ValueError):
    pass


class Ledger:
    """Thread-safe in-memory double-entry ledger domain model."""

    def __init__(self):
        self._entries: list[JournalEntry] = []
        self._balances: dict[str, Decimal] = {}
        self._idempotency: dict[str, JournalEntry] = {}
        self._lock = RLock()

    def post(self, reference: str, postings: list[Posting], idempotency_key: str) -> JournalEntry:
        if not idempotency_key or not idempotency_key.strip():
            raise LedgerError("idempotency_key is required")
        if any(not p.account_id.strip() or not p.amount.is_finite() for p in postings):
            raise LedgerError("postings require named accounts and finite amounts")
        if len(postings) < 2:
            raise LedgerError("an entry requires at least two postings")
        if sum((p.amount for p in postings), Decimal("0")) != Decimal("0"):
            raise LedgerError("postings must sum to zero")
        with self._lock:
            if idempotency_key in self._idempotency:
                previous = self._idempotency[idempotency_key]
                if previous.reference != reference or previous.postings != tuple(postings):
                    raise LedgerError("idempotency key already used for a different request")
                return previous
            entry = JournalEntry(str(uuid4()), reference, tuple(postings))
            for p in postings:
                self._balances[p.account_id] = (
                    self._balances.get(p.account_id, Decimal("0")) + p.amount
                )
            self._entries.append(entry)
            self._idempotency[idempotency_key] = entry
            return entry

    def transfer(
        self, source: str, destination: str, amount: Decimal, idempotency_key: str
    ) -> JournalEntry:
        if not amount.is_finite() or amount <= 0:
            raise LedgerError("amount must be positive")
        if source == destination:
            raise LedgerError("source and destination must differ")
        return self.post(
            reference=f"transfer:{source}->{destination}",
            postings=[Posting(source, -amount), Posting(destination, amount)],
            idempotency_key=idempotency_key,
        )

    def balance(self, account_id: str) -> Decimal:
        with self._lock:
            return self._balances.get(account_id, Decimal("0"))

    def audit(self) -> tuple[JournalEntry, ...]:
        with self._lock:
            return tuple(self._entries)
