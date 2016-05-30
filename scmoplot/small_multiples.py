import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FixedLocator
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

fig, axarr = plt.subplots(ncols=gridsize[0], nrows=gridsize[1], 
                          figsize=(10, 10))

for row in axarr:
    for ax in row:
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_xlim(-xlim, xlim)
        ax.set_ylim(-ylim, ylim)

Hcs = [[None for i in range(5)] for i in range(5)]
Mrs = [[None for i in range(5)] for i in range(5)]
for f in listdir(root_path):
    gleaned = ng.glean(f)
    if gleaned['averaged']:
        print('Plotting %s' % f)
        x, y = int(gleaned['x']), int(gleaned['y'])
        ax = axarr[x, y]
        B, V = np.loadtxt(join(root_path, f), usecols=(0, 1), unpack=True, 
                          skiprows=1)
        B, V = tfmr((B, V), f)
        # print('\tMin: %f\tMax: %f' %(min(V), max(V)))
        ax.plot(B, V, 'k-')

        Hc = tfms.Hc_of(B, V)
        Hcs[y][x] = Hc
        # print('\t', Hc)
        Mr = tfms.Mrem_of(B, V)
        Mrs[y][x] = Mr
        # print('\t', Mr)
        zs = np.zeros(3)
        ax.plot(zs, Mr, 'ro', ms=7)
        ax.plot(Hc, zs, 'ro', ms=7)

plt.tight_layout(w_pad=0, h_pad=0)
plt.show()

Hcs = np.array([x[1] for row in Hcs for x in row])
Mrs = np.array([x[1] for row in Mrs for x in row])
# Hcsnp = np.array([[x[1] for x in row] for row in Hcs])
# Mrsnp = np.array([[x[1] for x in row] for row in Mrs])

gs = GridSpec(10, 10)
ax0 = plt.subplot(gs[0:9, :5])
ax1 = plt.subplot(gs[9, :5])
ax2 = plt.subplot(gs[0:9, 5:])
ax3 = plt.subplot(gs[9, 5:])
fig = ax0.get_figure()
fig.set_size_inches(12, 8)

n = Normalize(vmin=0.0, vmax=5.0, clip=True)
res = ax0.pcolor(Hcs.reshape(5, 5), cmap='afmhot', norm=n, edgecolors='k')
plt.colorbar(res, cax=ax1, orientation='horizontal', ticks=(0, 2.5, 5))
n = Normalize(vmin=0.0, vmax=1.0, clip=True)
res = ax2.pcolor(Mrs.reshape(5, 5), cmap='afmhot', norm=n, edgecolors='k')
plt.colorbar(res, cax=ax3, orientation='horizontal', ticks=(0, 0.5, 1))

ax0.set_title('Hc (mT)')
ax0.set_aspect('equal', adjustable='box')
ax2.set_title('Mrem/Msat')
ax2.set_aspect('equal', adjustable='box')
plt.tight_layout()
plt.show()
