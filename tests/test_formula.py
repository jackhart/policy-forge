from z3 import And, Not, Or, deserialize

from policy_forge.formula import (
    A, B, C, D, Example, Formula, check_equivalence, formula_1,
)


def test_identical():
    assert check_equivalence(And(A, B), And(A, B))


def test_not_equivalent():
    assert not check_equivalence(And(A, B), Or(A, B))


def test_commutativity():
    assert check_equivalence(And(A, B), And(B, A))


def test_de_morgan():
    assert check_equivalence(Not(And(A, B)), Or(Not(A), Not(B)))


def test_formula_1_self():
    assert check_equivalence(formula_1.expr, And(A, B, Or(C, D)))


def test_formula_1_wrong():
    assert not check_equivalence(formula_1.expr, And(A, B, And(C, D)))


def test_formula_check_equivalence_method():
    assert formula_1.check_equivalence(And(A, B, Or(C, D)))
    assert not formula_1.check_equivalence(And(A, B, And(C, D)))


def test_formula_properties():
    assert formula_1.code == str(formula_1.expr)
    assert formula_1.logic == formula_1.expr.sexpr()
    assert formula_1.expected_results == [True, False, False]


def test_formula_frozen():
    import pytest
    with pytest.raises(AttributeError):
        formula_1.expr = And(A, B)


def test_formula_serialize_roundtrip():
    serialized = formula_1.serialize()
    restored = Formula.deserialize(serialized)
    assert check_equivalence(formula_1.expr, restored.expr)
    assert restored.expected_results == formula_1.expected_results
    assert len(restored.examples) == len(formula_1.examples)


def test_example_roundtrip():
    from dataclasses import asdict

    ex = Example(assignment={"A": True, "B": False}, result=True)
    d = asdict(ex)
    assert d == {"assignment": {"A": True, "B": False}, "result": True}
    restored = Example(**d)
    assert restored == ex


def test_z3_serialize_roundtrip():
    serialized = formula_1.expr.serialize()
    restored = deserialize(serialized)
    assert check_equivalence(formula_1.expr, restored)


def test_deserialized_vars_match_module_vars():
    """Deserialized variables should work with module-level A, B, C, D."""
    serialized = And(A, B).serialize()
    restored = deserialize(serialized)
    assert check_equivalence(And(restored, C), And(A, B, C))
