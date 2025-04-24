#!/bin/bash
#SBATCH --job-name=launch_all_outlier_check
#SBATCH --output=./log/launch_all_outlier_check_%j.out
#SBATCH --error=./log/launch_all_outlier_check_%j.err
#SBATCH --time=00:05:00
#SBATCH -p russpold,hns,normal
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G

# Launch each batch script in current directory
for script in ./batch/quality_control/*.sbatch; do
    echo "Launching $script"
    sbatch $script
done
