#!/bin/bash

# Base paths 
export BIDS_DIR="/oak/stanford/groups/russpold/data/network_grant/discovery_BIDS_20250402/"
export APPTAINER_DIR="./apptainer_images"

# fMRIPrep version
# - NOTE: Change tags to match the version you want to use
export TAG="latest" 
export TIMESTAMP="20250402"
export FMRIPREP_VERSION="${APPTAINER_DIR}/fmriprep_${TAG}_${TIMESTAMP}.sif"

# - FMRIPrep
export FMRIPREP_DERIVS_DIR="${BIDS_DIR}/derivatives/fmriprep_${TAG}"
export FMRIPREP_WORK_DIR="./work/fmriprep_${TAG}"

# Batch input
export ALL_SUBJECTS_FILE="./all_subs.txt"

# FreeSurfer license
# - NOTE: Change this to the path to your FreeSurfer license file
export FS_LICENSE="$HOME/license.txt"