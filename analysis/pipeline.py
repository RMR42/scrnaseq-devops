"""
Full pipeline: raw AnnData in -> annotated, clustered AnnData out.

Usage:
    python analysis/pipeline.py --input path/to/raw.h5ad --output path/to/result.h5ad
"""

import argparse
import json
import logging
import scanpy as sc
import os

from qc import qc_and_filter
from normalize import normalize, select_highly_variable_genes
from clustering import run_pca_and_neighbors, cluster, rank_marker_genes, annotate_clusters,save_marker_genes,save_plots


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def run_pipeline(input_path, output_path, cluster_file=None,marker_file=None,plot_dir="figures"):

    # Load the data
    logger.info(f"Loading data from: {input_path}")
    adata = sc.read_h5ad(input_path)
    logger.info(f"Loaded data: {adata.n_obs} cells, {adata.n_vars} genes")

    # QC
    logger.info("Starting quality control")
    adata = qc_and_filter(adata,min_genes=200,min_cells=3,max_pct_mt=5.0)
    logger.info(
        f"QC complete: {adata.n_obs} cells, {adata.n_vars} genes"
    )

    # Normalize
    logger.info("Starting normalization")
    adata = normalize(adata, target_sum=1e4)
    logger.info("Normalization complete")

    # Select HVGs
    logger.info("Selecting highly variable genes")
    adata = select_highly_variable_genes(adata,n_top_genes=2000)
    logger.info(
        f"HVG selection complete: {adata.n_vars} genes retained"
    )

    # PCA + neighbors
    logger.info("Running PCA and computing neighbors")
    adata = run_pca_and_neighbors(adata,n_pcs=15,n_neighbors=10)
    logger.info("PCA and neighbor graph complete")

    # Cluster
    logger.info("Clustering cells")
    adata = cluster(adata, resolution=0.8)
    logger.info(
        f"Clustering complete: "
        f"{adata.obs['leiden'].nunique()} clusters found"
    )

    # Rank marker genes
    logger.info("Ranking marker genes")
    adata = rank_marker_genes(adata,groupby="leiden",method="wilcoxon")
    logger.info("Marker gene ranking complete")

    logger.info("Saving marker genes")

    output_dir = os.path.dirname(output_path)
    marker_path = os.path.join(output_dir, "markers.csv")

    save_marker_genes(adata, marker_path, n_genes=20)

    logger.info(f"Marker genes saved to: {marker_path}")

    cluster_to_celltype = None

    if cluster_file:
        logger.info(f"Loading cluster annotation mapping from: {cluster_file}")

        with open(cluster_file, "r") as f:
            cluster_to_celltype = json.load(f)

    marker_genes = None

    if marker_file:

        logger.info(
            f"Loading marker genes from: {marker_file}"
        )

        with open(marker_file, "r") as f:
            marker_genes = json.load(f)

    # Optional annotation
    if cluster_to_celltype:
        logger.info("Annotating clusters")
        adata = annotate_clusters(adata,cluster_to_celltype,cluster_key="leiden")
        logger.info("Cluster annotation complete")
    else:
        logger.info("No cluster annotation mapping provided; skipping annotation")

    logger.info("Saving plots")

    save_plots(adata,plot_dir,marker_genes)

    logger.info(
        f"Plots saved to: {plot_dir}"
    )

    # Save
    logger.info(f"Saving final AnnData object to: {output_path}")
    adata.write(output_path)
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full scRNA-seq analysis pipeline")
    parser.add_argument("--input", required=True, help="Path to raw .h5ad file")
    parser.add_argument("--output", required=True, help="Path to save the processed .h5ad")
    parser.add_argument("--clusters",required=False,help="JSON file containing cluster-to-cell-type mapping")
    parser.add_argument("--markers",required=False,help="JSON file containing marker genes for dot plot")
    parser.add_argument("--plot-dir",default="figures",help="Directory to save plots")
    args = parser.parse_args()

    run_pipeline(args.input, args.output, args.clusters, args.markers, args.plot_dir)
