import logging
from pathlib import Path
import pandas as pd
import re

from nilearn import datasets, plotting
from nilearn.maskers import NiftiMapsMasker
from factor_analyzer import FactorAnalyzer
from factor_analyzer.factor_analyzer import calculate_bartlett_sphericity
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

def fetch_difumo_atlas(dimension: int, resolution_mm: int):
    """
    Fetches the DiFuMo functional atlas.

    Args:
        dimension: The dimensionality of the atlas (e.g., 128).
        resolution_mm: The resolution in millimeters (e.g., 2).

    Returns:
        The fetched atlas object.
    """
    logging.info(f"Fetching DiFuMo atlas (dimension={dimension}, resolution={resolution_mm}mm)")
    return datasets.fetch_atlas_difumo(dimension=dimension, resolution_mm=resolution_mm)

def create_contrast_matrix(nifti_files: list[Path], masker: NiftiMapsMasker) -> pd.DataFrame:
    """
    Creates a contrast matrix from a list of NIfTI files.
    """
    column_names = []
    for f in nifti_files:
        info = parse_filename_info(f)
        column_names.append(info['column_name'])

    matrix = pd.DataFrame(columns=column_names)
    data_for_columns = {}

    for f in nifti_files:
        print(f"Processing {f.name}")
        o = masker.transform(f)
        info = parse_filename_info(f)
        data_for_columns[info['column_name']] = o.flatten()

    for col_name, data in data_for_columns.items():
        matrix[col_name] = data

    return matrix

def get_all_mni_contrast_files(output_lev1_mni_dir: Path) -> list[Path]:
    """
    Finds all fixed-effects contrast NIfTI files in the specified directory.

    Args:
        output_lev1_mni_dir: The base directory containing subject outputs.

    Returns:
        A list of Path objects pointing to the NIfTI files.
    """
    logging.info(f"Searching for NIFTI files in: {output_lev1_mni_dir}")
    tag = "fixed-effects.nii.gz"
    pattern = f"sub-*/*/fixed_effects/*{tag}"
    files = list(output_lev1_mni_dir.glob(pattern))

    # Sort files by subject ID numerically
    def get_subject_number(filepath: Path) -> int:
        match = re.search(r'sub-s?(\d+)', str(filepath))
        return int(match.group(1)) if match else float('inf')

    files.sort(key=get_subject_number)
    logging.info(f"Found {len(files)} nifti files matching pattern '{pattern}'")
    return files

def parse_filename_info(filepath: Path) -> dict:
    """
    Parses the filename to extract Subject, Task, and Contrast information.

    Assumes filename format like:
    .../sub-sXX/task/fixed_effects/sub-sXX_task-YYY_contrast-ZZZ_..._stat-fixed-effects.nii.gz

    Args:
        filepath: The Path object for the NIfTI file.

    Returns:
        A dictionary containing 'subject', 'task', and 'contrast'.
    """
    filename = filepath.name
    info = {}

    # Extract subject (sub-sXX)
    sub_match = re.search(r'(sub-[a-zA-Z0-9]+)', filename)
    info['subject'] = sub_match.group(1) if sub_match else 'unknown_subject'

    # Extract task (task-YYY)
    task_match = re.search(r'task-([a-zA-Z0-9]+)', filename)
    info['task'] = task_match.group(1) if task_match else 'unknown_task'

    # Extract contrast (contrast-ZZZ)
    # This regex looks for 'contrast-' followed by anything up to '_rtmodel'
    # or up to '_stat' if '_rtmodel' is not present.
    contrast_match = re.search(r'contrast-(.+?)_(?:rtmodel|stat)', filename)
    info['contrast'] = contrast_match.group(1) if contrast_match else 'unknown_contrast'

    info['column_name'] = f'{info["subject"]}_{info["task"]}_{info["contrast"]}'

    return info

def _HornParallelAnalysis(data, K=10, printEigenvalues=False, outdir: Path = "./efa_analysis"):
    ################
    # Create a random matrix to match the dataset
    ################
    n, m = data.shape
    # Set the factor analysis parameters
    fa = FactorAnalyzer(n_factors=1, method="minres", rotation=None, use_smc=True)
    # Create arrays to store the values
    sumComponentEigens = np.empty(m)
    sumFactorEigens = np.empty(m)
    # Run the fit 'K' times over a random matrix
    for runNum in range(0, K):
        fa.fit(np.random.normal(size=(n, m)))
        sumComponentEigens = sumComponentEigens + fa.get_eigenvalues()[0]
        sumFactorEigens = sumFactorEigens + fa.get_eigenvalues()[1]
    # Average over the number of runs
    avgComponentEigens = sumComponentEigens / K
    avgFactorEigens = sumFactorEigens / K

    ################
    # Get the eigenvalues for the fit on supplied data
    ################
    fa.fit(data)
    dataEv = fa.get_eigenvalues()
    # Set up a scree plot
    plt.figure(figsize=(12, 10))

    ################
    ### Print results
    ################
    if printEigenvalues:
        print(
            "Principal component eigenvalues for random matrix:\n", avgComponentEigens
        )
        print("Factor eigenvalues for random matrix:\n", avgFactorEigens)
        print("Principal component eigenvalues for data:\n", dataEv[0])
        print("Factor eigenvalues for data:\n", dataEv[1])

    # Find the suggested stopping points
    suggestedFactors = sum((dataEv[1] - avgFactorEigens) > 0)
    suggestedComponents = sum((dataEv[0] - avgComponentEigens) > 0)
    print(
        "Parallel analysis suggests that the number of factors = ",
        suggestedFactors,
        " and the number of components = ",
        suggestedComponents,
    )

    ################
    ### Plot the eigenvalues against the number of variables
    ################
    # Line for eigenvalue 1
    plt.plot([0, m + 1], [1, 1], "k--", alpha=0.3)
    # For the random data - Components
    plt.plot(range(1, m + 1), avgComponentEigens, "b", label="PC - random", alpha=0.4)
    # For the Data - Components
    plt.scatter(range(1, m + 1), dataEv[0], c="b", marker="o")
    plt.plot(range(1, m + 1), dataEv[0], "b", label="PC - data")
    # For the random data - Factors
    plt.plot(range(1, m + 1), avgFactorEigens, "g", label="FA - random", alpha=0.4)
    # For the Data - Factors
    plt.scatter(range(1, m + 1), dataEv[1], c="g", marker="o")
    plt.plot(range(1, m + 1), dataEv[1], "g", label="FA - data")
    plt.title("Parallel Analysis Scree Plots", {"fontsize": 20})
    plt.xlabel("Factors/Components", {"fontsize": 15})
    plt.xticks(ticks=range(1, m + 1), labels=range(1, m + 1))
    plt.ylabel("Eigenvalue", {"fontsize": 15})
    plt.legend()
    # plt.show()
    plt.savefig(outdir / "parallel_analysis.png")

    return suggestedFactors

def create_and_save_difumo_matrix(output_lev1_mni_dir: Path, difumo_atlas: NiftiMapsMasker):
    """Get loadings if loadings tsv does not exist.
    """
    masker = NiftiMapsMasker(
        maps_img=difumo_atlas["maps"],
        memory="nilearn_cache",
        n_jobs=2,
        memory_level=1,
    ).fit()
    nifti_files = get_all_mni_contrast_files(output_lev1_mni_dir)
    matrix = create_contrast_matrix(nifti_files, masker)
    return matrix

def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # == SETTING UP PATHS == 
    # - Directories 
    output_lev1_mni_dir = Path("./output_lev1_mni")
    outdir = Path("./efa_results")
    outdir.mkdir(parents=True, exist_ok=True)

    # == DIFUMO ATLAS SETUP ==
    atlas_dimension, atlas_resolution_mm = 64, 2

    # - Files
    output_difumo_matrix = outdir / f"parcellated_difumo_{atlas_dimension}.tsv"

    # - Fetch atlas
    difumo_atlas = fetch_difumo_atlas(dimension=atlas_dimension, resolution_mm=atlas_resolution_mm)

    if output_difumo_matrix.exists():
        matrix = pd.read_csv(output_difumo_matrix, sep='\t')
    else:
        matrix = create_and_save_difumo_matrix(output_lev1_mni_dir, difumo_atlas)
        matrix.to_csv(output_difumo_matrix, sep='\t')

    # Run parallel analysis to determine number of factors
    logging.info("Running parallel analysis...")
    suggested_factors = _HornParallelAnalysis(matrix, K=10000, printEigenvalues=True, outdir=outdir)
    logging.info(f'Parallel analysis suggested {suggested_factors} factors')

    # Run EFA model with suggested number of factors
    suggested_factors = 7 
    logging.info(f"Running EFA model with {suggested_factors} factors...")
    fa_final = FactorAnalyzer(
        n_factors=suggested_factors,
        rotation="promax",
    )
    fa_final.fit(matrix)

    # Get the factor loadings
    loadings = fa_final.loadings_
    loadings_df = pd.DataFrame(
        loadings,
        index=matrix.columns,
        columns=[f'Factor{i+1}' for i in range(suggested_factors)]
    )

    # Save factor loadings to files
    output_fa_loadings = outdir / f"loadings-atlDim-{atlas_dimension}_atlRes-{atlas_resolution_mm}mm_nFactors-{suggested_factors}.tsv"
    loadings_df.to_csv(output_fa_loadings, sep='\t')
    logging.info(f"Saved loadings to {output_fa_loadings}")

    # Create and save heatmap of factor loadings
    logging.info(f'Loadings df shape: {loadings_df.shape}, columns: {loadings_df.columns}')
    for subj_id in ['s03', 's10', 's19', 's29', 's43']:
        plt.figure(figsize=(20, 10))
        # Create plot for each subject's loadings.
        subset = loadings_df.index.str.startswith(f'sub-{subj_id}')
        subset_df = loadings_df[subset]
        sns.heatmap(subset_df, annot=False, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f')
        plt.title(f"EFA Loadings ({suggested_factors} Factors)")
        plt.tight_layout()
        outpath = outdir / f'sub-{subj_id}' / f"efa_loadings_heatmap_{suggested_factors}factors_sub-{subj_id}.png"
        outpath.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(outpath)
        plt.close()


if __name__ == "__main__":
    main()
