from discovery_wm.utils import get_path_config, get_all_subj_paths, dump_json
import logging
from pathlib import Path
from templateflow import api as tf
from nilearn import image
import numpy as np

def get_all_mni_masks(glm_data_dir: Path) -> list[str]:
    tag = "MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"
    pattern = f"ses-*/func/*{tag}"
    return [str(p) for p in glm_data_dir.glob(pattern)]

def get_mask_data_and_size(mni_mask: str) -> tuple[np.ndarray, int]:
    mask_img = image.load_img(mni_mask)
    mask_data = mask_img.get_fdata() > 0
    mask_size = mask_data.sum()
    return mask_data, mask_size

def get_dice_scores(mni_masks: list[str], template: str) -> list[float]:
    dice_scores = {}
    template_data, template_size = get_mask_data_and_size(template)

    for mni_mask in mni_masks:
        mask_name = mni_mask.split('/')[-1]
        mask_data, mask_size = get_mask_data_and_size(mni_mask)

        assert mask_data.shape == template_data.shape, (
            f"Mask {mni_mask} and template {template} have different shapes for {mni_mask}"
        )

        dice_score = 2 * (mask_data & template_data).sum() / (mask_size + template_size)
        dice_scores[mask_name] = dice_score
        
    return dice_scores

def flag_dice_scores(dice_scores: dict[str, float], threshold: float) -> dict[str, dict[str, float]]:
    flagged_dice_scores = {}
    for subj_id, dice_scores in dice_scores.items():
        for mask, score in dice_scores.items():
            if score < threshold:
                flagged_dice_scores[subj_id] = dice_scores
    return flagged_dice_scores

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Adding sidecars to BIDS directory")

    bids_dir, fmriprep_dir, _, _, _, glm_data_dir, _ = get_path_config()

    all_subjects = get_all_subj_paths(bids_dir)

    template = tf.get("MNI152NLin2009cAsym", resolution=2, desc="brain", suffix="mask")
    print(f"Using template {template}")

    all_dice_scores = {}
    for subj in all_subjects:
        logging.info(f"Processing {subj.stem}")
        subj_id = subj.stem
        subj_glm_dir = Path(glm_data_dir, subj_id)
        all_mni_masks = get_all_mni_masks(subj_glm_dir)
        print(f'Found {len(all_mni_masks)} MNI masks...')
        subj_dice_scores = get_dice_scores(all_mni_masks, template)
        all_dice_scores[subj_id] = subj_dice_scores

    print(f'All dice scores: \n{all_dice_scores}')

    flagged_dice_scores = flag_dice_scores(all_dice_scores, 0.85)
    print(f'Found {len(flagged_dice_scores)} subjects with dice scores below {threshold}: \n{flagged_dice_scores}')

    # Write all and flagged dice scores to file
    dump_json(all_dice_scores, 'all_dice_scores.json')
    dump_json(flagged_dice_scores, 'flagged_dice_scores.json')

    return

if __name__ == "__main__":
    main()