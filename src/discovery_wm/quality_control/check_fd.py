from pathlib import Path
import logging
import pandas as pd

from discovery_wm.utils import get_path_config, get_all_subj_paths, dump_json

def get_confound_files(subj_fmriprep_dir: Path) -> list[Path]:
    pattern = "ses-*/func/*confounds_timeseries.tsv"
    return list(subj_fmriprep_dir.glob(pattern))

def calculate_fd_metrics(fd_series: pd.Series) -> dict[str, float]:
    mean_fd = fd_series.mean()
    proportion_trs_over_threshold = (fd_series > 0.5).mean()
    return mean_fd, proportion_trs_over_threshold

def get_confound_values(confound_files: Path) -> dict[str, float]:
    confound_values = {}
    for f in confound_files:
        df = pd.read_csv(f, sep="\t")
        fd_series = df["framewise_displacement"]
        mean_fd, proportion_trs_over_threshold = calculate_fd_metrics(fd_series)
        confound_values[f.stem] = {
            "mean_fd": mean_fd,
            "proportion_trs_over_threshold": proportion_trs_over_threshold,
        }
    return confound_values

def get_flagged_confounds(
        confound_values: dict[str, dict[str, float]], 
        mean_threshold: float = 0.2, 
        proportion_threshold: float = 0.5
    ) -> dict[str, dict[str, float]]:
    return {
        f: v for f, v in confound_values.items() if v["mean_fd"] > mean_threshold 
        or v["proportion_trs_over_threshold"] > proportion_threshold
    }

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("Adding sidecars to BIDS directory")

    bids_dir, fmriprep_dir, _, _, _, _, _ = get_path_config()

    all_subjects = get_all_subj_paths(bids_dir)
    all_flagged_confounds = {}
    for subj in all_subjects:
        logging.info(f"Processing {subj.stem}")
        subj_id = subj.stem
        # subj_fmriprep_dir = Path(fmriprep_dir, subj_id)
        subj_fmriprep_dir = Path(
            fmriprep_dir, 
            subj_id
        )
        print(subj_fmriprep_dir)
        confound_files = get_confound_files(subj_fmriprep_dir)
        confound_values = get_confound_values(confound_files)
        flagged_confounds = get_flagged_confounds(confound_values)
        all_flagged_confounds[subj_id] = flagged_confounds

    # Sort the subjects by their ID
    all_flagged_confounds = dict(sorted(all_flagged_confounds.items()))
    dump_json(all_flagged_confounds, Path("all_flagged_confounds.json"))


if __name__ == "__main__":
    main() 