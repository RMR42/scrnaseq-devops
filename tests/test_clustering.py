import numpy as np
import anndata as ad

from analysis.clustering import (
    run_pca_and_neighbors,
    cluster,
    annotate_clusters,
)


def create_test_adata(n_cells=20, n_genes=10):
    """
    Create a small synthetic AnnData object for testing.
    """
    rng = np.random.default_rng(42)

    X = rng.poisson(
        lam=5,
        size=(n_cells, n_genes)
    ).astype(float)

    adata = ad.AnnData(X=X)

    adata.var_names = [
        f"Gene{i}"
        for i in range(n_genes)
    ]

    adata.obs_names = [
        f"Cell{i}"
        for i in range(n_cells)
    ]

    return adata


def test_run_pca_and_neighbors():
    adata = create_test_adata()

    result = run_pca_and_neighbors(
        adata,
        n_comps=5,
        n_pcs=5,
        n_neighbors=5,
    )

    # PCA results should exist.
    assert "X_pca" in result.obsm

    # PCA should contain the requested number of components.
    assert result.obsm["X_pca"].shape == (20, 5)

    # Neighbors graph should have been created.
    assert "connectivities" in result.obsp
    assert "distances" in result.obsp


def test_cluster():
    adata = create_test_adata()

    adata = run_pca_and_neighbors(
        adata,
        n_comps=5,
        n_pcs=5,
        n_neighbors=5,
    )

    result = cluster(
        adata,
        resolution=0.8,
    )

    # Leiden should create cluster labels.
    assert "leiden" in result.obs

    # Every cell should have a cluster assignment.
    assert result.obs["leiden"].notna().all()

    # At least one cluster should exist.
    assert result.obs["leiden"].nunique() >= 1


def test_annotate_clusters():
    adata = create_test_adata()

    adata.obs["leiden"] = [
        "0", "0", "0", "1", "1",
        "1", "0", "1", "0", "1",
        "0", "0", "1", "1", "0",
        "1", "0", "1", "0", "1",
    ]

    cluster_to_celltype = {
        "0": "T_cell",
        "1": "B_cell",
    }

    result = annotate_clusters(
        adata,
        cluster_to_celltype,
    )

    assert "cell_type" in result.obs

    assert result.obs["cell_type"].tolist() == [
        "T_cell", "T_cell", "T_cell", "B_cell", "B_cell",
        "B_cell", "T_cell", "B_cell", "T_cell", "B_cell",
        "T_cell", "T_cell", "B_cell", "B_cell", "T_cell",
        "B_cell", "T_cell", "B_cell", "T_cell", "B_cell",
    ]