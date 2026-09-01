import scanpy as sc
import numpy as np

INPUT = "/home/ranjana/results_scrnaseq/scanpy_analysis/pbmc3k_raw.h5ad"
OUTPUT = "tests/data/pbmc3k_test.h5ad"

N_CELLS = 100
N_GENES = 3000

print(f"Loading {INPUT}")
adata = sc.read_h5ad(INPUT)

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
if hasattr(adata.X, "toarray"):
    total_counts = np.asarray(adata.X.sum(axis=0)).ravel()
else:
    total_counts = np.asarray(adata.X.sum(axis=0)).ravel()

non_mt_indices = np.where(~mt_mask)[0]

n_non_mt = N_GENES - int(mt_mask.sum())

selected_non_mt = non_mt_indices[
    np.argsort(total_counts[non_mt_indices])[-n_non_mt:]
]

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
