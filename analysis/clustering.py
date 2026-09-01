"""
Dimensionality reduction, clustering, and cell-type annotation.

"""

import scanpy as sc


def run_pca_and_neighbors(adata, n_comps=50, n_pcs=15, n_neighbors=10, max_value=10):
    """
    Scale, run PCA, and build the neighbors graph.

    """
    sc.pp.scale(adata, max_value=max_value)
    sc.tl.pca(adata, n_comps=n_comps,svd_solver='arpack')
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs)
    return adata



def cluster(adata, resolution=0.8):
    """
    Leiden clustering.

    """

    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=resolution)
    return adata


def annotate_clusters(adata, cluster_to_celltype, cluster_key="leiden"):
    """
    Map numeric cluster labels to real cell-type names.

    """
    adata.obs['cell_type']=adata.obs[cluster_key].map(cluster_to_celltype)
    return adata


def rank_marker_genes(adata, groupby="leiden", method="wilcoxon"):
    """
    Differential expression per cluster (one-vs-rest).

    """
    sc.tl.rank_genes_groups(adata, groupby=groupby, method=method)
    return adata

def save_marker_genes(adata, output_path, n_genes=20):
    """
    Save top marker genes for each cluster to a CSV file.
    """

    import pandas as pd

    result = adata.uns["rank_genes_groups"]

    clusters = result["names"].dtype.names

    rows = []

    for cluster in clusters:
        for rank in range(n_genes):
            rows.append({
                "cluster": cluster,
                "rank": rank + 1,
                "gene": result["names"][cluster][rank]
            })

    markers = pd.DataFrame(rows)
    markers.to_csv(output_path, index=False)

def save_plots(adata, output_dir, marker_genes=None):
    """
    Save UMAP and dot plot figures.

    Marker genes are checked against both the HVG-filtered AnnData
    object and adata.raw.
    """

    import os
    import matplotlib.pyplot as plt
    import scanpy as sc

    os.makedirs(output_dir, exist_ok=True)

    # -------------------------
    # UMAP
    # -------------------------
    sc.pl.umap(
        adata,
        color="leiden",
        show=False
    )

    plt.savefig(
        os.path.join(output_dir, "umap.png"),
        bbox_inches="tight"
    )

    plt.close()

    # -------------------------
    # Dot plot
    # -------------------------
    if marker_genes:

        # Flatten marker dictionary into one gene list
        genes = []

        for gene_list in marker_genes.values():
            genes.extend(gene_list)

        # Remove duplicates while preserving order
        genes = list(dict.fromkeys(genes))

        available_in_adata = []
        available_in_raw = []
        missing_genes = []

        for gene in genes:

            if gene in adata.var_names:
                available_in_adata.append(gene)

            elif adata.raw is not None and gene in adata.raw.var_names:
                available_in_raw.append(gene)

            else:
                missing_genes.append(gene)

        print(f"Total marker genes requested: {len(genes)}")
        print(f"Available in HVG data: {len(available_in_adata)}")
        print(f"Available only in adata.raw: {len(available_in_raw)}")
        print(f"Actually missing: {len(missing_genes)}")

        if missing_genes:
            print("Missing genes:")
            print(missing_genes)

        genes_to_plot = available_in_adata + available_in_raw

        if not genes_to_plot:
            print("Error: No marker genes are available for dot plot.")
            return

        sc.pl.dotplot(
            adata,
            var_names=genes_to_plot,
            groupby="leiden",
            show=False
        )

        plt.savefig(
            os.path.join(output_dir, "dotplot.png"),
            bbox_inches="tight"
        )

        plt.close()
