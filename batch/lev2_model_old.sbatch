#!/bin/bash
#
# Job name specified from launch script. 
#SBATCH --time=02:00:00
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4G
#SBATCH -p russpold,hns,normal 
# Outputs ----------------------------------
#SBATCH -o ./log/%x-%A-%a.out
#SBATCH -e ./log/%x-%A-%a.err
#SBATCH --mail-user=logben@stanford.edu
#SBATCH --mail-type=END
# ------------------------------------------

: '
Name: lev2_model.sbatch

Description: This script runs second-level GLM models for a specific task.

Usage: sbatch ./batch/lev2_model.sbatch TASK_NAME

Notes: 
- TASK_NAME should be one of: cuedTS, directedForgetting, flanker, goNogo, nBack, stopSignal, shapeMatching, spatialTS
'

TASK_NAME=$1

if [ -z "$TASK_NAME" ]; then
    echo "Error: Task name not provided"
    echo "Usage: sbatch ./batch/lev2_model.sbatch TASK_NAME"
    exit 1
fi

# Script names 
second_level_script="src/discovery_wm/glm/second_level.py"

# Run the second-level model script
echo "Running second-level model for task: $TASK_NAME"
cmd="uv run $second_level_script --task-name $TASK_NAME"
echo "Running command: $cmd"
$cmd

exit $? 
