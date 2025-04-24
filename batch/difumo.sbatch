#!/bin/bash
#
#SBATCH -J difumo
#SBATCH --time=02:00:00
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

# Script names 
difumo_script="src/discovery_wm/efa/difumo.py"

# Run the first-level model script
echo "Creating difumo parcellated data..."
cmd="uv run $difumo_script"
echo "Running command: $cmd"
$cmd