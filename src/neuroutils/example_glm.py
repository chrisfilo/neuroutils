# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
This is an example where
1. An sequence of fMRI volumes are simulated
2. A design matrix describing all the effects related to the data is computed
3. A GLM is applied to all voxels
4. A contarst image is created

Author : Bertrand Thirion, 2010
"""
print __doc__

import numpy as np
import os.path as op
import matplotlib.pylab as mp
import tempfile

from nipy.io.imageformats import load, save, Nifti1Image
import nipy.neurospin.utils.design_matrix as dm
from nipy.neurospin.utils.simul_multisubject_fmri_dataset import \
     surrogate_4d_dataset
import nipy.neurospin.glm as GLM

#######################################
# Simulation parameters
#######################################

# volume mask
shape = (80, 80, 80)
affine = np.eye(4)

# timing
n_scans = 128
tr = 2.4

# paradigm
frametimes = np.linspace(0, (n_scans-1)*tr, n_scans)
conditions = np.arange(20)%2
onsets = np.linspace(5, (n_scans-1)*tr-10, 20) # in seconds
hrf_model = 'Canonical'
motion = np.cumsum(np.random.randn(n_scans, 6),0)
add_reg_names = ['tx','ty','tz','rx','ry','rz']

# write directory
swd = tempfile.mkdtemp()

########################################
# Design matrix
########################################

paradigm = dm.EventRelatedParadigm(conditions, onsets)
X, names = dm.dmtx_light(frametimes, drift_model='Cosine', hfcut=128,
               hrf_model=hrf_model, paradigm=paradigm, add_regs=motion, add_reg_names=add_reg_names)


#######################################
# Get the FMRI data
#######################################

fmri_data = surrogate_4d_dataset(shape=shape, n_scans=n_scans)[0]

# if you want to save it as an image
data_file = op.join(swd,'fmri_data.nii')
save(fmri_data, data_file)

########################################
# Perform a GLM analysis
########################################

# GLM fit
Y = fmri_data.get_data()
model = "ar1"
method = "kalman"
glm = GLM.glm()
mp.pcolor(X)
mp.show()
glm.fit(Y.T, X, method=method, model=model)
#explained = np.dot(X,glm.beta.reshape(X.shape[1],-1)).reshape(Y.T.shape).T
#residuals = Y - explained 
#residuals_image = Nifti1Image(np.reshape(residuals, shape), affine)


# specify the contrast [1 -1 0 ..]
contrast = np.zeros(X.shape[1])
contrast[0] = 1
contrast[1] = -1
my_contrast = glm.contrast(contrast)

# compute the constrast image related to it
zvals = my_contrast.zscore()
contrast_image = Nifti1Image(np.reshape(zvals, shape), affine)

# if you want to save the contrast as an image
contrast_path = op.join(swd, 'zmap.nii')
save(contrast_image, contrast_path)


print 'wrote the some of the results as images in directory %s' %swd

h,c = np.histogram(zvals, 100)
import pylab
pylab.figure()
pylab.plot(c[:-1],h)
pylab.title(' Histogram of the z-values')
pylab.show()
