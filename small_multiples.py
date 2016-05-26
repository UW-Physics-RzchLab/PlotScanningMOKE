import matplotlib.pyplot as plt
import numpy as np
from os import listdir
from os.path import join
from lvxml2dict import Cluster
from namegleaner import NameGleaner
from transformer import Transformer
import transformations as tfms
import re

xlim, ylim = 20.0, 1.1
thresh = 13

ng = NameGleaner(scan=r'scan=(\d+)', x=r'x=(\d+)', y=r'y=(\d+)',
                 averaged=r'(averaged)')

tfmr = Transformer(gleaner=ng)
# Args: add(slot, func, params={}, filter='.*')
tfmr.add(10, tfms.scale, params={'xsc': 0.1})
tfmr.add(20, tfms.flatten_saturation, 
          params={'threshold': thresh, 'polarity': '+'})
tfmr.add(25, tfms.center)
tfmr.add(30, tfms.wrapped_medfilt, params={'ks': 157})
tfmr.add(40, tfms.saturation_normalize, params={'thresh': thresh})


root_path = '/home/jji/Desktop/scanning_moke_test/trial0_5x5_BFO_test_sample'
clust = Cluster(join(root_path, 'parameters.xml')).to_dict()

# gridsize = (clust..., ...)   # can get from clust for newer clust datatype 
gridsize = (5, 5)

fig, axarr = plt.subplots(nrows=gridsize[1], ncols=gridsize[0], 
                          figsize=(10, 10))

for row in axarr:
    for ax in row:
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_xlim(-xlim, xlim)
        ax.set_ylim(-ylim, ylim)


for f in listdir(root_path):
    gleaned = ng.glean(f)
    if gleaned['averaged']:
        print('Plotting %s' % f)
        ax = axarr[gleaned['x'], gleaned['y']]
        B, V = np.loadtxt(join(root_path, f), usecols=(0, 1), unpack=True, 
                          skiprows=1)
        B, V = tfmr((B, V), f)
        print('\tMin: %f\tMax: %f' %(min(V), max(V)))
        ax.plot(B, V, 'k-')

plt.tight_layout(w_pad=0, h_pad=0)
plt.show()
