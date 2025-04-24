import logging
from pathlib import Path
import pandas as pd
import re # Import the regular expression module

from nilearn import datasets
from nilearn.maskers import NiftiMapsMasker
# Assuming discovery_wm.utils are not strictly needed for this core task
# from discovery_wm.utils import get_all_subj_paths, get_path_config

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

def get_all_mni_contrast_files(output_lev1_mni_dir: Path) -> list[Path]:
    """
    Finds all fixed-effects contrast NIfTI files in the specified directory.

    Args:
        output_lev1_mni_dir: The base directory containing subject outputs.

    Returns:
        A list of Path objects pointing to the NIfTI files.
    """
    logging.info(f"Searching for NIfTI files in: {output_lev1_mni_dir}")
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

    return info

def parcellate_files(file_list: list[Path], masker: NiftiMapsMasker) -> pd.DataFrame:
    """
    Parcellates a list of NIfTI files using the provided masker and
    structures the output as Parcels (rows) x Maps (columns).

    Args:
        file_list: List of Path objects to NIfTI files.
        masker: An initialized NiftiMapsMasker object.

    Returns:
        A pandas DataFrame with Parcels as index and Maps as columns.
    """
    logging.info("Starting parcellation...")
    # Use masker.transform on the list of files
    # Result shape will be (n_files, atlas_dimension)
    parcellated_data = masker.transform(file_list)
    logging.info(f"Parcellation complete. Initial data shape: {parcellated_data.shape}")

    # Get information for column names and create them
    map_info = [parse_filename_info(f) for f in file_list]
    # Create column names like 'sub-s03_spatialTS_cue_switch_cost'
    column_names = [f"{info['subject']}_{info['task']}_{info['contrast']}" for info in map_info]

    # Create DataFrame with original shape (n_files, atlas_dimension)
    df_parcellated = pd.DataFrame(parcellated_data) # No column names yet, index is file order

    # Transpose the DataFrame: now (atlas_dimension, n_files)
    df_parcellated = df_parcellated.T

    # Assign the descriptive column names
    df_parcellated.columns = column_names

    # Add Parcel ID as an index or column
    df_parcellated.index.name = 'Parcel_ID'
    # If you prefer Parcel_ID as a regular column:
    # df_parcellated.insert(0, 'Parcel_ID', [f'Parcel_{i}' for i in range(df_parcellated.shape[0])])
    # df_parcellated = df_parcellated.reset_index(drop=True) # Reset numeric index if you added Parcel_ID column


    logging.info(f"DataFrame structured. Final shape: {df_parcellated.shape}")
    # print(df_parcellated.head()) # Optional: print head for verification
    return df_parcellated

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Parcellation Script (Refactored)")

    # Configuration
    atlas_dimension = 1024
    atlas_resolution_mm = 2
    output_lev1_mni_dir = Path("./output_lev1_mni")
    outdir = Path("./difumo_contrast_maps")
    output_filename = f"parcellated_difumo_{atlas_dimension}dim_maps_as_columns.tsv" # New filename to distinguish format
    output_filepath = outdir / output_filename

    # Ensure output directory exists
    output_filepath.parent.mkdir(parents=True, exist_ok=True)

    # == 1. Fetch Difumo atlas ==
    difumo_atlas = fetch_difumo_atlas(dimension=atlas_dimension, resolution_mm=atlas_resolution_mm)
    # No need to print the full atlas object, logging info is sufficient

    # == 2. Create Difumo Nifti Masker ==
    # Fit the masker to the atlas maps
    masker = NiftiMapsMasker(
        maps_img=difumo_atlas['maps'],
        standardize=False, # Keep original values
        memory='nilearn_cache', # Use caching
        memory_level=1,
        verbose=0, # Reduce verbosity during transform
        resampling_target='maps' # Resample input images to atlas space
    ).fit() # Fit the masker here

    # == 3. Get all nifti files ==
    mni_contrast_files = get_all_mni_contrast_files(output_lev1_mni_dir)

    if not mni_contrast_files:
        logging.warning("No MNI contrast files found. Exiting.")
        return

    # == 4. Parcellate files and structure DataFrame ==
    df_parcellated = parcellate_files(mni_contrast_files, masker)

    # == 5. Save the DataFrame to a TSV file ==
    # Use index=True if 'Parcel_ID' is the index name, index=False if it's a regular column
    df_parcellated.to_csv(output_filepath, sep='\t', index=True) # Assuming Parcel_ID is index

    logging.info(f"Parcellated data successfully saved to: {output_filepath.resolve()}")

if __name__ == "__main__":
    main()

# import logging
# from pathlib import Path
# import pandas as pd

# from nilearn import datasets
# from nilearn.maskers import NiftiMapsMasker
# from discovery_wm.utils import get_all_subj_paths, get_path_config

# def fetch_difumo_atlas(dimension: int, resolution_mm: int) -> None:
#     return datasets.fetch_atlas_difumo(dimension=dimension, resolution_mm=resolution_mm)

# def get_all_mni_contrast_files(output_lev1_mni_dir: Path) -> list[str]:
#     tag = "fixed-effects.nii.gz"
#     pattern = f"sub-*/*/fixed_effects/*{tag}"
#     return [str(p) for p in output_lev1_mni_dir.glob(pattern)]

# def main() -> None:
#     logging.basicConfig(level=logging.INFO)
#     logging.info("Starting Difumo script")
#     outdir = Path("./difumo_contrast_maps")

#     # == Fetch Difumo atlas ==
#     atlas_dimension = 128
#     atlas_resolution_mm = 2
#     difumo_atlas = fetch_difumo_atlas(dimension=atlas_dimension, resolution_mm=atlas_resolution_mm)
#     print(f'Difumo atlas: {difumo_atlas}')

#     # == Create Difumo Nifti Masker ==
#     masker = NiftiMapsMasker(
#         maps_img=difumo_atlas['maps'],
#         standardize=False,
#         memory='nilearn_cache',
#         memory_level=1,
#         verbose=1,
#         resampling_target='maps'
#     )

#     # == Get all nifti files ==
#     output_lev1_mni_dir = Path("./output_lev1_mni")
#     mni_contrast_files = get_all_mni_contrast_files(output_lev1_mni_dir)
#     print(f"Found {len(mni_contrast_files)} nifti files")

#     # == Parcellate all nifti files ==
#     parcellated_data_all = masker.fit_transform(mni_contrast_files)
#     # should be (n_files, atlas_dimension)
#     logging.info(f"Parcellation complete. Output data shape: {parcellated_data_all.shape}")

#     parcel_columns = [f'Parcel_{i}' for i in range(atlas_dimension)]
#     df_parcellated = pd.DataFrame(parcellated_data_all, columns=parcel_columns) 
#     print(df_parcellated.head())

#     # Add the input file names as the first column
#     df_parcellated.insert(0, 'InputFile', mni_contrast_files)

#     # Define the output file path
#     output_filename = f"parcellated_difumo_{atlas_dimension}dim.tsv"
#     output_filepath = outdir / output_filename
#     output_filepath.parent.mkdir(parents=True, exist_ok=True)

#     # Save the DataFrame to a TSV file
#     df_parcellated.to_csv(output_filepath, sep='\t', index=False) # Use tab separation, do not write row index

#     logging.info(f"Parcellated data successfully saved to: {output_filepath.resolve()}")


# if __name__ == "__main__":
#     main()