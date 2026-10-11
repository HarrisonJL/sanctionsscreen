"""
Direct Mode tests for CounterpartyGate.

Direct Mode can't simulate cross-contract calls without a "glsim" hook (the
same documented limitation as this account's earlier consumers), so the reads
of KYB Desk and SanctionsScreen are proven live instead - an allowed
onboarding and payment, and a refusal from each control, all linked in
CONTRACT.md. What's tested here is everything that runs before those calls.
"""

import pytest

KYB = "0x" + "55" * 20          # never actually called in these tests
SANCTIONS = "0x" + "66" * 20


def _deploy(direct_vm, direct_deploy, owner, max_age=86400, max_list_age=30):
    direct_vm.sender = owner
    return direct_deploy("contracts/counterparty_gate.py", KYB, SANCTIONS, max_age, max_list_age)


def test_config_and_empty_state(direct_vm, direct_deploy, direct_owner):
    gate = _deploy(direct_vm, direct_deploy, direct_owner)
    cfg = gate.get_config()
    assert cfg["kyb_address"].lower() == KYB and cfg["sanctions_address"].lower() == SANCTIONS
    assert (cfg["max_age_seconds"], cfg["max_list_age_days"], cfg["counterparty_count"], cfg["payment_count"]) == (86400, 30, 0, 0)
    assert gate.list_counterparties() == [] and gate.get_payments(0, 10) == []
    with pytest.raises(Exception, match="not onboarded"):
        gate.get_counterparty("00445790")


@pytest.mark.parametrize("max_age, max_list_age", [(0, 30), (86400, 0)])
def test_invalid_configuration_is_rejected(direct_vm, direct_deploy, direct_owner, max_age, max_list_age):
    with pytest.raises(Exception):
        _deploy(direct_vm, direct_deploy, direct_owner, max_age, max_list_age)


def test_only_the_owner_can_onboard_or_pay(direct_vm, direct_deploy, direct_owner, direct_alice):
    gate = _deploy(direct_vm, direct_deploy, direct_owner)
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="only the owner can onboard counterparties"):
        gate.onboard("00445790", "tesco")
    with pytest.raises(Exception, match="only the owner can pay counterparties"):
        gate.pay("00445790", 100)


def test_a_zero_payment_is_rejected_before_any_cross_contract_call(direct_vm, direct_deploy, direct_owner):
    gate = _deploy(direct_vm, direct_deploy, direct_owner)
    with pytest.raises(Exception, match="amount must be positive"):
        gate.pay("00445790", 0)


def test_a_company_that_was_never_onboarded_cannot_be_paid(direct_vm, direct_deploy, direct_owner):
    gate = _deploy(direct_vm, direct_deploy, direct_owner)
    with pytest.raises(Exception, match="is not onboarded"):
        gate.pay("00445790", 100)
