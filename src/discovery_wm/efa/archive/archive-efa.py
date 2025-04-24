import sys
import warnings
import os
import time
from glob import glob
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colorbar as mpl_colorbar # Needed for custom colorbar later
import seaborn as sns
# from nilearn.glm import compute_fixed_effects # Not needed for EFA itself
# from nilearn.glm.second_level import SecondLevelModel # Not needed for EFA itself
from nilearn import image, masking, plotting
from nilearn.datasets import fetch_atlas_difumo # Needed to reload atlas for spatial mapping
from nilearn.maskers import NiftiMapsMasker # Needed to reload masker for spatial mapping
# import warnings # Already imported
from pathlib import Path
# Ignore specific matplotlib warning if needed (from notebook)
from matplotlib import MatplotlibDeprecationWarning
warnings.filterwarnings("ignore", category=MatplotlibDeprecationWarning)

# --- rpy2 Setup and R Package Loading (from Notebook) ---
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2.rinterface_lib.callbacks import logger as rpy2_logger
import logging 

from sklearn.preprocessing import StandardScaler

# Suppress R output
rpy2_logger.setLevel(logging.ERROR)

# Activate automatic conversion for pandas DataFrames
pandas2ri.activate()

# Load necessary R libraries
try:
    utils = importr('utils')
    base = importr('base')
    # Set CRAN mirror and install packages silently (only needed first time)
    # In a production script, you might handle R package installation outside the main run
    # utils.chooseCRANmirror(ind=1) # Choose a mirror if needed
    # utils.install_packages('psych', quiet=True)
    # utils.install_packages('ggplot2', quiet=True)
    # utils.install_packages('paran', quiet=True) # psych installs paran

    # Import the installed libraries
    psych = importr('psych')
    # ggplot2 = importr('ggplot2') # Not directly used in the plotting functions here

    logging.info("R and psych package loaded successfully.")

except Exception as e:
    logging.error(f"Error setting up rpy2 or loading R packages: {e}")
    logging.error("Please ensure R is installed and 'psych' package is available.")
    sys.exit(1) # Exit if R setup fails


# --- Plotting Helper Functions (Adapted from Notebook) ---

def plot_loading_phi(fa_object_r, variable_names, out_img_path, title_prefix, out_type='phi', phi_plot_diag=True):
    """
    Plots heatmap for factor loadings or phi matrix from an R psych::fa object.

    Args:
        fa_object_r: R object returned by psych::fa accessed via rpy2.
        variable_names: List of original variable names (Map column names).
        out_img_path: Path to save the image.
        title_prefix: Prefix for the plot title (e.g., 'SubjectX' or 'Group').
        out_type: 'phi' or 'loadings'.
        phi_plot_diag: Whether to mask the diagonal and upper triangle for phi.
    """
    plt.figure(figsize=(10, 8))
    
    if out_type == 'phi':
        phi_matrix = np.array(fa_object_r.rx2('Phi'))
        n_factors = phi_matrix.shape[0]
        phi_df = pd.DataFrame(phi_matrix,
                              index=[f'Factor {i+1}' for i in range(n_factors)],
                              columns=[f'Factor {i+1}' for i in range(n_factors)])

        mask = np.triu(np.ones_like(phi_matrix, dtype=bool), k=0 if phi_plot_diag else 1)
        sns.heatmap(phi_df, annot=True, cmap='coolwarm',
                    mask=mask, # Mask upper triangle + diagonal if phi_plot_diag is True
                    vmin=-1, vmax=1, fmt='.2f', linewidths=0.25)
        plt.title(f"{title_prefix}: Phi Matrix", fontsize=12)
        plt.xlabel("Factors")
        plt.ylabel("Factors")

    elif out_type == 'loadings':
        factor_loadings_r = fa_object_r.rx2('loadings')
        # Convert R matrix to numpy array, then pandas DataFrame
        # Note: psych::fa loadings are often transposed relative to typical sklearn output
        # They are variables (rows) x factors (cols) which is what we want here
        factor_loadings = np.array(factor_loadings_r)
        n_factors = factor_loadings.shape[1]
        
        # Threshold loadings for display clarity
        threshold = 0.30
        factor_loadings_display = factor_loadings.copy()
        factor_loadings_display[np.abs(factor_loadings_display) < threshold] = np.nan

        df_loadings = pd.DataFrame(factor_loadings_display,
                                   index=variable_names, # Original map names are rows
                                   columns=[f'Factor {i+1}' for i in range(n_factors)])

        plt.figure(figsize=(12, max(8, n_factors * 0.5))) # Adjust figure size based on factors/variables
        sns.heatmap(df_loadings, annot=True, cmap='coolwarm', vmin=-1, vmax=1, fmt='.2f', linewidths=0.25)
        plt.title(f"{title_prefix}: EFA Loadings (Abs > {threshold:.2f})", fontsize=12)
        plt.xlabel("Factors", fontsize=10)
        plt.ylabel("Maps (Task_Contrast)", fontsize=10)
        plt.yticks(rotation=0) # Keep y-labels horizontal for readability

    else:
        raise ValueError("out_type must be 'phi' or 'loadings'")

    plt.tick_params(axis='both', labelsize=8)
    plt.tight_layout() # Adjust layout to prevent labels overlapping
    plt.savefig(out_img_path, bbox_inches='tight')
    plt.close() # Close plot to prevent it from displaying inline if not desired

def plot_fa_parallel(parallel_output_r, out_img_path, title_prefix):
    """
    Plots the results from the R psych::fa.parallel function.

    Args:
        parallel_output_r: R object (list) from psych::fa.parallel.
        out_img_path: Path to save the image.
        title_prefix: Prefix for the plot title.
    """
    # Convert R vectors to numpy arrays
    fa_eigen = np.array(parallel_output_r[0])
    pc_eigen = np.array(parallel_output_r[1])
    fa_sim_eigen = np.array(parallel_output_r[4]) # Correct index based on psych::fa.parallel output structure
    pc_sim_eigen = np.array(parallel_output_r[2]) # Correct index

    # Recommended numbers are elements 6 (FA) and 7 (PC)
    recommended_factors = int(np.array(parallel_output_r[6])[0])
    recommended_components = int(np.array(parallel_output_r[7])[0])

    plt.figure(figsize=(10, 6))

    # FA data eigen + sim eigen
    plt.plot(range(1, len(fa_eigen) + 1), fa_eigen, label='FA EVs', color='black', marker='o', linestyle='-', markersize=5)
    plt.plot(range(1, len(fa_sim_eigen) + 1), fa_sim_eigen, label='FA Sim EVs', color='black', marker='x', linestyle='--', markersize=5)

    # PC data eigen + sim eigen
    plt.plot(range(1, len(pc_eigen) + 1), pc_eigen, label='PC EVs', color='red', marker='o', linestyle='-', markersize=5)
    plt.plot(range(1, len(pc_sim_eigen) + 1), pc_sim_eigen, label='PC Sim EVs', color='red', marker='x', linestyle='--', markersize=5)

    # Recommended factors/components
    plt.axvline(x=recommended_factors, color='blue', linestyle=':', label=f'Rec FA: {recommended_factors}')
    plt.axvline(x=recommended_components, color='green', linestyle=':', label=f'Rec PC: {recommended_components}')
    plt.axhline(y=1, color='gray', linestyle='-', linewidth=0.8, label='Eigenvalue > 1') # Add Kaiser criterion line

    plt.xlabel('Number of Factors/Components')
    plt.ylabel('Eigenvalue')
    plt.title(f'{title_prefix}: Parallel Analysis Eigenvalues')
    plt.legend(loc='best')
    plt.grid(True)
    plt.figtext(0.95, 0.02, "Note: PC EVs is used in Scree plots eigen > 1", ha='right', fontsize=8, color='gray')
    plt.tight_layout()
    plt.savefig(out_img_path, bbox_inches='tight')
    plt.close() # Close plot


# --- Main EFA Logic ---

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Refactored EFA Script (Aligning with Notebook)")

    out_dir = Path("./efa_results")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Configuration
    atlas_dimension = 1024
    # Use the new file name created by the refactored script
    input_filename = f"parcellated_difumo_{atlas_dimension}dim_maps_as_columns.tsv"
    input_file = Path("./difumo_contrast_maps") / input_filename

    # --- 1. Read the input file ---
    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        logging.error("Please run the parcellation script to generate this file.")
        sys.exit(1)

    logging.info(f"Reading input file: {input_file}")
    # Read the TSV, setting the first column ('Parcel_ID') as the index
    try:
        df = pd.read_csv(input_file, sep='\t', index_col=0)
        logging.info(f"Input data shape: {df.shape} (Parcels x Maps)")
        # print(df.head()) # Optional: print head for verification
    except Exception as e:
        logging.error(f"Error reading input file {input_file}: {e}")
        sys.exit(1)

    # Data for EFA are all columns (the maps), rows are parcels
    data_for_efa = df.copy() # Use a copy to avoid modifying the original df index
    map_names = data_for_efa.columns.tolist()
    n_parcels, n_maps = data_for_efa.shape

    if n_parcels < n_maps:
        logging.warning(f"Number of observations (Parcels: {n_parcels}) is less than number of variables (Maps: {n_maps}). EFA results might be unstable.")
    if n_parcels < 50: # Rule of thumb: N > 100-200, or N:p ratio > 5:1 or 10:1
         logging.warning(f"Low number of observations (Parcels: {n_parcels}). Consider if EFA is appropriate.")

    # --- 2. Scale the data ---
    # StandardScaler scales columns (variables). Since Maps are columns, this is correct.
    logging.info("Scaling data (Maps as variables)...")
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data_for_efa)
    scaled_df = pd.DataFrame(scaled_data, index=data_for_efa.index, columns=data_for_efa.columns)
    logging.info("Data scaling complete.")
    # print(scaled_df.head())

    # --- 3. Convert data to R DataFrame for psych package ---
    logging.info("Converting data to R DataFrame...")
    try:
        r_df = pandas2ri.py2rpy(scaled_df)
        logging.info("Conversion to R DataFrame complete.")
    except Exception as e:
        logging.error(f"Error converting pandas DataFrame to R DataFrame: {e}")
        logging.error("Ensure rpy2 is correctly configured and can communicate with R.")
        sys.exit(1)

    # --- 4. Determine Number of Factors using Parallel Analysis (psych::fa.parallel) ---
    logging.info("Running Parallel Analysis to determine number of factors...")
    parallel_output_r = None
    try:
        # fm="ml" (Maximum Likelihood), fa="both" (FA and PC), n_iter (simulations)
        parallel_output_r = psych.fa_parallel(r_df, fm="ml", fa="both", n_iter=500, show_legend=True, plot=False) # plot=False, we'll plot manually
        logging.info("Parallel Analysis complete.")

        # Plot Parallel Analysis results
        plot_fa_parallel(parallel_output_r, out_dir / "parallel_analysis_plot.png", title_prefix="Data")

        # Recommended number of factors by FA (index 6) and Components by PC (index 7)
        # Note: psych::fa.parallel output is a list/vector in R
        recommended_factors_fa = int(np.array(parallel_output_r[6])[0])
        recommended_factors_pc = int(np.array(parallel_output_r[7])[0])

        logging.info(f"Parallel Analysis Recommendations:")
        logging.info(f"  Number of factors (FA): {recommended_factors_fa}")
        logging.info(f"  Number of components (PC): {recommended_factors_pc}")
        logging.info("Consider these recommendations and domain knowledge to choose the final number of factors.")

        # Choose number of factors (example: use FA recommendation)
        chosen_number_of_factors = recommended_factors_fa
        if chosen_number_of_factors == 0:
             logging.warning("Parallel analysis recommended 0 factors. EFA might not be appropriate.")
             # Decide how to handle this - e.g., set a minimum number, or exit
             # For demonstration, let's set a minimum if needed, or just log and proceed with 0 (which psych::fa handles)
             # chosen_number_of_factors = max(recommended_factors_fa, 1) # Example: ensure at least 1 factor


    except Exception as e:
        logging.error(f"Error during Parallel Analysis: {e}")
        logging.error("Ensure R and the 'psych' package are installed and accessible via rpy2.")
        sys.exit(1)

    if chosen_number_of_factors <= 0:
         logging.warning("Chosen number of factors is 0 or less. Skipping EFA.")
         return


    # --- 5. Run EFA using psych::fa ---
    logging.info(f"Running EFA with {chosen_number_of_factors} factors and Promax rotation...")
    fa_result_r = None
    try:
        # fm="ml" (Maximum Likelihood), rotate="promax" (Oblique rotation)
        # scores="Bartlett" or "Thurstone" (Methods to estimate factor scores)
        fa_result_r = psych.fa(r_df, nfactors=chosen_number_of_factors, fm="ml", rotate="promax", scores="Bartlett")
        logging.info("EFA complete.")

        # Print fit statistics
        print_fit_stats(label="Overall Data", model_obj=fa_result_r)

    except Exception as e:
        logging.error(f"Error during EFA using psych::fa: {e}")
        logging.error("Check chosen number of factors and data suitability.")
        sys.exit(1)

    # --- 6. Extract Results and Convert Back to Pandas ---
    logging.info("Extracting results from R FA object...")
    try:
        # Loadings (variables x factors)
        loadings_np = np.array(fa_result_r.rx2('loadings'))
        loadings_df = pd.DataFrame(loadings_np,
                                   index=map_names, # Rows are the original map names
                                   columns=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)])
        loadings_df.index.name = 'Map'


        # Phi (factor correlations)
        phi_np = np.array(fa_result_r.rx2('Phi'))
        phi_df = pd.DataFrame(phi_np,
                              index=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)],
                              columns=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)])


        # Factor Scores (observations x factors)
        scores_np = np.array(fa_result_r.rx2('scores'))
        scores_df = pd.DataFrame(scores_np,
                                 index=df.index, # Rows are the original Parcel IDs
                                 columns=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)])
        scores_df.index.name = 'Parcel_ID'

        logging.info("Results extracted and converted.")

    except Exception as e:
        logging.error(f"Error extracting results from R FA object: {e}")
        sys.exit(1)

    # --- 7. Save and Plot Results ---

    # Save Loadings
    loadings_df.to_csv(out_dir / "factor_loadings_maps_on_factors.tsv", sep='\t')
    logging.info(f"Factor loadings (Maps on Factors) saved to: {out_dir / 'factor_loadings_maps_on_factors.tsv'}")
    # Plot Loadings Heatmap
    plot_loading_phi(fa_result_r, map_names, out_dir / "factor_loadings_heatmap.png", title_prefix="Data", out_type='loadings')


    # Save Phi matrix
    phi_df.to_csv(out_dir / "factor_phi_matrix.tsv", sep='\t')
    logging.info(f"Phi matrix saved to: {out_dir / 'factor_phi_matrix.tsv'}")
    # Plot Phi Heatmap
    plot_loading_phi(fa_result_r, None, out_dir / "factor_phi_heatmap.png", title_prefix="Data", out_type='phi')


    # Save Factor Scores
    scores_df.to_csv(out_dir / "factor_scores_parcels_on_factors.tsv", sep='\t')
    logging.info(f"Factor scores (Parcels on Factors) saved to: {out_dir / 'factor_scores_parcels_on_factors.tsv'}")


    # --- 8. Spatial Mapping of Factor Scores (Parcels on Factors) ---
    logging.info("Mapping factor scores back to brain space...")

    # Need to reload the atlas and masker used during parcellation
    try:
        # Assuming the same atlas dimension and resolution were used
        atlas_dimension_mapping = atlas_dimension # Use the same dimension
        atlas_resolution_mm_mapping = 2 # Use the same resolution (adjust if needed)
        difumo_atlas_mapping = fetch_difumo_atlas(dimension=atlas_dimension_mapping, resolution_mm=atlas_resolution_mm_mapping)

        masker_mapping = NiftiMapsMasker(
            maps_img=difumo_atlas_mapping['maps'],
            standardize=False, # Keep original values for mapping
            memory='nilearn_cache',
            memory_level=1,
            verbose=0,
            resampling_target='maps'
        ).fit() # Fit the masker

        # Inverse transform each factor score column
        spatial_maps_dir = out_dir / "spatial_factor_maps"
        spatial_maps_dir.mkdir(parents=True, exist_ok=True)

        for factor_col in scores_df.columns:
            # Get the scores for the current factor (as a pandas Series)
            factor_scores_series = scores_df[factor_col]

            # Ensure scores are in the order of the masker's components
            # The scores_df index (Parcel_ID) should match the order of parcels in the atlas/masker
            # If df.index matches difumo_atlas['labels'], order should be correct
            # NiftiMapsMasker.inverse_transform expects a (n_components,) shape or (n_samples, n_components)
            # Here we have (n_parcels,), representing scores for each parcel
            try:
                # inverse_transform expects shape (n_components,) or (n_samples, n_components)
                # Here n_components is n_parcels. We have scores for each parcel.
                # Need to ensure the scores are passed as a 1D array of shape (n_parcels,)
                factor_scores_array_1d = factor_scores_series.values # .values converts pandas Series to numpy array

                # Inverse transform the scores
                factor_map_img = masker_mapping.inverse_transform(factor_scores_array_1d)

                # Save the resulting NIfTI image
                output_map_path = spatial_maps_dir / f"{factor_col}_spatial_map.nii.gz"
                factor_map_img.to_filename(output_map_path)
                logging.info(f"Saved spatial map for {factor_col} to: {output_map_path.resolve()}")

                # Optional: Display or plot a slice of the map
                # if factor_col == 'Factor_1': # Just plot the first factor as an example
                #     plotting.plot_stat_map(factor_map_img, title=f"Spatial Map: {factor_col}")
                #     plt.show() # Requires displaying plots

            except Exception as e:
                 logging.error(f"Error mapping {factor_col} back to brain space: {e}")


    except Exception as e:
        logging.error(f"Error during setup for spatial mapping: {e}")
        logging.error("Ensure nilearn, the atlas, and masker are correctly configured.")


    logging.info("EFA script finished.")

# Helper function to print fit stats (from notebook)
def print_fit_stats(label: str, model_obj: robjects.ListVector):
    """
    Summarizes key metrics (RMSEA, CFI, BIC) from an R psych::fa object.

    Args:
        label: Label for the analysis (e.g., 'Group').
        model_obj: An R object returned by psych::fa accessed via rpy2.
    """
    try:
        # extract/round to 2 dec
        rmsea = model_obj.rx2('RMSEA')
        # RMSEA is typically a vector/list in R with value, lower bound, upper bound, P value
        rmsea_values = f"RMSEA: {np.array(rmsea)[0]:.3f} (lower: {np.array(rmsea)[1]:.3f}, upper: {np.array(rmsea)[2]:.3f})"
        cfi = model_obj.rx2('CFI')
        cfi_value = f"CFI: {np.array(cfi)[0]:.3f}"
        # BIC is also often a vector/list, take the first element
        bic = model_obj.rx2('BIC')
        bic_value = f"BIC: {np.array(bic)[0]:.3f}"

        logging.info(f"\nAnalysis: * {label} * \n\t Global Fit Statistics: \n \t {rmsea_values} \n \t {cfi_value} & {bic_value}")

    except Exception as e:
        logging.error(f"Error extracting or printing fit statistics for {label}: {e}")
        logging.info("Fit statistics might not be available or structure is different.")


if __name__ == "__main__":
    main()


# import pandas as pd
# import logging
# from pathlib import Path
# from factor_analyzer import calculate_bartlett_sphericity, calculate_kmo
# from sklearn.preprocessing import StandardScaler
# from factor_analyzer import FactorAnalyzer
# import matplotlib.pyplot as plt
# import numpy as np

# def main() -> None:
#     out_dir = Path("./efa_results")
#     out_dir.mkdir(parents=True, exist_ok=True)
#     logging.basicConfig(level=logging.INFO)
#     logging.info("Starting EFA script")
#     dimension = 128
#     input_file = Path(f"./difumo_contrast_maps/parcellated_difumo_{dimension}dim.tsv")
#     print(input_file)

#     # Read the input file
#     df = pd.read_csv(input_file, sep='\t')
#     print(df.head())

#     input_files = df['InputFile']
#     parcel_data = df.filter(regex='^Parcel_')
#     n_files, n_parcels = parcel_data.shape

#     if n_files < n_parcels:
#          logging.warning(f"Number of observations ({n_files}) is less than number of variables ({n_parcels}). EFA results might be unstable.")
#     if n_files < 50:
#          logging.warning(f"Low number of observations ({n_files}). Consider if EFA is appropriate.")
    
#     logging.info("Checking data suitability for EFA...")

#     # Bartlett's Test of Sphericity
#     # H0: Correlation matrix is an identity matrix (variables are uncorrelated)
#     # We want to REJECT H0 (p < 0.05) for EFA to be suitable.
#     try:
#         chi_square_value, p_value = calculate_bartlett_sphericity(parcel_data)
#         print(chi_square_value, p_value)
#         logging.info(f"Bartlett's Test: Chi-Square = {chi_square_value:.3f}, p-value = {p_value:.3e}")
#         if p_value > 0.05:
#             logging.warning("Bartlett's test is non-significant (p > 0.05). Variables may be uncorrelated; EFA might not be suitable.")
#         else:
#              logging.info("Bartlett's test is significant (p < 0.05), indicating suitability for EFA.")
#     except Exception as e:
#         logging.error(f"Error calculating Bartlett's test: {e}")

#     # Scale the data
#     scaler = StandardScaler()
#     scaled_parcel_data = scaler.fit_transform(parcel_data)

#     # --- Determine Number of Factors (Add this section) ---
#     # Calculate eigenvalues for scree plot
#     fa_initial = FactorAnalyzer(rotation=None, n_factors=parcel_data.shape[1]) # Fit with max possible factors
#     fa_initial.fit(scaled_parcel_data)
#     eigenvalues, commonalities = fa_initial.get_eigenvalues()

#     # Plot scree plot (using matplotlib, which you imported)
#     plt.figure(figsize=(10, 6))
#     plt.plot(range(1, len(eigenvalues) + 1), eigenvalues, marker='o')
#     plt.axhline(y=1, color='r', linestyle='--') # Kaiser criterion
#     plt.title('Scree Plot')
#     plt.xlabel('Factor Number')
#     plt.ylabel('Eigenvalue')
#     plt.grid(True)
#     plt.savefig(out_dir / "scree_plot.png")

#     logging.info(f"Eigenvalues: {eigenvalues}")

#     # Based on the scree plot and Kaiser criterion (eigenvalues > 1),
#     # choose the number of factors (let's say you decide on k factors)
#     # You need to decide 'k' based on your plot/analysis
#     # For example, if the 5th eigenvalue is > 1 but the 6th is not, k=5.
#     # Let's assume k = chosen_number_of_factors (you'll need to set this)
#     chosen_number_of_factors = sum(eigenvalues > 1) # Example using Kaiser criterion

#     if chosen_number_of_factors == 0:
#         logging.warning("No factors with eigenvalues > 1. EFA might not be appropriate.")
#         # Decide how to handle this - maybe stop or choose a small number based on theory

#     logging.info(f"Chosen number of factors (based on Kaiser criterion): {chosen_number_of_factors}")

#     # --- Run EFA with Chosen Number of Factors ---
#     if chosen_number_of_factors > 0:
#         # Choose a rotation method (Varimax is common for orthogonal rotation)
#         fa_final = FactorAnalyzer(n_factors=chosen_number_of_factors, rotation='varimax')
#         fa_final.fit(scaled_parcel_data)

#         logging.info("EFA run complete.")

#         # --- Get Factor Loadings (Optional but Good for Interpretation) ---
#         loadings = pd.DataFrame(fa_final.loadings_, index=parcel_data.columns, columns=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)])
#         loadings.to_csv(out_dir / "factor_loadings.tsv", sep='\t')
#         logging.info(f"Factor loadings saved to {out_dir / 'factor_loadings.tsv'}")
#         print("Factor Loadings:")
#         print(loadings) # Display loadings to interpret what each factor represents

#         # --- Get Factor Scores (This is key for your goal) ---
#         # The get_scores() method returns the factor scores for each observation
#         factor_scores = pd.DataFrame(fa_final.transform(scaled_parcel_data),
#                                     index=input_files,
#                                     columns=[f'Factor_{i+1}' for i in range(chosen_number_of_factors)])

#         # Save the factor scores
#         factor_scores.to_csv(out_dir / "factor_scores.tsv", sep='\t')
#         logging.info(f"Factor scores saved to {out_dir / 'factor_scores.tsv'}")

#         print("\nFactor Scores:")
#         print(factor_scores.head())

#         # --- Analyze Factor Scores to see which Input Files "Hang Together" ---
#         logging.info("Analyzing factor scores to identify groups of input files...")

#         # Method 1: Look at files with high scores on the same factor
#         for i in range(chosen_number_of_factors):
#             factor_col = f'Factor_{i+1}'
#             # You can define a threshold for "high score", e.g., > 1 standard deviation
#             # Or simply sort to see the highest loading files
#             sorted_files = factor_scores.sort_values(by=factor_col, ascending=False)
#             logging.info(f"\nInput files with highest scores on {factor_col}:")
#             print(sorted_files[factor_col].head()) # Print top files for this factor

#         # Method 2: Perform Clustering on Factor Scores
#         # You could use clustering algorithms (like K-Means, Agglomerative Clustering)
#         # from sklearn.cluster on the 'factor_scores' DataFrame to group files
#         # based on their overall profile across all factors.
#         # Example (requires importing KMeans from sklearn.cluster):
#         # from sklearn.cluster import KMeans
#         # n_clusters = 3 # You'd need to decide how many clusters to look for
#         # kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10) # Add n_init explicitly
#         # clusters = kmeans.fit_predict(factor_scores)
#         # clustered_files = pd.DataFrame({'InputFile': factor_scores.index, 'Cluster': clusters})
#         # clustered_files.to_csv(out_dir / "clustered_files_by_factor_scores.tsv", sep='\t')
#         # logging.info(f"\nInput files clustered by factor scores saved to {out_dir / 'clustered_files_by_factor_scores.tsv'}")
#         # print(clustered_files.head())


#     else:
#         logging.warning("EFA was not performed as no factors met the eigenvalue criterion.")


# if __name__ == "__main__":
#     main()