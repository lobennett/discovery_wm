import logging
from glob import glob
from pathlib import Path
from discovery_wm.utils import get_path_config, get_all_subj_paths, dump_json, get_ses_task_run

def get_echo_counts(func_dir, pattern):
    full_pattern = str(func_dir / pattern)
    echo_files = glob(full_pattern)
    return full_pattern, len(echo_files)

def find_dummy_removed_file(pattern, tedana_dummy_removed_dir):
    full_pattern = str(tedana_dummy_removed_dir / pattern)
    dummy_removed_files = glob(full_pattern)
    return dummy_removed_files, len(dummy_removed_files)

def find_denoised_file(pattern, tedana_denoised_dir):
    full_pattern = str(tedana_denoised_dir / pattern / "*optcom_bold.nii.gz")
    denoised_files = glob(full_pattern)
    return denoised_files, len(denoised_files)

def find_transformed_file(pattern, tedana_transformed_dir):
    full_pattern = str(tedana_transformed_dir / "ses-*" / "func" / pattern)
    transformed_files = glob(full_pattern)
    return transformed_files, len(transformed_files)

def get_bids_files(subj_bids_dir, subj_fmriprep_dir, tedana_dummy_removed_dir, tedana_denoised_dir, tedana_transformed_dir, glm_data_dir, expected=3):
    bids_files = {}
    missing_dummy_removed = {}
    missing_denoised = {}
    missing_t1w_transformed = {}
    missing_mni_transformed = {}
    missing_glm_data = {}
    for ses in subj_bids_dir.glob("ses-*"):
        bids_files[ses.name] = []
        for func in ses.glob("func"):
            for f in func.glob("*bold.nii.gz"):
                ses, task_name, run_number = get_ses_task_run(f)
                key = f"{ses}_{task_name}_{run_number}"
                bids_pattern = f"*{ses}*{task_name}*{run_number}*echo-*.nii.gz"
                dummy_removed_pattern = bids_pattern
                denoised_pattern = f"*{ses}*{task_name}*{run_number}*"
                t1w_transformed_pattern = f"*{ses}*{task_name}*{run_number}*space-T1w*desc-optcom_bold.nii.gz"
                # TODO: Uncomment this once we have MNI transformed data
                # mni_transformed_pattern = f"*{ses}*{task_name}*{run_number}*space-MNI*desc-optcom_bold.nii.gz"
                full_pattern, echo_count = get_echo_counts(func, bids_pattern)
                # There must be three echo files in bids
                assert echo_count == expected, f"Expected {expected} echo files, got {echo_count} for {f}"

                dummy_removed_files, dummy_removed_count = find_dummy_removed_file(dummy_removed_pattern, tedana_dummy_removed_dir)
                if dummy_removed_count != expected:
                    missing_dummy_removed[key] = dummy_removed_count

                denoised_files, denoised_count = find_denoised_file(denoised_pattern, tedana_denoised_dir)
                if denoised_count != 1:
                    missing_denoised[key] = denoised_count   
                
                t1w_transformed_files, t1w_transformed_count = find_transformed_file(t1w_transformed_pattern, tedana_transformed_dir)
                if t1w_transformed_count != 1:
                    missing_t1w_transformed[key] = t1w_transformed_count

                # TODO: Uncomment this once we have MNI transformed data
                # mni_transformed_files, mni_transformed_count = find_transformed_file(mni_transformed_pattern, tedana_transformed_dir)
                # if mni_transformed_count != 1:
                #     missing_mni_transformed[key] = mni_transformed_count

                # glm_data_files, glm_data_count = find_glm_data_file(pattern, glm_data_dir)
                # if glm_data_count != 1:
                #     missing_glm_data[key] = glm_data_count

    print(f"Missing dummy removed: {missing_dummy_removed}")
    print(f"Missing denoised: {missing_denoised}")
    print(f"Missing t1w transformed: {missing_t1w_transformed}")
    print(f"Missing mni transformed: {missing_mni_transformed}")
    return missing_dummy_removed, missing_denoised, missing_t1w_transformed, missing_mni_transformed

def add_summarized(json_log_data):
    """
    Add summarized session information to the JSON log data.
    Extracts unique session IDs from each missing data category.
    """
    for category in ['missing_dummy_removed', 'missing_denoised', 'missing_t1w_transformed', 'missing_mni_transformed']:
        if category in json_log_data:
            # Extract session IDs from keys like "ses-11_task-spatialTSWCuedTS_run-1"
            sessions = set()
            for key in json_log_data[category].keys():
                parts = key.split('_')
                session = next((part for part in parts if part.startswith('ses-')), None)
                if session:
                    sessions.add(session)
            
            # Add the summarized sessions to the JSON data
            json_log_data[f"{category}_sessions"] = sorted(list(sessions))
    
    return json_log_data

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Get the path config
    bids_dir, fmriprep_dir, tedana_dummy_removed_dir, tedana_denoised_dir, tedana_transformed_dir, glm_data_dir, _ = get_path_config()

    # Parse the command line arguments
    # - Get the subject ID from the command line arguments
    all_subjects = get_all_subj_paths(bids_dir)
    print(f"All subjects: {all_subjects}")
    all_subjects_data = {}

    for subj_id in all_subjects:
        json_log_file = Path(f"./log/{subj_id.name}/00_check_outputs.json")
        json_log_file.parent.mkdir(parents=True, exist_ok=True)
        json_log_data = {}
        subj_bids_dir = Path(bids_dir / subj_id)
        subj_fmriprep_dir = Path(fmriprep_dir / subj_id)
        subj_tedana_dummy_removed_dir = Path(tedana_dummy_removed_dir / subj_id)
        subj_tedana_denoised_dir = Path(tedana_denoised_dir / subj_id)
        subj_tedana_transformed_dir = Path(tedana_transformed_dir / subj_id)
        subj_glm_data_dir = Path(glm_data_dir / subj_id)
        missing_dummy_removed, missing_denoised, missing_t1w_transformed, missing_mni_transformed = get_bids_files(subj_bids_dir, subj_fmriprep_dir, subj_tedana_dummy_removed_dir, subj_tedana_denoised_dir, subj_tedana_transformed_dir, subj_glm_data_dir)
        
        # Add to summary file
        json_log_data["missing_dummy_removed"] = missing_dummy_removed
        json_log_data["missing_denoised"] = missing_denoised
        json_log_data["missing_t1w_transformed"] = missing_t1w_transformed
        json_log_data["missing_mni_transformed"] = missing_mni_transformed
        
        # Add summarized session information
        json_log_data = add_summarized(json_log_data)
        dump_json(json_log_data, json_log_file)
        print(f"Saved log file to {json_log_file}")
        all_subjects_data[subj_id] = json_log_data

    print(f"All subjects data: {all_subjects_data}")
    dump_json(all_subjects_data, "./log/all_subjects_data.json")
    return 

if __name__ == "__main__":
    main()