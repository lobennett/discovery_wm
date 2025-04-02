import logging
import json
from discovery_wm.utils import get_paths, get_all_subject_paths, get_subj_sessions, dump_json

def create_json_path(subj, ses):
    """Create a json fmap file for a subject and session."""
    subj_id = subj.name
    basename = f'{subj_id}_{ses.name}_run-1_fieldmap.json'
    json_fmap = ses / "fmap" / basename
    return json_fmap

def create_json_data(subj, ses):
    """Create a json fmap data for a subject and session."""
    subj_id = subj.name
    basename = f'{subj_id}_{ses.name}_run-1_fieldmap.json'
    return {
        "B0FieldIdentifier": basename
    }

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Adding sidecars to BIDS directory")

    bids_dir, _, _, _, _, _, _= get_paths()

    all_subjects = get_all_subject_paths(bids_dir)
    
    for subj in all_subjects:
        sessions = get_subj_sessions(subj)
        for ses in sessions:
            fmap_dir = ses / "fmap"
            if not fmap_dir.exists():
                raise ValueError(f"No fmap directory found for {subj} {ses}")
            
            json_fmap = create_json_path(subj, ses)
            json_data = create_json_data(subj, ses)

            if not json_fmap.exists():
                logging.info(f"Added json fmap file for {ses}")
                dump_json(json_data, json_fmap)
            else:
                logging.warning(f"Skipping {subj} {ses}: already exists")
    

if __name__ == "__main__":
    main()