from eth2spec.phase0 import spec
from typing import Tuple, Any, Callable
from eth_utils import to_dict
from eth2spec.debug.encode import encode

EdgeCaseExec = Callable[[spec.BeaconState, Any], spec.BeaconState]

# description (of the edge-case)
# type of the change-object being tested with
# pre (pre state to apply change to, becomes output state)
# change (object to be applied to pre state using executor)
# executor (applies the edge case to the state),
# does_error (if we expect the executor to throw an assertion-exception)
EdgeCaseDef = Tuple[str, Any, spec.BeaconState, Any, EdgeCaseExec, bool]


def expect_error(fn: Callable[[], spec.BeaconState]) -> None:
    try:
        fn()
    except AssertionError:
        return None
    raise Exception('processing function has unexpectedly not thrown an assertion error')


@to_dict
def gen_edge_case(edge_case: EdgeCaseDef):
    (description, typ, state, data, executor, does_error) = edge_case
    yield 'description', description
    yield 'pre', encode(state, spec.BeaconState)
    yield 'data', encode(data, typ)
    if does_error:
        expect_error(lambda: executor(state, data))
    else:
        executor(state, data)
    yield 'post', None if does_error else encode(state, spec.BeaconState)


def run_edge_case(edge_case: EdgeCaseDef):
    (description, typ, state, data, executor, does_error) = edge_case
    if does_error:
        expect_error(executor(state, data))
    else:
        executor(state, data)


def edge_case(description: str, typ: Any, runner: EdgeCaseExec, does_error=False):
    """
    Decorator to create edge-case definitions with
    :param description: description of the edge-case
    :param typ: type of the change-object being tested with
    :param runner: applies the edge case to the state
    :param does_error: if we expect the executor to throw an assertion-exception
    :return: wrapped setup function, which will produce an EdgeCaseDef if called
    """
    def edge_case_wrap(fn):
        def edge_case_entry(*args, **kw):
            state, change = fn(*args, **kw)
            return tuple((description, typ, state, change, runner, does_error))
        return edge_case_entry
    return edge_case_wrap

