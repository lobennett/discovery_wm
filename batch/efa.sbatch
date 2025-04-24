#!/bin/bash
#
#SBATCH -J efa
#SBATCH --time=2-00:00:00
#SBATCH -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=8G
#SBATCH -p russpold,hns,normal 
# Outputs ----------------------------------
#SBATCH -o ./log/%x-%A-%a.out
#SBATCH -e ./log/%x-%A-%a.err
#SBATCH --mail-user=logben@stanford.edu
#SBATCH --mail-type=END
# ------------------------------------------

# Prepare env
# ml R

# Script names
efa_script="src/discovery_wm/efa/efa.py"

# Run the first-level model script
echo "Running EFA..."
cmd="uv run $efa_script"
echo "Running command: $cmd"
$cmd
