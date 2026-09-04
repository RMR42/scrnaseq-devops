from pathlib import Path

from analysis.pipeline import run_pipeline


def test_full_pipeline(tmp_path):
    """
    Integration test for the complete scRNA-seq analysis pipeline.

    Uses the small real PBMC3k-derived test dataset and verifies
    that the expected output files are produced.
    """

    input_file = Path("tests/data/pbmc3k_test.h5ad")

    output_file = tmp_path / "result.h5ad"
    plot_dir = tmp_path / "figures"

    run_pipeline(
        input_path=str(input_file),
        output_path=str(output_file),
        plot_dir=str(plot_dir),
    )

    # Main AnnData result
    assert output_file.exists()
    assert output_file.stat().st_size > 0

    # Marker genes
    marker_file = tmp_path / "markers.csv"
    assert marker_file.exists()
    assert marker_file.stat().st_size > 0

    # UMAP plot
    umap_file = plot_dir / "umap.png"
    assert umap_file.exists()
    assert umap_file.stat().st_size > 0
