#!/bin/bash
#
#SBATCH -J copy
#SBATCH --time=1-00:00:00
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

# 
source=/scratch/users/logben/discovery_wm/output_lev1_mni/
target=/oak/stanford/groups/russpold/data/network_grant/discovery_BIDS_20250402/derivatives/output_lev1_mni/
rsync -av --progress $source $target/
# 

# source=/oak/stanford/groups/russpold/data/network_grant/discovery_BIDS_21.0.1/
# target=/oak/stanford/groups/russpold/data/network_grant/discovery_BIDS_20250402/
# rsync -av --progress --exclude='/derivatives/' $source $target

# # Remove all averaged fmap sessions
# rm -rf $target/sub-s*/ses-00/
# # Remove all events.tsv files
# rm -rf $target/sub-s*/ses-*/func/*events.tsv
