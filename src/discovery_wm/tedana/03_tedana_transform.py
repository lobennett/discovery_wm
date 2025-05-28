import logging
import os
from pathlib import Path
import multiprocessing
from functools import partial
from nipype.interfaces.ants import ApplyTransforms
from discovery_wm.utils import get_path_config, get_parser, get_subj_id, get_ses_task_run
import gc


def apply_xforms(scan, outpath, xforms, reference):
    # if os.path.isfile(outpath):
    #     logging.warning(f"Skipping: {outpath} exists...")
    #     return

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


def process_file(f, subj_id, subj_fmriprep_dir, outdir):
    """Process a single file - this will be run in parallel"""
    ses, task_name, run_number = get_ses_task_run(f.parent)

    include = [('sub-s03', 'ses-09', 'task-rest'), ('sub-s03', 'ses-12', 'task-rest'), ('sub-s10', 'ses-02', 'task-shapeMatching'), ('sub-s10', 'ses-05', 'task-goNogo'), ('sub-s10', 'ses-05', 'task-rest'), ('sub-s10', 'ses-08', 'task-directedForgetting'), ('sub-s10', 'ses-08', 'task-spatialTS'), ('sub-s10', 'ses-11', 'task-directedForgettingWFlanker'), ('sub-s10', 'ses-12', 'task-rest'), ('sub-s19', 'ses-01', 'task-cuedTS'), ('sub-s19', 'ses-03', 'task-stopSignal'), ('sub-s19', 'ses-05', 'task-rest'), ('sub-s19', 'ses-10', 'task-rest'), ('sub-s19', 'ses-12', 'task-rest'), ('sub-s29', 'ses-06', 'task-goNogo'), ('sub-s29', 'ses-09', 'task-rest'), ('sub-s43', 'ses-09', 'task-shapeMatching'), ('sub-s43', 'ses-12', 'task-rest')]
    
    target = (subj_id, ses, task_name)
    print(target)

    if target not in include:
        logging.info(f"Skipping {f.name} - {ses} - {task_name} - {run_number}")
        return

    logging.info(f'Processing {f.name} - {ses} - {task_name} - {run_number}')

    # Collect all necessary transforms and references
    try:
        xforms = collect_xforms(subj_fmriprep_dir, ses, task_name, run_number)
    except IndexError:
        logging.error(f"Could not find all necessary transform files for {ses} {task_name} {run_number}")
        return

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

    # Apply transforms
    for task in transform_tasks:
        apply_xforms(**task)
        gc.collect()


def main() -> None:
    # Configure logging to handle multiprocessing properly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    _, fmriprep_dir, _, tedana_denoised_dir, tedana_transformed_dir, _, _, = get_path_config()

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

    print(files_to_process)

    # Set up the multiprocessing pool with 4 workers
    num_processes = 4
    logging.info(f"Starting multiprocessing pool with {num_processes} workers")

    # Create a partial function with fixed arguments
    process_func = partial(
        process_file,
        subj_id=subj_id,
        subj_fmriprep_dir=subj_fmriprep_dir,
        outdir=outdir
    )

    # Process files in parallel
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(process_func, files_to_process)

    logging.info("All transformations completed")


if __name__ == "__main__":
    main()

# import logging
# import os
# from pathlib import Path
# from nipype.interfaces.ants import ApplyTransforms
# from discovery_wm.utils import get_path_config, get_parser, get_subj_id, get_ses_task_run


# def apply_xforms(scan, outpath, xforms, reference):
#     at = ApplyTransforms()
#     at.inputs.input_image = scan
#     at.inputs.reference_image = reference
#     at.inputs.output_image = outpath
#     at.inputs.interpolation = "LanczosWindowedSinc"
#     at.inputs.transforms = xforms
#     at.inputs.input_image_type = 3
#     at.run()


# def collect_xforms(subj_fmriprep_dir, ses, task_name, run_number):
#     """Collect transform files based on input parameters."""
#     anat_dir = list(subj_fmriprep_dir.glob(f'ses-*/anat'))[0]
#     func_dir = subj_fmriprep_dir / ses / "func"

#     # Find transform files
#     t1w_to_mni_xform = list(anat_dir.glob(f"*_from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5"))[0]
#     bold_to_t1w_xform = list(func_dir.glob(f"*{task_name}*{run_number}*from-bold*to-T1w_mode-image*xfm.txt"))[0]

#     # Find reference images
#     mni_reference = list(func_dir.glob(f"*{task_name}*{run_number}*space-MNI152NLin2009cAsym_res-2_boldref.nii.gz"))[0]
#     t1w_reference = list(func_dir.glob(f"*{task_name}*{run_number}*space-T1w_boldref.nii.gz"))[0]

#     return {
#         "t1w_to_mni_xform": t1w_to_mni_xform,
#         "bold_to_t1w_xform": bold_to_t1w_xform,
#         "mni_reference": mni_reference,
#         "t1w_reference": t1w_reference
#     }


# def main() -> None:
#     logging.basicConfig(level=logging.INFO)

#     _, fmriprep_dir, _, tedana_denoised_dir, tedana_transformed_dir, _, _, = get_path_config()

#     # Parse the command line arguments
#     parser = get_parser()
#     subj_id = get_subj_id(parser)

#     subj_fmriprep_dir = Path(fmriprep_dir / subj_id)
#     subj_tedana_dir = Path(tedana_denoised_dir / subj_id)
#     outdir = Path(tedana_transformed_dir / subj_id)
#     outdir.mkdir(parents=True, exist_ok=True)

#     for f in subj_tedana_dir.glob('**/*desc-optcom_bold.nii.gz'):
#         ses, task_name, run_number = get_ses_task_run(f.parent)
#         logging.info(f'Processing {f.name} - {ses} - {task_name} - {run_number}')

#         # Collect all necessary transforms and references
#         try:
#             xforms = collect_xforms(subj_fmriprep_dir, ses, task_name, run_number)
#         except IndexError:
#             logging.error(f"Could not find all necessary transform files for {ses} {task_name} {run_number}")
#             continue

#         # prepare outdirs
#         outdir_full = outdir / ses / "func"
#         outdir_full.mkdir(parents=True, exist_ok=True)

#         # Create output paths for both spaces
#         t1w_outpath = outdir_full / f"{subj_id}_{ses}_{task_name}_{run_number}_space-T1w_desc-optcom_bold.nii.gz"
#         mni_outpath = outdir_full / f"{subj_id}_{ses}_{task_name}_{run_number}_space-MNI152NLin2009cAsym_res-2_desc-optcom_bold.nii.gz"

#         # Process T1w space transformation
#         if not os.path.isfile(t1w_outpath):
#             logging.info(f'Applying transforms to T1w space for {t1w_outpath}')
#             apply_xforms(
#                 scan=str(f),
#                 xforms=[str(xforms["bold_to_t1w_xform"])],
#                 outpath=str(t1w_outpath),
#                 reference=str(xforms["t1w_reference"]),
#             )
#             logging.info(f'Finished applying transforms to T1w space')
#         else:
#             logging.warning(f"Skipping: {t1w_outpath} exists...")

#         # Process MNI space transformation
#         if not os.path.isfile(mni_outpath):
#             logging.info(f'Applying transforms to MNI space for {mni_outpath}')
#             apply_xforms(
#                 scan=str(f),
#                 # NOTE: first bold->T1w, then T1w->MNI
#                 xforms=[str(xforms["t1w_to_mni_xform"]), str(xforms["bold_to_t1w_xform"])],
#                 outpath=str(mni_outpath),
#                 reference=str(xforms["mni_reference"]),
#             )
#             logging.info(f'Finished applying transforms to MNI space')
#         else:
#             logging.warning(f"Skipping: {mni_outpath} exists...")


# if __name__ == "__main__":
#     main()
