#!/bin/bash
#
#SBATCH -J tedana-transform-MNI
#SBATCH --time=2-00:00:00
#SBATCH -n 1
#SBATCH --array 1-5
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=6G
#SBATCH -p russpold,hns,normal 
# Outputs ----------------------------------
#SBATCH -o ./log/%x-%A-%a.out
#SBATCH -e ./log/%x-%A-%a.err
#SBATCH --mail-user=logben@stanford.edu
#SBATCH --mail-type=END
# ------------------------------------------


: '

Name: tedana.sbatch

Description: This script runs tedana on a dataset. 

Usage: sbatch ./batch/tedana.sbatch

Notes: 

'

# Prepare computing environment
source ./batch/setup_env.sh

# Get script paths relative to project root
script_files=(
    # "src/discovery_wm/tedana/01_remove_dummy_trs.py"
    # "src/discovery_wm/tedana/02_denoise_data.py"
    "src/discovery_wm/tedana/03_tedana_transform.py"
    # src/discovery_wm/tedana/04_prepare_glm_directory.py"
)

# Get the subject ID from the command line arguments
subject=$( sed "${SLURM_ARRAY_TASK_ID}q;d" ${ALL_SUBJECTS_FILE} )
echo "Subject: $subject"

# Load modules for tedana transform
ml biology ants

# Get full path to uv executable
uv_exec=$(which uv)

# Run each script using the uv executable
for script in "${script_files[@]}"; do
    echo "Running script: $script"
    $uv_exec run "$script" --subj-id "$subject"
    echo "Completed script: $script"
done

echo "All scripts completed"

exitcode=$?
echo "Exit code: $exitcode"
exit $exitcode
