# ---
# jupyter:
#   jupytext:
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 2026-05-04 experiment
#
# Recomputes the pool and sampling tables in the README from `population.json` and `formulas.json`.

# %%
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

EXPERIMENT_DIR = Path(".")
population = json.loads((EXPERIMENT_DIR / "population.json").read_text())["formulas"]
formulas = json.loads((EXPERIMENT_DIR / "formulas.json").read_text())["formulas"]

pool_df = pd.DataFrame(population)
pool_df["symmetry_partition"] = pool_df["symmetry_partition"].apply(tuple)
sample_df = pd.DataFrame(formulas)
sample_df["symmetry_partition"] = sample_df["symmetry_partition"].apply(tuple)

print(f"Pool: {len(pool_df)} functions, sampled: {len(sample_df)}")


# %% [markdown]
# ## Pool counts by symmetry class

# %%
def format_partition_shapes(s):
    counts = s.value_counts()
    fmt = lambda p: str(p).replace(", ", ",")
    if len(counts) == 1:
        return fmt(counts.index[0])
    return ", ".join(f"{fmt(p)}={c}" for p, c in counts.items())


pool_df.groupby("symmetry_classes").agg(
    count=("name", "size"),
    partition_shapes=("symmetry_partition", format_partition_shapes),
    distinct_variance=("influence_variance", "nunique"),
)

# %% [markdown]
# ## Influence variance per symmetry class

# %%
pool_df.groupby("symmetry_classes")["influence_variance"].agg(
    ["min", "max", "mean", "nunique"]
).round(3)

# %% [markdown]
# ## Sampling budget

# %%
pd.DataFrame(
    {
        "Pool": pool_df.groupby("symmetry_classes").size(),
        "Budget": sample_df.groupby("symmetry_classes").size(),
    }
)

# %% [markdown]
# ## Realised allocation: samples per (symmetry class, variance level)

# %%
allocation = sample_df.groupby(["influence_variance", "symmetry_classes"]).size().unstack(fill_value=0)
allocation.columns = [f"sym={c}" for c in allocation.columns]
allocation.index = [
    f"{Decimal(str(v)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP):.3f}"
    for v in allocation.index
]
allocation.loc["Total"] = allocation.sum()
allocation

# %% [markdown]
# ## Per-sample DataFrame from results
#
# `perm` mirrors the run's `verified` flag (perm equivalence achieved within the 3-attempt
# retry budget). `perm_and_semantic` requires the judge's `semantic_match` to also be true.
# `exact` is any attempt achieving strict equivalence (`formula_ok_strict`).

# %%
results = json.loads((EXPERIMENT_DIR / "results-unrealistic.json").read_text())["results"]

rows = []
for r in results:
    attempts = r.get("attempts", [])
    judgement = r.get("judgement") or {}
    rows.append(
        {
            "sample_id": r["sample_id"],
            "formula": r["sample_id"].rsplit("_", 1)[0],
            "symmetry_classes": r["symmetry_classes"],
            "influence_variance": r["influence_variance"],
            "n_attempts": len(attempts),
            "perm": r["verified"],
            "perm_and_semantic": r["verified"] and bool(judgement.get("semantic_match")),
        }
    )

results_df = pd.DataFrame(rows)
print(f"{len(results_df)} samples")


def metrics(df):
    return pd.Series(
        {
            "n": len(df),
            "mean_attempts": round(df["n_attempts"].mean(), 2),
            "retry_rate": round((df["n_attempts"] > 1).mean(), 3),
            "fail_rate": round((~df["perm"]).mean(), 3),
            "perm_and_semantic": round(df["perm_and_semantic"].mean(), 3),
        }
    )


# %% [markdown]
# ### Overall

# %%
pd.DataFrame([metrics(results_df)], index=["all"])

# %% [markdown]
# ### By symmetry class

# %%
results_df.groupby("symmetry_classes")[["n_attempts", "perm", "perm_and_semantic"]].apply(metrics)

# %% [markdown]
# ### By influence variance

# %%
by_variance = results_df.groupby("influence_variance")[["n_attempts", "perm", "perm_and_semantic"]].apply(metrics)
by_variance.index = [
    f"{Decimal(str(v)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP):.3f}"
    for v in by_variance.index
]
by_variance

# %% [markdown]
# ### n_attempts distribution

# %%
results_df["n_attempts"].value_counts().sort_index().to_frame("samples")

# %% [markdown]
# ### Per-formula: only formulas that ever failed or retried
#
# Sorted by fail_rate then retry_rate. Formulas that always succeeded on the first try are omitted.

# %%
per_formula = results_df.groupby("formula")[["n_attempts", "perm", "perm_and_semantic"]].apply(metrics)
per_formula[(per_formula["fail_rate"] > 0) | (per_formula["retry_rate"] > 0)].sort_values(
    ["fail_rate", "retry_rate"], ascending=False
)

# %% [markdown]
# ## Judge fault classifications
#
# One row per judgement attempt (so a retried sample contributes multiple rows).

# %%
attempt_rows = []
for r in results:
    judgement = r.get("judgement") or {}
    for i, att in enumerate(judgement.get("attempts", [])):
        attempt_rows.append(
            {
                "sample_id": r["sample_id"],
                "formula": r["sample_id"].rsplit("_", 1)[0],
                "symmetry_classes": r["symmetry_classes"],
                "influence_variance": r["influence_variance"],
                "attempt_idx": i,
                "fault": att.get("fault"),
                "fault_type": att.get("fault_type"),
            }
        )

attempts_df = pd.DataFrame(attempt_rows)
print(f"{len(attempts_df)} judgement attempts total")

# %% [markdown]
# ### Overall fault distribution (all attempts)

# %%
attempts_df["fault"].value_counts(dropna=False).to_frame("count")

# %% [markdown]
# ### Non-neither attempts only

# %%
faulty = attempts_df[attempts_df["fault"] != "neither"]
print(f"{len(faulty)} non-neither attempts")
faulty["fault"].value_counts().to_frame("count")

# %% [markdown]
# ### Fault by symmetry class (non-neither attempts)

# %%
pd.crosstab(faulty["symmetry_classes"], faulty["fault"], margins=True, margins_name="Total")

# %% [markdown]
# ### Fault by influence variance (non-neither attempts)

# %%
crosstab_var = pd.crosstab(
    faulty["influence_variance"], faulty["fault"], margins=True, margins_name="Total"
)
crosstab_var.index = [
    f"{Decimal(str(v)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP):.3f}"
    if isinstance(v, float)
    else v
    for v in crosstab_var.index
]
crosstab_var

# %% [markdown]
# ### Fault types (more granular than fault)

# %%
faulty["fault_type"].value_counts().to_frame("count")
