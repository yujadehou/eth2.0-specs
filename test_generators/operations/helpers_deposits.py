from eth2spec.phase0 import spec
from eth2spec.utils.minimal_ssz import signing_root
from eth2spec.utils.merkle_minimal import get_merkle_root, calc_merkle_tree_from_leaves, get_merkle_proof

from typing import List, Tuple

import genesis, keys
from py_ecc import bls


def build_deposit_data(state,
                       pubkey: spec.BLSPubkey,
                       withdrawal_cred: spec.Bytes32,
                       privkey: int,
                       amount: int):
    deposit_data = spec.DepositData(
        pubkey=pubkey,
        withdrawal_credentials=spec.BLS_WITHDRAWAL_PREFIX_BYTE + withdrawal_cred[1:],
        amount=amount,
    )
    deposit_data.proof_of_possession = bls.sign(
        message_hash=signing_root(deposit_data),
        privkey=privkey,
        domain=spec.get_domain(
            state,
            spec.get_current_epoch(state),
            spec.DOMAIN_DEPOSIT,
        )
    )
    return deposit_data


def build_deposit(state,
                  deposit_data_leaves: List[spec.Bytes32],
                  pubkey: spec.BLSPubkey,
                  withdrawal_cred: spec.Bytes32,
                  privkey: int,
                  amount: int) -> spec.Deposit:

    deposit_data = build_deposit_data(state, pubkey, withdrawal_cred, privkey, amount)

    item = spec.hash(deposit_data.serialize())
    index = len(deposit_data_leaves)
    deposit_data_leaves.append(item)
    tree = calc_merkle_tree_from_leaves(tuple(deposit_data_leaves))
    proof = list(get_merkle_proof(tree, item_index=index))

    deposit = spec.Deposit(
        proof=list(proof),
        index=index,
        data=deposit_data,
    )
    assert spec.verify_merkle_branch(item, proof, spec.DEPOSIT_CONTRACT_TREE_DEPTH, index, get_merkle_root(tuple(deposit_data_leaves)))

    return deposit


def build_deposit_for_index(initial_validator_count: int, index: int) -> Tuple[spec.Deposit, spec.BeaconState]:
    genesis_deposits = genesis.create_deposits(
        keys.pubkeys[:initial_validator_count],
        keys.withdrawal_creds[:initial_validator_count]
    )
    state = genesis.create_genesis_state(genesis_deposits)

    deposit_data_leaves = [spec.hash(dep.data.serialize()) for dep in genesis_deposits]

    deposit = build_deposit(
        state,
        deposit_data_leaves,
        keys.pubkeys[index],
        keys.withdrawal_creds[index],
        keys.privkeys[index],
        spec.MAX_DEPOSIT_AMOUNT,
    )

    state.latest_eth1_data.deposit_root = get_merkle_root(tuple(deposit_data_leaves))
    state.latest_eth1_data.deposit_count = len(deposit_data_leaves)

    return deposit, state
