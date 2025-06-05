#!/bin/bash

# Base paths
export BIDS_DIR="/oak/stanford/groups/russpold/data/network_grant/validation_BIDS"
export APPTAINER_DIR="./apptainer_images"

# fMRIPrep version
# - NOTE: Change tags to match the version you want to use
export FMRIPREP_VERSION="/home/groups/russpold/singularity_images/fmriprep_24.1.0rc2.sif"

# - FMRIPrep
export FMRIPREP_DERIVS_DIR="./bids/derivatives/fmriprep-24.1.0rc2/"
export FMRIPREP_WORK_DIR="./work/fmriprep-24.1.0rc2/"

# Batch input
export ALL_SUBJECTS_FILE="./validation_subs.txt"

# FreeSurfer license
# - NOTE: Change this to the path to your FreeSurfer license file
export FS_DIR="/oak/stanford/groups/russpold/data/network_grant/validation_BIDS/derivatives/fmriprep-24.1.0rc2/sourcedata/freesurfer"
export FS_LICENSE="$HOME/license.txt"
