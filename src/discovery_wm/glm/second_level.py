import logging
import re
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nb
import numpy as np
import pandas as pd
from nilearn import plotting
from nilearn.glm import threshold_stats_img
from nilearn.glm.second_level import SecondLevelModel
from templateflow import api as tf

from discovery_wm.utils import extract_contrast_name, get_parser


def get_contrast_paths_by_subject_and_contrast_name(base_dir: str, task_name: str = None, contrast_name: str = None) -> dict:
    """
    Takes in the directory of the first level contrast maps in MNI space,
    and returns a dictionary of the contrast maps by each subject for each contrast.
    If task_name is provided, only returns maps for that task.
    If contrast_name is provided, only returns maps for that contrast.
    """
    contrast_maps = {}
    for subj in base_dir.glob('sub-s*'):
        contrast_maps[subj.name] = {}
        
        # Build glob pattern based on provided args
        glob_pattern = '*/indiv_contrasts/*effect-size.nii.gz'
        if task_name is not None:
            glob_pattern = f'{task_name}/indiv_contrasts/*effect-size.nii.gz'
        if contrast_name is not None:
            glob_pattern = f'*/indiv_contrasts/*contrast-{contrast_name}_*effect-size.nii.gz'
            
        for task_contrast in subj.glob(glob_pattern):
            cname = extract_contrast_name(task_contrast)
            current_task_name = task_contrast.parent.parent.name
            key = f'{current_task_name}_{cname}'
            if key not in contrast_maps[subj.name]:
                contrast_maps[subj.name][key] = []
            contrast_maps[subj.name][key].append(task_contrast)
    return contrast_maps

def sort_by_session_order(contrast_maps: dict) -> dict:
    """
    Sorts the contrast maps by session order.
    """
    for subj in contrast_maps:
        for cname in contrast_maps[subj]:
            # Extract session number from filename to use as sorting key
            # This ensures that the contrast maps are sorted in the correct
            # order: from first session to last session.
            contrast_maps[subj][cname] = sorted(
                contrast_maps[subj][cname],
                key=lambda x: int(re.search(r'ses-(\d+)', str(x)).group(1))
            )

    return contrast_maps

def sort_by_encounter_number(contrast_maps: dict) -> dict:
    """
    Organizes the contrast maps by the order in which they
    were encountered by the subjects. Clusters contrasts across
    subjects, used for 2.5-level analysis.
    """
    maps_by_encounter_number = {}
    for subj in contrast_maps:
        for cname in contrast_maps[subj]:
            if cname not in maps_by_encounter_number:
                maps_by_encounter_number[cname] = {}
            for idx, cmap in enumerate(contrast_maps[subj][cname]):
                if idx not in maps_by_encounter_number[cname]:
                    maps_by_encounter_number[cname][idx] = []
                maps_by_encounter_number[cname][idx].append((cmap, subj))

    # Assert all contrasts have exactly 5 maps
    for cname in maps_by_encounter_number:
        count = len(maps_by_encounter_number[cname])
        assert count == 5, (
            f"Contrast {cname} has {count} maps, expected 5"
        )

    return maps_by_encounter_number

def plot_stat_map(
    stat_map: nb.Nifti1Image,
    threshold: float,
    cname: str,
    idx: int,
    outdir: Path,
    template: nb.Nifti1Image,
    title: str = None,
    cut_coords: tuple = (-10, 0, 10, 20, 30, 40, 50, 60, 70)
):
    """
    Plots the statistical map.
    """
    fig = plt.figure(figsize=(12, 3))
    plotting.plot_stat_map(
        stat_map,
        threshold=threshold,
        display_mode='z',
        cut_coords=cut_coords,
        title=title,
        figure=fig,
        draw_cross=False,
        annotate=True,
        bg_img=template,
        cmap='coolwarm',
    )
    outpath = outdir / cname / f'{cname}_encounter-{idx+1}_threshold-{threshold:.2f}.png'
    outpath.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outpath)
    logging.info(f"Saved plot to {outpath}")
    plt.close()

def main():
    logging.basicConfig(level=logging.INFO)

    parser = get_parser()
    args = parser.parse_args()

    # == PATHS ==
    outdir = Path('output_lev2_mni')
    oak = Path('/oak/stanford/groups/russpold/data/')
    bids_dir = oak / 'network_grant' / 'discovery_BIDS_20250402'
    output_lev1_mni = bids_dir / 'derivatives' / 'output_lev1_mni'

    # == GET CONTRAST MAPS ==
    contrast_maps = get_contrast_paths_by_subject_and_contrast_name(output_lev1_mni, args.task_name, args.contrast_name)
    contrast_maps_sorted = sort_by_session_order(contrast_maps)
    contrast_maps_by_encounter_number = sort_by_encounter_number(contrast_maps_sorted)

    # == THRESHOLDS ==
    liberal_threshold = 1.0
    alpha = 0.05

    # == MNI TEMPLATE FOR BACKGROUND IMG ==
    template=tf.get('MNI152NLin2009cAsym', resolution=2, suffix="T1w", desc="brain")

    logging.info("Starting execution of second level GLMs")
    # == LOOP THROUGH ALL CONTRASTS AND RUN SECOND LEVEL MODEL ==
    for cname in contrast_maps_by_encounter_number:
        for idx in contrast_maps_by_encounter_number[cname]:
            # == CREATE DESIGN MATRIX ==
            logging.info(f"Running GLM for contrast: {cname}, encounter: {idx+1}")
            cmaps, subj_ids = zip(*contrast_maps_by_encounter_number[cname][idx])
            cmaps = [nb.load(cmap) for cmap in cmaps]
            subj_ids = [
                np.float64(float(subj_id.replace('sub-s', '')))
                for subj_id in subj_ids
            ]
            desmat = pd.DataFrame({
                'intercept': 1,
                'subject': subj_ids
            })

            # == FIT SECOND LEVEL MODEL ==
            second_level_model = SecondLevelModel(smoothing_fwhm=8.0)
            second_level_model.fit(cmaps, design_matrix=desmat)

            # == COMPUTE CONTRAST ==
            z_map = second_level_model.compute_contrast(
                second_level_contrast='intercept',
                output_type='z_score'
            )

            # == THRESHOLD MAP ==
            thresholded_map, threshold = threshold_stats_img(
                z_map, alpha=alpha, height_control='fpr'
            )

            # == PLOT MAPS (THRESHOLDED AND UNTHRESHOLDED) ==
            plot_stat_map(thresholded_map, threshold, cname, idx, outdir, template, title=f'{cname} - Encounter #{idx+1} (FPR-corrected p < {alpha})')
            plot_stat_map(z_map, liberal_threshold, cname, idx, outdir, template, title=f'{cname} - Encounter #{idx+1} (z > {liberal_threshold:.2f})')

    return

if __name__ == "__main__":
    main()
