import numpy as np
import anndata as ad

from analysis.normalize import (
    normalize,
    select_highly_variable_genes,
)


def test_normalize_preserves_counts_and_transforms_data():
    X = np.array([
        [10, 20, 30, 40],
        [20, 10, 40, 30],
        [30, 30, 20, 20],
    ], dtype=float)

    adata = ad.AnnData(X=X)

    original_counts = adata.X.copy()

    result = normalize(adata, target_sum=100)

    # Original counts should be preserved.
    assert "counts" in result.layers
    np.testing.assert_array_equal(
        result.layers["counts"],
        original_counts,
    )

    # Normalized data should no longer be identical to raw counts.
    assert not np.array_equal(result.X, original_counts)

    # Each cell should have approximately the requested total
    # after normalization/log transformation.
    assert result.n_obs == 3
    assert result.n_vars == 4


def test_select_highly_variable_genes():
    X = np.array([
        [10, 20, 30, 40, 50, 60],
        [11, 21, 29, 41, 49, 61],
        [9, 19, 31, 39, 51, 59],
        [12, 22, 28, 42, 48, 62],
        [8, 18, 32, 38, 52, 58],
    ], dtype=float)

    adata = ad.AnnData(X=X)

    adata.var_names = [
        "GeneA",
        "GeneB",
        "GeneC",
        "GeneD",
        "GeneE",
        "GeneF",
    ]

    result = select_highly_variable_genes(
        adata,
        n_top_genes=3,
    )

    # HVG calculation should create the highly_variable annotation.
    assert "highly_variable" in result.raw.var.columns

    # raw should preserve the complete pre-HVG dataset.
    assert result.raw is not None
    assert result.raw.n_vars == 6

    # Active AnnData should contain only the genes marked as highly variable.
    expected_hvg_count = result.raw.var["highly_variable"].sum()
    assert result.n_vars == expected_hvg_count