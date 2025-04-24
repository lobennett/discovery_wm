from pathlib import Path
import pandas as pd
from sklearn.preprocessing import StandardScaler
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2.rinterface_lib.callbacks import logger as rpy2_logger
import numpy as np
import logging
import sys
import matplotlib.pyplot as plt

def scale_data(df: pd.DataFrame) -> pd.DataFrame:
    # Assuming your dataframe is called 'df'
    # 1. Save the Parcel_ID column
    parcel_ids = df['Parcel_ID'].copy()

    # 2. Scale only the feature columns (not the ID column)
    features = df.drop('Parcel_ID', axis=1)
    scaler = StandardScaler()
    scaled_features = pd.DataFrame(
        scaler.fit_transform(features),
        columns=features.columns
    )

    # 3. Add back the original Parcel_ID
    scaled_df = pd.concat(
        [parcel_ids.reset_index(drop=True),
        scaled_features.reset_index(drop=True)],
        axis=1)

    return scaled_df

def plot_fa_parallel(parallel_output_r, out_img_path, title_prefix):
    """
    Plots the results from the R psych::fa.parallel function.

    Args:
        parallel_output_r: R object (list) from psych::fa.parallel.
        out_img_path: Path to save the image.
        title_prefix: Prefix for the plot title.
    """
    fa_eigen = np.array(parallel_output_r[0])
    pc_eigen = np.array(parallel_output_r[1])
    fa_sim_eigen = np.array(parallel_output_r[4])
    pc_sim_eigen = np.array(parallel_output_r[2])

    recommended_factors = int(np.array(parallel_output_r[6])[0])
    recommended_components = int(np.array(parallel_output_r[7])[0])

    plt.figure(figsize=(10, 6))

    plt.plot(range(1, len(fa_eigen) + 1), fa_eigen, label='FA EVs', color='black', marker='o', linestyle='-', markersize=5)
    plt.plot(range(1, len(fa_sim_eigen) + 1), fa_sim_eigen, label='FA Sim EVs', color='black', marker='x', linestyle='--', markersize=5)

    plt.plot(range(1, len(pc_eigen) + 1), pc_eigen, label='PC EVs', color='red', marker='o', linestyle='-', markersize=5)
    plt.plot(range(1, len(pc_sim_eigen) + 1), pc_sim_eigen, label='PC Sim EVs', color='red', marker='x', linestyle='--', markersize=5)

    plt.axvline(x=recommended_factors, color='blue', linestyle=':', label=f'Rec FA: {recommended_factors}')
    plt.axvline(x=recommended_components, color='green', linestyle=':', label=f'Rec PC: {recommended_components}')
    plt.axhline(y=1, color='gray', linestyle='-', linewidth=0.8, label='Eigenvalue > 1')

    plt.xlabel('Number of Factors/Components')
    plt.ylabel('Eigenvalue')
    plt.title(f'{title_prefix}: Parallel Analysis Eigenvalues')
    plt.legend(loc='best')
    plt.grid(True)
    plt.figtext(0.95, 0.02, "Note: PC EVs is used in Scree plots eigen > 1", ha='right', fontsize=8, color='gray')
    plt.tight_layout()
    plt.savefig(out_img_path, bbox_inches='tight')
    plt.close()


def main() -> None:
    print("Running EFA...")
    out_dir = Path("./efa_results")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Configuration
    atlas_dimension = 1024
    # Use the new file name created by the refactored script
    input_filename = f"parcellated_difumo_{atlas_dimension}dim_maps_as_columns.tsv"
    input_file = Path("./difumo_contrast_maps") / input_filename

    df = pd.read_csv(input_file, sep="\t")
    efa_data = df.copy()
    n_parcels, n_maps = efa_data.shape
    print(f'Found {n_parcels} parcels and {n_maps} maps.')

    # Scale the data
    efa_data_scaled = scale_data(efa_data)
    print(efa_data_scaled.head())

    # Convert to R DataFrame
    rpy2_logger.setLevel(logging.ERROR)
    pandas2ri.activate()
    try:
        utils = importr('utils')
        base = importr('base')
        psych = importr('psych')
        logging.info("R and psych package loaded successfully.")
    except Exception as e:
        logging.error(f"Error setting up rpy2 or loading R packages: {e}")
        logging.error("Please ensure R is installed and 'psych' package is available.")
        sys.exit(1)

    r_df = pandas2ri.py2rpy(efa_data_scaled)
    print("Running parallel analysis to determine number of factors...")
    parallel_output_r = psych.fa_parallel(r_df, fm="ml", fa="both", n_iter=500, show_legend=True, plot=False)

    print("Plotting parallel analysis results...")
    analysis_label = "Overall Data"
    plot_fa_parallel(parallel_output_r, out_dir / "parallel_analysis_plot.png", title_prefix=analysis_label)
    recommended_factors_fa = int(np.array(parallel_output_r[6])[0])
    chosen_number_of_factors = recommended_factors_fa
    print(f"== Recommended number of factors: {chosen_number_of_factors} ==")

    # Print fit statistics
    fa_result_r = psych.fa(r_df, nfactors=chosen_number_of_factors, fm="ml", rotate="promax", scores="Bartlett")
    print_fit_stats(label="Overall Data", model_obj=fa_result_r)


if __name__ == "__main__":
    main()
