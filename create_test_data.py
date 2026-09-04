"""
One-off generator for the small PBMC3k-derived test fixture in
tests/data/pbmc3k_test.h5ad. Not part of the pipeline itself — you only
need to re-run this if you want to regenerate that fixture from a fresh
raw PBMC3k download.

Usage:
    python create_test_data.py --input /path/to/pbmc3k_raw.h5ad
"""

import argparse

import numpy as np
import scanpy as sc

OUTPUT = "tests/data/pbmc3k_test.h5ad"

N_CELLS = 100
N_GENES = 3000

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--input",
    required=True,
    help="Path to a raw PBMC3k .h5ad file (e.g. from the 10x Genomics PBMC3k dataset)",
)
args = parser.parse_args()

print(f"Loading {args.input}")
adata = sc.read_h5ad(args.input)

# --------------------------------------------------
# 1. Select a deterministic set of real PBMC3k cells
# --------------------------------------------------
adata = adata[:N_CELLS].copy()

# --------------------------------------------------
# 2. Identify mitochondrial genes
# --------------------------------------------------
mt_mask = adata.var_names.str.startswith("MT-")

# --------------------------------------------------
# 3. Select the most expressed non-mitochondrial genes
# --------------------------------------------------
total_counts = np.asarray(adata.X.sum(axis=0)).ravel()

non_mt_indices = np.where(~mt_mask)[0]

n_non_mt = N_GENES - int(mt_mask.sum())

selected_non_mt = non_mt_indices[np.argsort(total_counts[non_mt_indices])[-n_non_mt:]]

selected_mask = np.zeros(adata.n_vars, dtype=bool)

selected_mask[selected_non_mt] = True
selected_mask[mt_mask] = True

adata = adata[:, selected_mask].copy()

print(f"Created fixture: {adata.n_obs} cells × {adata.n_vars} genes")
print(f"Mitochondrial genes retained: {mt_mask.sum()}")

# --------------------------------------------------
# 4. Save
# --------------------------------------------------
adata.write_h5ad(OUTPUT)

print(f"Saved to: {OUTPUT}")
