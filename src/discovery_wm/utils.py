from pathlib import Path
import json

def get_paths():
    """Get paths to the data."""
    with open("data/path_config.json", "r") as f:
        path_config = json.load(f)

    bids_dir = path_config["bids_dir"]
    fmriprep_dir = path_config["fmriprep_dir"]
    tedana_dummy_removed_dir = path_config["tedana_dummy_removed_dir"]
    tedana_denoised_dir = path_config["tedana_denoised_dir"]
    tedana_transformed_dir = path_config["tedana_transformed_dir"]
    glm_data_dir = path_config["glm_data_dir"]
    behavioral_dir = path_config["behavioral_dir"]

    return (
        bids_dir, 
        fmriprep_dir, 
        tedana_dummy_removed_dir, 
        tedana_denoised_dir, 
        tedana_transformed_dir, 
        glm_data_dir,
        behavioral_dir
    )


def get_all_subject_paths(bids_dir):
    """Get all subjects in the BIDS directory."""
    return [f for f in Path(bids_dir).glob("sub-*")]


def get_subj_sessions(subject_path):
    """Get all sessions for a subject."""
    return [f for f in Path(subject_path).glob("ses-*")]


def dump_json(json_data, json_fmap):
    """Dump json data to a file."""
    with open(json_fmap, "w") as f:
        json.dump(json_data, f, indent=4)