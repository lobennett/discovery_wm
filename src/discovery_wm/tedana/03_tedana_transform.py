import logging
import os
from pathlib import Path
import multiprocessing
from functools import partial
from concurrent.futures import ProcessPoolExecutor, as_completed
from nipype.interfaces.ants import ApplyTransforms
from discovery_wm.utils import get_path_config, get_parser, get_subj_id, get_ses_task_run
import gc
from tqdm import tqdm


def apply_xforms(scan, outpath, xforms, reference):
    if os.path.isfile(outpath):
        logging.warning(f"Skipping: {outpath} exists...")
        return outpath

    # Ensure output directory exists with error handling for race conditions
    output_dir = Path(outpath).parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        # Handle race condition where another process created the directory
        pass
    except OSError as e:
        logging.error(f"Failed to create output directory {output_dir}: {e}")
        raise

    logging.info(f'Applying transforms to {outpath}')
    at = ApplyTransforms()
    at.inputs.input_image = scan
    at.inputs.reference_image = reference
    at.inputs.output_image = outpath
    at.inputs.interpolation = "LanczosWindowedSinc"
    at.inputs.transforms = xforms
    at.inputs.input_image_type = 3
    at.run()
    logging.info(f'Finished applying transforms to {outpath}')
    return outpath


def collect_xforms(subj_fmriprep_dir, ses, task_name, run_number):
    """Collect transform files based on input parameters."""
    anat_dir = list(subj_fmriprep_dir.glob(f'ses-*/anat'))[0]
    func_dir = subj_fmriprep_dir / ses / "func"

    # Find transform files
    t1w_to_mni_xform = list(anat_dir.glob(f"*_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5"))[0]
    bold_to_t1w_xform = list(func_dir.glob(f"*{task_name}*{run_number}*from-bold*to-T1w_mode-image*xfm.txt"))[0]

    # Find reference images
    mni_reference = list(func_dir.glob(f"*{task_name}*{run_number}*space-MNI152NLin2009cAsym_res-2_boldref.nii.gz"))[0]
    t1w_reference = list(func_dir.glob(f"*{task_name}*{run_number}*space-T1w_boldref.nii.gz"))[0]

    return {
        "t1w_to_mni_xform": t1w_to_mni_xform,
        "bold_to_t1w_xform": bold_to_t1w_xform,
        "mni_reference": mni_reference,
        "t1w_reference": t1w_reference
    }


def create_transform_task(f, subj_id, subj_fmriprep_dir, outdir):
    """Create transform tasks for a single file"""
    ses, task_name, run_number = get_ses_task_run(f.parent)

    # Collect all necessary transforms and references
    try:
        xforms = collect_xforms(subj_fmriprep_dir, ses, task_name, run_number)
    except IndexError:
        logging.error(f"Could not find all necessary transform files for {ses} {task_name} {run_number}")
        return []

    # prepare outdirs
    outdir_full = outdir / ses / "func"
    outdir_full.mkdir(parents=True, exist_ok=True)

    # Create output paths for both spaces
    t1w_outpath = outdir_full / f"{subj_id}_{ses}_{task_name}_{run_number}_space-T1w_desc-optcom_bold.nii.gz"
    mni_outpath = outdir_full / f"{subj_id}_{ses}_{task_name}_{run_number}_space-MNI152NLin2009cAsym_res-2_desc-optcom_bold.nii.gz"

    # List of transform tasks to perform
    transform_tasks = [
        {
            'scan': str(f),
            'xforms': [str(xforms["bold_to_t1w_xform"])],
            'outpath': str(t1w_outpath),
            'reference': str(xforms["t1w_reference"]),
        },
        {
            'scan': str(f),
            'xforms': [str(xforms["t1w_to_mni_xform"]), str(xforms["bold_to_t1w_xform"])],
            'outpath': str(mni_outpath),
            'reference': str(xforms["mni_reference"]),
        }
    ]

    return transform_tasks


def apply_single_transform(task_args):
    """Wrapper function for applying a single transform - for parallel execution"""
    try:
        result = apply_xforms(**task_args)
        gc.collect()
        return result
    except Exception as e:
        logging.error(f"Error applying transform to {task_args['outpath']}: {str(e)}")
        return None


def main() -> None:
    # Configure logging to handle multiprocessing properly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # _, fmriprep_dir, _, tedana_denoised_dir, tedana_transformed_dir, _, _, = get_path_config()
    bids_dir = Path("/oak/stanford/groups/russpold/data/network_grant/validation_BIDS")
    fmriprep_dir = bids_dir / "derivatives" / "fmriprep-24.1.0rc2"
    tedana_denoised_dir = bids_dir / "derivatives" / "tedana_denoised"
    tedana_transformed_dir = bids_dir / "derivatives" / "tedana_transformed"

    # Parse the command line arguments
    parser = get_parser()
    subj_id = get_subj_id(parser)

    subj_fmriprep_dir = Path(fmriprep_dir / subj_id)
    subj_tedana_dir = Path(tedana_denoised_dir / subj_id)
    outdir = Path(tedana_transformed_dir / subj_id)
    outdir.mkdir(parents=True, exist_ok=True)

    # Get all files that need processing
    files_to_process = list(subj_tedana_dir.glob('**/*desc-optcom_bold.nii.gz'))
    logging.info(f"Found {len(files_to_process)} files to process")

    # Detect available CPUs from SLURM environment or use system default
    num_processes = min(int(os.environ.get('SLURM_CPUS_PER_TASK', multiprocessing.cpu_count())), 6)
    logging.info(f"Using {num_processes} workers")

    # Create all transform tasks
    all_tasks = []
    for f in files_to_process:
        tasks = create_transform_task(f, subj_id, subj_fmriprep_dir, outdir)
        all_tasks.extend(tasks)

    logging.info(f"Created {len(all_tasks)} transform tasks")

    # Process all tasks in parallel
    completed_tasks = 0
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit all tasks
        future_to_task = {executor.submit(apply_single_transform, task): task for task in all_tasks}
        
        # Process completed tasks with progress bar
        with tqdm(total=len(all_tasks), desc="Applying transforms") as pbar:
            for future in as_completed(future_to_task):
                result = future.result()
                completed_tasks += 1
                pbar.update(1)
                if result:
                    logging.debug(f"Completed task {completed_tasks}/{len(all_tasks)}: {result}")

    logging.info(f"All {completed_tasks} transformations completed")


if __name__ == "__main__":
    main()
