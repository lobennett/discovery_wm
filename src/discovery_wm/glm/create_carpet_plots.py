import os
from glob import glob
from pathlib import Path

import matplotlib.pyplot as plt
import nibabel as nf
import numpy as np
import pandas as pd
import seaborn as sns
from nilearn import masking
from nilearn.masking import apply_mask
from discovery_wm.utils import get_parser, get_subj_id

def extract_session_from_filename(filename: str) -> str:
    """Extract session from filename"""
    return (
        filename.split('_ses-')[1].split('_')[0] if '_ses-' in filename else 'unknown'
    )

def get_task_baseline_contrasts(task_name: str) -> str:
    """Get task-baseline contrast provided the task name"""
    contrasts = {
        "cuedTS": (
            "1/3*(task_stay_cue_switch+task_stay_cue_stay+task_switch_cue_switch)"
        ),
        "spatialTS": (
            "1/3*(task_stay_cue_switch+task_stay_cue_stay+task_switch_cue_switch)"
        ),
        "directedForgetting": "1/4*(con+pos+neg+memory_and_cue)",
        "flanker": "1/2*congruent + 1/2*incongruent",
        "goNogo": "1/2*go+1/2*nogo_success",
        "nBack": "1/4*(mismatch_1back+match_1back+mismatch_2back+match_2back)",
        "stopSignal": "1/3*go + 1/3*stop_failure + 1/3*stop_success",
        "shapeMatching": "1/7*(SSS+SDD+SNN+DSD+DDD+DDS+DNN)",
        "directedForgettingWFlanker": (
            "1/7*(congruent_pos+congruent_neg+congruent_con+incongruent_pos+"
            "incongruent_neg+incongruent_con+memory_and_cue)"
        ),
        "stopSignalWDirectedForgetting": (
            "1/10*(go_pos+go_neg+go_con+stop_success_pos+stop_success_neg+"
            "stop_success_con+stop_failure_pos+stop_failure_neg+stop_failure_con+"
            "memory_and_cue)"
        ),
        "stopSignalWFlanker": (
            "1/6*(go_congruent+go_incongruent+stop_success_congruent+"
            "stop_success_incongruent+stop_failure_congruent+stop_failure_incongruent)"
        )
    }
    return contrasts[task_name]

def get_target_contrast(contrast: str, task_name: str) -> str:
    """Get short name of contrast provided the full contrast name"""
    contrasts = {
        'task-baseline': get_task_baseline_contrasts(task_name),
        'main_vars': "1/3*(SDD+DDD+DDS)-1/2*(SNN+DNN)",
        'cue_switch_cost': "task_stay_cue_switch-task_stay_cue_stay",
        'task_switch_cost': "task_switch_cue_switch-task_stay_cue_switch",
        'match-mismatch': "1/2*(match_2back+match_1back-mismatch_2back-mismatch_1back)",
        'twoBack-oneBack': "1/2*(mismatch_2back+match_2back-mismatch_1back-match_1back)"
    }
    return contrasts.get(contrast, contrast)

def get_unique_contrasts(indiv_contrasts_dir: Path, subj_id: str, task_name: str) -> list[str]:
    """Get unique contrasts from effect size files"""
    all_contrasts = glob(f"{indiv_contrasts_dir}/*{subj_id}*{task_name}*effect-size*")
    contrasts = [
        contrast.split('_contrast-')[1].split('_rtmodel')[0]
        for contrast in all_contrasts
    ]
    return np.unique(contrasts)

def main():
    # get unique contrast names
    parser = get_parser()
    task_name = parser.parse_args().task_name
    subj_id = get_subj_id(parser)

    # Paths
    # - Input path 
    subj_lev1_dir = Path(f"./output_lev1_mni/{subj_id}/{task_name}")
    # - Contains effect size files for subject
    indiv_contrasts_dir = Path(f"{subj_lev1_dir}/indiv_contrasts")
    # - Contains files with corresponding VIF values for subject
    quality_control_dir = Path(f"{subj_lev1_dir}/quality_control")

    # Get unique contrasts
    unique_contrasts = get_unique_contrasts(indiv_contrasts_dir, subj_id, task_name)

    # carefully concatenate contrasts and variance images to keep order consistent
    all_eff_sizes, all_eff_vars, all_con_names, all_sessions, all_vifs = [], [], [], [], []

    for contrast in unique_contrasts:
        # Get effect size and variance files
        contrast_effect_size = glob(f'{indiv_contrasts_dir}/*{subj_id}*{task_name}*contrast-{contrast}_rtmodel*effect-size*')
        contrast_effect_var = [
            eff_size.replace('effect-size', 'variance')
            for eff_size in contrast_effect_size
        ]

        # Extract session numbers from filenames
        sessions = []

        for eff_size in contrast_effect_size:
            # Extract session from filename (format: ses-XX)
            # - Session
            session_match = extract_session_from_filename(eff_size)
            sessions.append(session_match)

            # LOAD VIFS
            vif_file = list(
                quality_control_dir.glob(f"*{subj_id}*{session_match}*{task_name}*")
            )

            assert len(vif_file) == 1, f"Expected 1 VIF file, found {len(vif_file)}"

            # Get VIF value
            vif_data = pd.read_csv(vif_file[0])
            target_contrast = get_target_contrast(contrast, task_name)
            vif_value = vif_data[
                vif_data['contrast'] == target_contrast
            ]['VIF'].values[0]
            all_vifs.append(vif_value)

        all_eff_sizes.extend(contrast_effect_size)
        all_eff_vars.extend(contrast_effect_var)
        all_con_names.extend([contrast]*len(contrast_effect_size))
        all_sessions.extend(sessions)

    # prep data and mask
    eff_size_4d = nf.funcs.concat_images(all_eff_sizes)
    eff_size_4d_array = eff_size_4d.get_fdata()

    mask_img = masking.compute_epi_mask(eff_size_4d)

    # get min/max for colorbar (feel free to change)
    # We're mosty interested in finding outliers, so we don't really need to see the
    # full range of values
    # i.e., there will be a lot of gray in the image and those voxels are fine as they
    # will not be outliers
    data_nonzero = eff_size_4d_array[eff_size_4d_array.nonzero()]
    cutoff_max = np.quantile(data_nonzero, .9)
    cutoff_min = np.quantile(data_nonzero, .1)

    # Apply mask and plot
    data = apply_mask(eff_size_4d, mask_img)

    # Sort data by contrast name and then by session number
    # Create a list of tuples with (contrast, session, index)
    sort_indices = [
        (con, int(ses), i)
        for i, (con, ses) in enumerate(zip(all_con_names, all_sessions))
    ]
    # Sort by contrast first, then by session number as integer
    sort_indices.sort(key=lambda x: (x[0], x[1]))
    # Get the original indices in the sorted order
    sorted_indices = [i for _, _, i in sort_indices]

    # Reorder data and labels
    sorted_data = data[sorted_indices]
    sorted_con_names = [all_con_names[i] for i in sorted_indices]
    sorted_sessions = [all_sessions[i] for i in sorted_indices]
    sorted_vifs = [all_vifs[i] for i in sorted_indices]

    # Create carpet plot
    plt.figure(figsize=(20, 10))
    plt.subplots_adjust(left=0.3)
    sns.heatmap(
        sorted_data, cmap='coolwarm', center=0, vmin=cutoff_min, vmax=cutoff_max
    )
    plt.xticks([], [])
    plt.xlabel('Voxels')

    # Create combined labels with contrast, session, and VIF value
    combined_labels = [
        f"{con} (ses-{ses}) (VIF={vif:.2f})"
        for con, ses, vif in zip(sorted_con_names, sorted_sessions, sorted_vifs)
    ]

    plt.yticks(
        ticks=np.arange(len(combined_labels)), labels=combined_labels, rotation=0
    )
    plt.ylabel('Contrasts')
    plt.title(f'Effect sizes ({subj_id})')

    # Save carpet plot
    outdir = f'./output_lev1_mni/figures/{subj_id}/{task_name}/carpet_plots/'
    os.makedirs(outdir, exist_ok=True)
    outpath = f'{outdir}/{subj_id}_{task_name}_effect_sizes.png'
    plt.savefig(outpath)
    print(f"Saved {outpath}")   
    plt.close()

if __name__ == "__main__":
    main()
