from pathlib import Path
import pandas as pd
import numpy as np
from nilearn.datasets import load_mni152_template
from nilearn.glm import threshold_stats_img
from nilearn.glm.second_level import SecondLevelModel, non_parametric_inference
from nilearn import plotting 
import os
from templateflow import api as tf
from discovery_wm.utils import get_parser, get_subj_id, dump_json, extract_contrast_name
from nilearn import image


def get_all_task_contrasts(in_dir: Path) -> dict:
    task_contrasts = {}
    for subj in in_dir.glob("sub-s*"):
        for task in subj.glob("*"):
            if task.name not in task_contrasts:
                task_contrasts[task.name] = []
            for f in task.glob("fixed_effects/*fixed-effects.nii.gz"):
                cname = extract_contrast_name(f)
                if cname not in task_contrasts[task.name]:
                    task_contrasts[task.name].append(cname)
    return task_contrasts

def get_subj_ids(in_dir: str) -> list[str]:
    """Finds subject directories (like sub-sXXX) within the input directory."""
    matching_dirs = [p for p in Path(in_dir).glob("sub-s*") if p.is_dir()]
    subject_ids = sorted([p.name for p in matching_dirs])
    return subject_ids

def get_all_fx_contrast_files(in_dir: Path, task_name: str, contrast: str) -> list[str]:
    """Finds all fixed-effects contrast files matching the pattern."""
    files = []
    pattern = f"sub-*/{task_name}/fixed_effects/*contrast-{contrast}_*stat-fixed-effects.nii.gz"
    for f in in_dir.glob(pattern):
        cname = extract_contrast_name(f)
        if cname == contrast:
            files.append(str(f))
    return sorted(files)

def compute_contrast(files: list[str], design_matrix_df: pd.DataFrame, contrast: str, threshold_z: float = 2.0, n_jobs: int = 4):
    second_level_model = SecondLevelModel(n_jobs=n_jobs, verbose=1)
    second_level_model = second_level_model.fit(
        files, design_matrix=design_matrix_df
    )
    z_map = second_level_model.compute_contrast(
        second_level_contrast='intersect',
        first_level_contrast=contrast,
        output_type='z_score'
    )
    return z_map

def plot_glass_brain(z_map: str, out_dir: Path, task_name: str, contrast: str, threshold_z: float = 3.0):
    display = plotting.plot_glass_brain(
        z_map,
        threshold=threshold_z,
        title=f"Group {contrast} (Z > {threshold_z})",
        black_bg=True,
        display_mode="lyrz",
    )
    basename = f"task-{task_name}_contrast-{contrast}_glass_brain_threshold-{threshold_z}"
    display.savefig(out_dir / f"{basename}.png")

def main():
    # Parse the command line arguments
    parser = get_parser()
    task_name = parser.parse_args().task_name

    if not task_name:
        raise ValueError("Task name is required")

    in_dir = Path("./output_lev1_mni")
    out_dir = Path(f"./output_lev2_mni/{task_name}")
    glass_brain_dir = Path(f"./output_lev2_mni/{task_name}/glass_brain")
    log10_pvals_dir = Path(f"./output_lev2_mni/{task_name}/log10_pvals")
    glass_brain_dir.mkdir(parents=True, exist_ok=True)
    log10_pvals_dir.mkdir(parents=True, exist_ok=True)
    n_jobs = 4 

    task_contrasts = get_all_task_contrasts(in_dir)
    # dump_json(task_contrasts, "task_contrasts.json")
    # print(f"Saved task contrasts to: ./task_contrasts.json")
    
    contrasts = task_contrasts.get(task_name, None)
    if not contrasts:
        raise ValueError(f"No contrasts found for task: {task_name}")
    
    print(f"Found {len(contrasts)} contrasts for {task_name}: \n{contrasts}")

    threshold_z = 3.0

    subj_ids = get_subj_ids(in_dir)
    print(f"Found {len(subj_ids)} subjects in {in_dir}")

    # MNI template for background image
    template=tf.get('MNI152NLin2009cAsym', resolution=2, suffix="T1w", desc="brain")
    cut_coords=(-10, 0, 10, 20, 30, 40, 50, 60, 70)

    for contrast in contrasts:
        files = get_all_fx_contrast_files(in_dir, task_name, contrast)
        print(files)
        print(f'Found {len(files)} fx contrast files for {contrast} in {in_dir}')

        assert len(subj_ids) == len(files), (
            "Expected the number of subjects to match "
            "the number of fx contrast files found in the directory."
        )
        assert len(files) > 1, ( 
            f"Found only {len(files)} contrast file(s). "
            "Second level analysis requires multiple inputs."
        )

        subject_info_df = pd.DataFrame({
            'subject_label': subj_ids,
            'intersect': [1] * len(subj_ids)
        })
        design_matrix_df = subject_info_df[['intersect']]

        print("Computing contrast...")
        z_map = compute_contrast(files, design_matrix_df, contrast, threshold_z, n_jobs)

        print("Generating glass brain plot for the z-map...")
        
        # Glass brain plot
        plot_glass_brain(z_map, glass_brain_dir, task_name, contrast, threshold_z)

        print("Computing non-parametric p-values...")
        neg_log10_vfwe_pvals_img = non_parametric_inference(
            files,
            design_matrix=design_matrix_df,
            model_intercept=True,
            n_perm=10000,
            two_sided_test=False,
            mask=None,
            smoothing_fwhm=5.0,
            n_jobs=n_jobs,
        )

        print("Generating stat map plot...")
        max_value = np.max(neg_log10_vfwe_pvals_img.get_fdata())
        min_value = np.min(neg_log10_vfwe_pvals_img.get_fdata())

        if min_value < 0:
            msg = f"Min value of neg_log10_vfwe_pvals_img is {min_value}. "
            msg += "This is unexpected. Please check the data."
            raise ValueError(msg)

        threshold = 1
        min_display_threshold = 0.5

        effective_threshold = min(threshold, max_value) if max_value > min_display_threshold else 0

        vmax = max(max_value, min_display_threshold)

        title = f"Group {contrast} (Log P-values > {effective_threshold:.2f}, min: {min_value:.2f}, max: {max_value:.2f})"
        display = plotting.plot_stat_map(
            neg_log10_vfwe_pvals_img,
            cut_coords=cut_coords,
            threshold=effective_threshold,
            title=title,
            vmax=vmax,
            vmin=0,
            cmap="inferno",
            draw_cross=False,
            display_mode='z',
            bg_img=template,
        )
        basename = f"task-{task_name}_contrast-{contrast}_stat_map_log_p_values"
        display.savefig(log10_pvals_dir / f"{basename}.png")
        neg_log10_vfwe_pvals_img.to_filename(log10_pvals_dir / f"{basename}.nii.gz")
        print(f"Saved -log10(p-values) to: {log10_pvals_dir / f'{basename}.png'}")


    return

if __name__ == "__main__":
    main()