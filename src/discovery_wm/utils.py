from pathlib import Path
import json
import argparse

def get_path_config():
    """Get the path config from the config file."""
    with open("data/path_config.json") as f:
        data = json.load(f)
 
    required_keys = [
         'bids_dir', 'fmriprep_dir', 'tedana_dummy_removed_dir',
         'tedana_denoised_dir', 'tedana_transformed_dir', 'glm_data_dir', 
         'behavioral_dir'
    ]
    for key in required_keys:
        if key not in data or data[key] is None:
            raise KeyError(f"{key} is missing or None")
 
    return (Path(data[key]) for key in required_keys)


def get_parser():
    parser = argparse.ArgumentParser(description="Parallelize by subject ID")
    parser.add_argument("--subj-id", type=str, required=False, help="Subject ID to run")
    parser.add_argument("--all-subjs", type=bool, default=False, help="Run on all subjects")
    parser.add_argument("--task-name", type=str, required=False, help="Task name to run")
    parser.add_argument("--contrast-name", type=str, required=False, help="Contrast name to run")
    return parser

def get_all_subj_paths(bids_dir):
    """Get all subjects in the BIDS directory."""
    return [f for f in Path(bids_dir).glob("sub-*")]


def get_subj_sessions(subject_path):
    """Get all sessions for a subject."""
    return [f for f in Path(subject_path).glob("ses-*")]

def get_subj_id(parser):
    assert parser is not None, "Parser is not provided"
 
    subj_id = parser.parse_args().subj_id
 
    assert subj_id is not None, "Subject ID is not provided"
 
    if subj_id.startswith("sub-s"):
        return subj_id
     
    if subj_id.startswith("s"):
        return f"sub-{subj_id}"
     
    return f"sub-s{subj_id}"

def dump_json(json_data, json_fmap):
    """Dump json data to a file."""
    with open(json_fmap, "w") as f:
        json.dump(json_data, f, indent=4)

def get_ses_task_run(f):
    components = f.name.split('_')

    # Extract each component
    ses = next((comp for comp in components if comp.startswith('ses-')), None)
    task_name = next((comp for comp in components if comp.startswith('task-')), None)
    run_number = next((comp for comp in components if comp.startswith('run-')), None)

    return ses, task_name, run_number

def extract_contrast_name(contrast_file: Path) -> str:
    return contrast_file.name.split("contrast-")[1].split("_rtmodel")[0]