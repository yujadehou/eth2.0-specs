from eth2spec.phase0 import spec
from eth_utils import (
    to_tuple
)
from gen_base import gen_suite, gen_typing
from preset_loader import loader

from helpers_deposits import build_deposit_for_index

from eth2spec.debug.edge_case import edge_case, gen_edge_case



@edge_case('valid deposit to add new validator', spec.Deposit, spec.process_deposit)
def valid_deposit():
    new_dep, state = build_deposit_for_index(10, 10)
    return state, new_dep


@edge_case('valid deposit to top-up existing validator', spec.Deposit, spec.process_deposit)
def valid_topup():
    new_dep, state = build_deposit_for_index(10, 3)
    return state, new_dep


@edge_case('invalid deposit index', spec.Deposit, spec.process_deposit, does_error=True)
def invalid_deposit_index():
    new_dep, state = build_deposit_for_index(10, 10)
    # Mess up deposit index, 1 too low
    state.deposit_index = 9
    return state, new_dep


@edge_case('invalid deposit signature', spec.Deposit, spec.process_deposit, does_error=True)
def invalid_deposit_signature():
    new_dep, state = build_deposit_for_index(10, 10)
    # Make deposit data signature (proof of possession) invalid
    new_dep.data.signature[0] ^= b'\xff'
    # TODO(@Danny): the BLS impl. in the spec does not actually verify the signature, it doesn't throw
    return state, new_dep


@edge_case('invalid deposit proof', spec.Deposit, spec.process_deposit, does_error=True)
def invalid_deposit_proof():
    new_dep, state = build_deposit_for_index(10, 10)
    # Make deposit proof invalid (at bottom of proof)
    new_dep.proof[-1] = spec.ZERO_HASH
    return state, new_dep


@to_tuple
def deposit_cases():
    # Disabled, see comment: invalid_deposit_signature
    edge_cases = [valid_deposit, valid_topup, invalid_deposit_index, invalid_deposit_proof]
    for cas_fn in edge_cases:
        cas_def = cas_fn()
        yield gen_edge_case(cas_def)


def mini_deposits_suite(configs_path: str) -> gen_typing.TestSuiteOutput:
    presets = loader.load_presets(configs_path, 'minimal')
    spec.apply_constants_preset(presets)

    return ("deposit_minimal", "deposits", gen_suite.render_suite(
        title="deposit operation",
        summary="Test suite for deposit type operation processing",
        forks_timeline="testing",
        forks=["phase0"],
        config="minimal",
        runner="operations",
        handler="deposits",
        test_cases=deposit_cases()))


def full_deposits_suite(configs_path: str) -> gen_typing.TestSuiteOutput:
    presets = loader.load_presets(configs_path, 'mainnet')
    spec.apply_constants_preset(presets)

    return ("deposit_full", "deposits", gen_suite.render_suite(
        title="deposit operation",
        summary="Test suite for deposit type operation processing",
        forks_timeline="mainnet",
        forks=["phase0"],
        config="mainnet",
        runner="operations",
        handler="deposits",
        test_cases=deposit_cases()))
