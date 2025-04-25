#!/bin/bash
#
#SBATCH -J launch-all-lev2
#SBATCH --time=00:05:00
#SBATCH -n 1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G
#SBATCH -p russpold,hns,normal 
# Outputs ----------------------------------
#SBATCH -o ./log/%x-%A-%a.out
#SBATCH -e ./log/%x-%A-%a.err
#SBATCH --mail-user=logben@stanford.edu
#SBATCH --mail-type=END
# ------------------------------------------


: '

Name: launch_all_lev2.sbatch

Description: This script launches all first-level models on a dataset. 

Usage: sbatch ./batch/launch_all_lev2.sbatch

Notes: 

'

# Define all task names
TASKS=(
    "cuedTS"
    "directedForgetting"
    "flanker"
    "goNogo"
    "nBack"
    "shapeMatching"
    "spatialTS"
    "stopSignal"
)

# Launch first-level models for each task
for task in "${TASKS[@]}"; do
    echo "Launching second-level model for task: $task"
    sbatch --job-name="lev2-model-${task}-mni" ./batch/lev2_model.sbatch "$task"
done

echo "All first-level models launched"