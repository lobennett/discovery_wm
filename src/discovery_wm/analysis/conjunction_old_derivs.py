# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "templateflow",
# ]
# ///
from pathlib import Path
from nilearn import image, plotting
import templateflow.api as tf
import matplotlib.pyplot as plt
import numpy as np

def get_paths():
    oak = Path("/oak/stanford/groups/russpold/")
    bids = oak / "data/network_grant/discovery_BIDS_21.0.1/"
    output = bids / "derivatives/output_v4/"
    fitlins = bids / "derivatives/fitlins_analyzed_07_25_22"
    n_back_fx = output / "nBack_lev1_output/task_nBack_rtmodel_rt_centered/contrast_estimates"
    directed_forgetting_fx = output / "directedForgetting_lev1_output/task_directedForgetting_rtmodel_rt_centered/contrast_estimates"
    return n_back_fx, directed_forgetting_fx, fitlins

def get_contrast_files(contrast_dir, pattern):
    contrast_files = list(contrast_dir.glob(pattern))
    print(f'Found {len(contrast_files)} contrast files')
    return contrast_files

def resample_to_mni(files, mni_img):
    resampled_files = []
    for f in files:
        img = image.load_img(f)
        resampled_img = image.resample_to_img(
            img, 
            mni_img, 
            interpolation='continuous',
            force_resample=True,
            copy_header=True
        )
        print(f'Resampled {f} with shape {img.shape} to MNI space with shape {resampled_img.shape}')
        resampled_files.append(resampled_img)
    return resampled_files

def create_mean_img(files, mask):
    masked_imgs = []
    for f in files:
        img = image.load_img(f)
        # Apply the mask to each individual image
        masked_img = image.math_img('img1 * img2', img1=img, img2=mask)
        masked_imgs.append(masked_img)
    
    # Average the masked images
    return image.mean_img(masked_imgs, copy_header=True)

def create_conjunction_img(img1, img2):
    conjunction_img = image.math_img('np.minimum(img1, img2)', img1=img1, img2=img2)
    return conjunction_img

def plot_img(img, title, bg_img,coords = np.linspace(-10, 70, 12), threshold=None, outdir="./figs"):
    data = image.get_data(img)    
    # fig, ax = plt.subplots(figsize=(20, 4))
    if threshold is None:
        full_title = f'{title}_unthresholded'
    else:
        full_title = f'{title}_thresholded_{threshold}'
    
    display = plotting.plot_stat_map(
        img,
        title=title,
        display_mode='z',
        cut_coords=coords,
        colorbar=True,
        cmap='coolwarm',
        vmin=-1 * data.max(),
        vmax=data.max(),
        threshold=threshold,
        bg_img=bg_img,
        black_bg=False,
    )
    plt.savefig(f"./{outdir}/{full_title}.png")
    plt.close()

def main():
    outdir = Path('./figs')
    outdir.mkdir(exist_ok=True)

    n_back_fx, directed_forgetting_fx, fitlins = get_paths()
    
    n_back_fx_files = get_contrast_files(n_back_fx, "*twoBack-oneBack*fixed*t-test.nii.gz")
    directed_forgetting_fx_files = get_contrast_files(directed_forgetting_fx, "*neg-con*fixed*t-test.nii.gz")

    # Load common mask
    mni_file = tf.get('MNI152NLin2009cAsym', resolution=2, desc=None, suffix='T1w')
    mni_img = image.load_img(mni_file)
    mni_mask = tf.get('MNI152NLin2009cAsym', resolution=2, desc='brain', suffix='mask')
    
    # n_back_fitlins_files = get_contrast_files(fitlins, "*/fitlins/sub-*/*twoBackOneBack*stat-t_statmap.nii.gz")
    # directed_forgetting_fitlins_files = get_contrast_files(fitlins, "*/fitlins/sub-*/*negCon*stat-t_statmap.nii.gz")
    
    n_back_fx_mni_files = resample_to_mni(n_back_fx_files, mni_img)
    directed_forgetting_fx_mni_files = resample_to_mni(directed_forgetting_fx_files, mni_img)

    n_back_mni_mean_img = create_mean_img(n_back_fx_mni_files, mni_mask)
    directed_forgetting_mni_mean_img = create_mean_img(directed_forgetting_fx_mni_files, mni_mask)

    print('Creating conjunction image...')
    conj_img = create_conjunction_img(n_back_mni_mean_img, directed_forgetting_mni_mean_img)

    print('Saving mean images...')
    n_back_mni_mean_img.to_filename(outdir / "nBack_lev1_output_v4_mni_mean.nii.gz")
    directed_forgetting_mni_mean_img.to_filename(outdir / "directedForgetting_lev1_output_v4_mni_mean.nii.gz")
    print('Saving conjunction image...')
    conj_img.to_filename(outdir / "conjunction_img.nii.gz")

    thresholds = [0.1, 2.0, 2.5, 3.0]
    for threshold in thresholds:
        print(f'Plotting nBack image with threshold {threshold}...')
        plot_img(n_back_mni_mean_img, "nBack_lev1_output_v4_mni_mean", mni_img, threshold=threshold)
        print(f'Plotting directed forgetting image with threshold {threshold}...')
        plot_img(directed_forgetting_mni_mean_img, "directedForgetting_lev1_output_v4_mni_mean", mni_img, threshold=threshold)
        print(f'Plotting conjunction image with threshold {threshold}...')
        plot_img(conj_img, "conjunction_img", mni_img, threshold=threshold)
    
    return

if __name__ == "__main__":
    main()
