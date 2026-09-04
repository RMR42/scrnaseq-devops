"""
Normalization and highly-variable-gene selection.

"""

import scanpy as sc


def normalize(adata, target_sum=1e4):
    """
    Log-normalize the data.

    """
    adata.layers["counts"] = adata.X.copy()
    sc.pp.normalize_total(adata, target_sum=target_sum)
    sc.pp.log1p(adata)
    return adata


def select_highly_variable_genes(adata, n_top_genes=2000):
    """
    Select the most informative genes for clustering, WITHOUT losing
    canonical marker genes that don't make the cutoff.

    """
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top_genes)
    adata.raw = adata
    adata = adata[:, adata.var["highly_variable"]].copy()
    return adata
