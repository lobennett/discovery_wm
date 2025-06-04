import pandas as pd
from pathlib import Path
from discovery_wm.utils import get_path_config, get_all_subj_paths, get_subj_sessions

def extract_subj_ses_task(fname):
    parts = fname.split("_")
    subj = next(p for p in parts if p.startswith("sub-"))
    ses = next(p for p in parts if p.startswith("ses-"))
    task = next(p for p in parts if p.startswith("task-")).replace("task-", "")
    return subj, ses, task

# Set the path to your events files directory
bids_dir, _, _, _, _, _, behavioral_dir = get_path_config()

all_subjects = get_all_subj_paths(bids_dir)
sessions_of_interest = {"ses-11", "ses-12"}

for subj in all_subjects:
    for ses in get_subj_sessions(subj):
        if ses.name in sessions_of_interest:
            func_dir = ses / "func"
            for f in func_dir.rglob("*_events.tsv"):
                df = pd.read_csv(f, sep="\t")
                n_break = (df['trial_id'] == 'break').sum()
                n_perf = (df['trial_id'] == 'break_with_performance_feedback').sum()
                if n_break == 0 and n_perf > 1:
                    subj_str, ses_str, task_str = extract_subj_ses_task(f.name)
                    print(f"{subj_str}, {ses_str}, {task_str}: {n_perf} performance feedback breaks, 0 regular breaks")

            