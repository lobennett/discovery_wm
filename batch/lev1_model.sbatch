#!/bin/bash
#
# Job name specified from launch script. 
#SBATCH --time=00:30:00
#SBATCH -n 1
#SBATCH --array 2
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=8G
#SBATCH -p russpold,hns,normal 
# Outputs ----------------------------------
#SBATCH -o ./log/%x-%A-%a.out
#SBATCH -e ./log/%x-%A-%a.err
#SBATCH --mail-user=logben@stanford.edu
#SBATCH --mail-type=END
# ------------------------------------------

: '
Name: lev1_model.sbatch

Description: This script runs first-level GLM models for a specific task.

Usage: sbatch ./batch/lev1_model.sbatch TASK_NAME

Notes: 
- TASK_NAME should be one of: cuedTS, directedForgetting, flanker, goNogo, nBack, stopSignal, shapeMatching, spatialTS
'

TASK_NAME=$1

if [ -z "$TASK_NAME" ]; then
    echo "Error: Task name not provided"
    echo "Usage: sbatch ./batch/lev1_model.sbatch TASK_NAME"
    exit 1
fi

# Prepare computing environment
source ./batch/setup_env.sh

# Script names 
first_level_script="src/discovery_wm/glm/first_level.py"
carpet_plots_script="src/discovery_wm/glm/create_carpet_plots.py"
brain_maps_script="src/discovery_wm/glm/create_brain_maps.py"


# Get the subject ID from the command line arguments
subject=$( sed "${SLURM_ARRAY_TASK_ID}q;d" ${ALL_SUBJECTS_FILE} )
echo "Subject: $subject"

# Run the first-level model script
echo "Running first-level model for task: $TASK_NAME"
cmd="uv run $first_level_script --subj-id $subject --task-name $TASK_NAME"
echo "Running command: $cmd"
$cmd

# Create carpet plots
cmd="uv run $carpet_plots_script --subj-id $subject --task-name $TASK_NAME"
echo "Running command: $cmd"
$cmd

# Create brain maps
cmd="uv run $brain_maps_script --subj-id $subject --task-name $TASK_NAME"
echo "Running command: $cmd"
$cmd

exit $? 
