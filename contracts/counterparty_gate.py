# v0.1.0
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

# CounterpartyGate - a minimal consumer that composes two GenLayer verdicts into
# one onboarding control: a UK company is onboarded, and later paid, only if
#   - KYB Desk approves it right now (a fresh, unexpired GOOD_STANDING check of
#     the Companies House register), AND
#   - SanctionsScreen clears the subject the owner pairs with it (a fresh
#     NO_MATCH against a recent OFAC list).
# Both are checked again at the moment of every payment: onboarding is a
# record, never a standing permission. Anything else - a failed company check,
# a name or address match, a possible match, an undetermined screening, nothing
# on record, a stale answer - reverts, and the revert says which control said no.
#
# The owner pairs a company number with a subject_id; the gate cannot tell
# whether the screened name is the company's, so the pairing is the owner's act
# and is on the record.
#
# GenVM v0.2.11 conventions (locally tested source of truth);
# contracts/counterparty_gate_studio_next.py is the deployed port.
# Header must end in a blank line (real GenVM v0.2.11 requirement).

from genlayer import *
import datetime
import re

MAX_PAGE_LIMIT = 50


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise gl.vm.UserError(message)


def _now() -> datetime.datetime:
    return datetime.datetime.fromisoformat(gl.message_raw['datetime'])


@allow_storage
class Counterparty:
    subject_id: str
    onboarded_by: Address
    onboarded_at: datetime.datetime
    paid: u256


@allow_storage
class Payment:
    company_number: str
    subject_id: str
    amount: u256
    paid_by: Address
    paid_at: datetime.datetime


class CounterpartyGate(gl.Contract):
    owner: Address
    kyb_address: Address
    sanctions_address: Address
    max_age_seconds: u32
    max_list_age_days: u32
    counterparties: TreeMap[str, Counterparty]
    payments: DynArray[Payment]

    def __init__(self, kyb_address: str, sanctions_address: str, max_age_seconds: u32, max_list_age_days: u32) -> None:
        _require(max_age_seconds > 0, "max_age_seconds must be positive")
        _require(max_list_age_days > 0, "max_list_age_days must be positive")
        self.owner = gl.message.sender_address
        self.kyb_address = Address(kyb_address)
        self.sanctions_address = Address(sanctions_address)
        self.max_age_seconds = max_age_seconds
        self.max_list_age_days = max_list_age_days

    def _both_say_yes(self, company_number: str, subject_id: str) -> None:
        kyb = gl.get_contract_at(self.kyb_address).view().get_approval(company_number, self.max_age_seconds)
        _require(kyb["approved"], f"{company_number!r} refused: KYB Desk says {kyb['reason']}")
        screen = gl.get_contract_at(self.sanctions_address)
        cleared = screen.view().is_cleared(subject_id, self.max_age_seconds, self.max_list_age_days)
        _require(cleared, f"{company_number!r} refused: SanctionsScreen says {screen.view().latest_verdict(subject_id)} "
                          f"for {subject_id!r}, not a fresh NO_MATCH against a recent list")

    # Owner only: the gate demonstrates a consumer.
    @gl.public.write
    def onboard(self, company_number: str, subject_id: str) -> None:
        _require(gl.message.sender_address == self.owner, "only the owner can onboard counterparties")
        _require(company_number not in self.counterparties, "already onboarded")
        self._both_say_yes(company_number, subject_id)
        c = self.counterparties.get_or_insert_default(company_number)
        c.subject_id = subject_id
        c.onboarded_by = gl.message.sender_address
        c.onboarded_at = _now()
        c.paid = u256(0)

    # Owner only. Both controls are asked again, right now.
    @gl.public.write
    def pay(self, company_number: str, amount: u256) -> None:
        _require(gl.message.sender_address == self.owner, "only the owner can pay counterparties")
        _require(amount > 0, "amount must be positive")
        _require(company_number in self.counterparties, f"{company_number!r} is not onboarded")
        c = self.counterparties[company_number]
        self._both_say_yes(company_number, c.subject_id)
        record = self.payments.append_new_get()
        record.company_number = company_number
        record.subject_id = c.subject_id
        record.amount = amount
        record.paid_by = gl.message.sender_address
        record.paid_at = _now()
        c.paid = u256(int(c.paid) + int(amount))

    @gl.public.view
    def get_counterparty(self, company_number: str) -> dict:
        _require(company_number in self.counterparties, "not onboarded")
        c = self.counterparties[company_number]
        return {"company_number": company_number, "subject_id": c.subject_id, "onboarded_by": c.onboarded_by.as_hex,
                "onboarded_at": c.onboarded_at.isoformat(), "paid": str(c.paid)}

    @gl.public.view
    def list_counterparties(self) -> list:
        return [{"company_number": k, "subject_id": c.subject_id, "paid": str(c.paid)} for k, c in self.counterparties.items()]

    @gl.public.view
    def get_payments(self, offset: u32, limit: u32) -> list:
        limit = min(limit, MAX_PAGE_LIMIT)
        out = []
        i = len(self.payments) - 1 - offset
        while i >= 0 and len(out) < limit:
            p = self.payments[i]
            out.append({"company_number": p.company_number, "subject_id": p.subject_id, "amount": str(p.amount),
                        "paid_by": p.paid_by.as_hex, "paid_at": p.paid_at.isoformat()})
            i -= 1
        return out

    @gl.public.view
    def get_config(self) -> dict:
        return {"owner": self.owner.as_hex, "kyb_address": self.kyb_address.as_hex,
                "sanctions_address": self.sanctions_address.as_hex, "max_age_seconds": self.max_age_seconds,
                "max_list_age_days": self.max_list_age_days, "counterparty_count": len(self.counterparties),
                "payment_count": len(self.payments)}
