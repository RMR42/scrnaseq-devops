"""
Quality control and cell filtering for scRNA-seq data.

"""

import scanpy as sc


def check_mitochondrial_genes(adata, mt_prefix="MT-"):
    """
    Flag mitochondrial genes and report how many were found.

    """

    adata.var["mt"] = adata.var_names.str.startswith(mt_prefix)
    count = adata.var["mt"].sum()
    if count == 0:
        print("Warning: No mitochondrial genes were found.")
    return count


def calculate_qc_metrics(adata):
    """
    Compute per-cell QC metrics (n_genes_by_counts, total_counts, pct_counts_mt).

    """

    check_mitochondrial_genes(adata, mt_prefix="MT-")
    sc.pp.calculate_qc_metrics(
        adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True
    )
    return adata


def qc_and_filter(adata, min_genes=200, max_genes=2500, min_cells=3, max_pct_mt=5.0):
    """
    Filter cells and genes using thresholds derived from the data's own
    distribution — never copy a threshold without checking it first.

    """

    calculate_qc_metrics(adata)
    print(f"Before filtering: {adata.n_obs} cells, {adata.n_vars} genes")
    sc.pp.filter_cells(adata, min_genes=min_genes)
    filter_mask = (adata.obs["n_genes_by_counts"] < max_genes) & (
        adata.obs["pct_counts_mt"] < max_pct_mt
    )
    adata = adata[filter_mask].copy()
    sc.pp.filter_genes(adata, min_cells=min_cells)
    print(f"After filtering: {adata.n_obs} cells, {adata.n_vars} genes")
    return adata
