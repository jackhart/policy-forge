from z3 import And, Bools, Not, Or, deserialize

from policy_forge.formula import (
    Formula,
    check_equivalence,
    check_equivalence_up_to_permutation,
)

V1, V2, V3, V4 = Bools("V1 V2 V3 V4")

sample = Formula(expr=And(Or(V1, V2), Or(V3, V4)), name="sample")


def test_identical():
    assert check_equivalence(And(V1, V2), And(V1, V2))


def test_not_equivalent():
    assert not check_equivalence(And(V1, V2), Or(V1, V2))


def test_commutativity():
    assert check_equivalence(And(V1, V2), And(V2, V1))


def test_de_morgan():
    assert check_equivalence(Not(And(V1, V2)), Or(Not(V1), Not(V2)))


def test_formula_check_equivalence_method():
    assert sample.check_equivalence(And(Or(V1, V2), Or(V3, V4)))
    assert not sample.check_equivalence(And(V1, V2, V3, V4))


def test_formula_properties():
    assert sample.code == str(sample.expr)
    assert sample.logic == sample.expr.sexpr()


def test_formula_frozen():
    import pytest
    with pytest.raises(AttributeError):
        sample.expr = And(V1, V2)


def test_formula_serialize_roundtrip():
    serialized = sample.serialize()
    restored = Formula.deserialize(serialized)
    assert check_equivalence(sample.expr, restored.expr)


def test_z3_serialize_roundtrip():
    serialized = sample.expr.serialize()
    restored = deserialize(serialized)
    assert check_equivalence(sample.expr, restored)


def test_deserialized_vars_interop_with_local_vars():
    """Deserialized variables interchange with separately-constructed Bools of the same name."""
    serialized = And(V1, V2).serialize()
    restored = deserialize(serialized)
    assert check_equivalence(And(restored, V3), And(V1, V2, V3))


def test_perm_equivalence_strict_match():
    assert check_equivalence_up_to_permutation(And(V1, V2), And(V1, V2))


def test_perm_equivalence_under_relabeling():
    # Original Or(And(Not(V1), Not(V4)), V2, V3) vs candidate that
    # renamed V4 -> V2, V2 -> V3, V3 -> V4. Permutation (1, 3, 4, 2)
    # makes them equivalent.
    original = Or(And(Not(V1), Not(V4)), V2, V3)
    candidate = Or(And(Not(V1), Not(V2)), V3, V4)
    assert check_equivalence_up_to_permutation(original, candidate)


def test_perm_equivalence_genuinely_different():
    # No permutation of V1..V4 turns And into Or.
    assert not check_equivalence_up_to_permutation(
        And(V1, V2, V3, V4), Or(V1, V2, V3, V4)
    )


def test_perm_equivalence_different_atom_sets():
    # V3 missing on the right, V4 missing on the left.
    assert not check_equivalence_up_to_permutation(And(V1, V2, V3), And(V1, V2, V4))


def test_formula_perm_equivalence_method():
    f = Formula(expr=Or(And(Not(V1), Not(V4)), V2, V3))
    assert f.check_equivalence_up_to_permutation(Or(And(Not(V1), Not(V2)), V3, V4))
    assert not f.check_equivalence_up_to_permutation(And(V1, V2, V3, V4))


