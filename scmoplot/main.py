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

""" TODO
  - Need a way to detect non-magnetic areas and normalize them differently...
     - Or don't normalize any curves and just compute the contrast range that
       the pcolor maps should use. This is what we will do if/when we convert
       to polarization rotation eventually.
"""


xlim, ylim = 10.0, 1.1
thresh, max = 7, 10  # thresh: where to start fits, max: highest field

ng = NameGleaner(scan=r'scan=(\d+)', x=r'x=(\d+)', y=r'y=(\d+)',
                 averaged=r'(averaged)')

tfmr = Transformer(gleaner=ng)
tfmr.add(10, tfms.scale, params={'xsc': 0.1})
tfmr.add(20, tfms.flatten_saturation, 
          params={'threshold': thresh, 'polarity': '+'})
tfmr.add(25, tfms.center)
tfmr.add(30, tfms.wrapped_medfilt, params={'ks': 157})
tfmr.add(40, tfms.saturation_normalize, params={'thresh': thresh})


root_path = '/home/jji/Desktop/scanning_moke_test/trial1_5x5_BFO_test_sample'
# root_path = r'C:\Users\Tor\Desktop\test\trial1_5x5_BFO_test_sample'
clust = Cluster(join(root_path, 'parameters.xml')).to_dict()

gridsize = (clust['Rows'], clust['Cols'])   # can get from clust for newer clust datatype 
#gridsize = (5, 5)

fig, axarr = plt.subplots(ncols=gridsize[0], nrows=gridsize[1], 
                          figsize=(10, 10))

for row in axarr:
    for ax in row:
        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.set_xlim(-xlim, xlim)
        ax.set_ylim(-ylim, ylim)

Hcs = [[None for i in range(gridsize[0])] for i in range(gridsize[1])]
Mrs = [[None for i in range(gridsize[0])] for i in range(gridsize[1])]
for f in listdir(root_path):
    gleaned = ng.glean(f)
    if gleaned['averaged']:
        print('Plotting %s' % f)
        x, y = int(gleaned['x']), int(gleaned['y'])
        ax = axarr[y, x]
        B, V = np.loadtxt(join(root_path, f), usecols=(0, 1), unpack=True, 
                          skiprows=1)
        B, V = tfmr((B, V), f)
        ax.plot(B, V, 'k-')

        try:
            Hc = tfms.Hc_of(B, V, fit_int=(thresh, max))
            Hcs[y][x] = Hc
            Mr = tfms.Mrem_of(B, V, fit_int=(thresh, max))
            Mrs[y][x] = Mr
            zs = np.zeros(3)
            ax.plot(zs, Mr, 'ro', ms=7)
            ax.plot(Hc, zs, 'ro', ms=7)
        except Exception as e:
            print('\t{}'.format(e))
            Hcs[y][x] = 0.0
            Mrs[y][x] = 0.0

plt.tight_layout(w_pad=0, h_pad=0)
plt.show()

Hcs = np.array([x[1] for row in Hcs for x in row]).reshape(5, 5)
Mrs = np.array([x[1] for row in Mrs for x in row]).reshape(5, 5)

# Hcs = np.rot90(Hcs, 2)
# Mrs = np.rot90(Mrs, 2)

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
