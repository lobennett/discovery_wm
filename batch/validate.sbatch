#!/bin/bash
#
#SBATCH -J validate
#SBATCH --time=01:00:00
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

# Activate environment
source ./batch/setup_env.sh

# Just use full path to bids-validator image
# - We have one that exists in group home, so let's use that
apptainer_img=/home/groups/russpold/singularity_images/bids-validator_1.14.6.simg

# Run bids-validator
apptainer run $apptainer_img $BIDS_DIR