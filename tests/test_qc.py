import anndata as ad
import numpy as np

from analysis.qc import (
    check_mitochondrial_genes,
    qc_and_filter,
)


def test_check_mitochondrial_genes():
    X = np.array(
        [
            [10, 20, 30],
            [5, 10, 15],
        ]
    )

    adata = ad.AnnData(X=X)
    adata.var_names = ["MT-ND1", "GeneA", "MT-CO1"]

    count = check_mitochondrial_genes(adata)

    assert count == 2
    assert "mt" in adata.var.columns
    assert adata.var["mt"].tolist() == [True, False, True]


def test_qc_and_filter():
    X = np.array(
        [
            # MT-Gene, GeneA, GeneB, GeneC, GeneD
            [10, 10, 10, 10, 0],  # Cell 1: good
            [1, 0, 0, 0, 0],  # Cell 2: too few genes
            [50, 1, 1, 1, 1],  # Cell 3: high mitochondrial %
            [10, 10, 10, 10, 0],  # Cell 4: good
        ]
    )
    adata = ad.AnnData(X=X)

    adata.obs_names = [
        "cell1",
        "cell2",
        "cell3",
        "cell4",
    ]

    adata.var_names = [
        "MT-Gene",
        "GeneA",
        "GeneB",
        "GeneC",
        "GeneD",
    ]

    result = qc_and_filter(
        adata,
        min_genes=2,
        max_genes=5,
        min_cells=1,
        max_pct_mt=50.0,
    )

    assert "cell1" in result.obs_names
    assert "cell4" in result.obs_names

    assert "cell2" not in result.obs_names
    assert "cell3" not in result.obs_names
