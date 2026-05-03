from z3 import And, Not, Or, deserialize

from policy_forge.formula import (
    Formula,
    V1,
    V2,
    V3,
    V4,
    all_formulas,
    check_equivalence,
)

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


def test_deserialized_vars_match_module_vars():
    """Deserialized variables should work with module-level V1..V4."""
    serialized = And(V1, V2).serialize()
    restored = deserialize(serialized)
    assert check_equivalence(And(restored, V3), And(V1, V2, V3))


def test_all_formulas_unique_names():
    formulas = all_formulas()
    names = [f.name for f in formulas]
    assert len(names) == len(set(names))


def test_canonical_pairs_equivalent():
    formulas = {f.name: f for f in all_formulas()}
    for name, f in formulas.items():
        if name.endswith("_canonical"):
            base = formulas[name[: -len("_canonical")]]
            assert check_equivalence(f.expr, base.expr), (
                f"{name} not equivalent to {base.name}"
            )
