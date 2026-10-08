from decimal import Decimal
import pytest
from ledgerflow.domain import Ledger, LedgerError


def test_transfer_is_balanced_and_idempotent():
    l = Ledger()
    a = l.transfer("cash", "merchant", Decimal("42.50"), "req-1")
    b = l.transfer("cash", "merchant", Decimal("42.50"), "req-1")
    assert a.id == b.id
    assert l.balance("cash") == Decimal("-42.50")
    assert l.balance("merchant") == Decimal("42.50")
    assert len(l.audit()) == 1


def test_rejects_unbalanced_entry():
    from ledgerflow.domain import Posting

    with pytest.raises(LedgerError):
        Ledger().post("bad", [Posting("a", Decimal("1")), Posting("b", Decimal("2"))], "x")
