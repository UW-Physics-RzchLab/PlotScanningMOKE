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
import scipy

""" TODO
  - Need a way to detect non-magnetic areas and normalize them differently...
     - Or don't normalize any curves and just compute the contrast range that
       the pcolor maps should use. This is what we will do if/when we convert
       to polarization rotation eventually.
"""


xlim, ylim = 10.0, 1.1
thresh, max = 7, 10  # thresh: where to start fits, max: highest field
filt_ks = 157

default_ps = {
    'xlim': 10.0,
    'ylim': 1.1,
    'thresh': 7,
    'max': 10,
    'filt_ks': 157
}

def scmoplot(root_path, user_ps):

    ps = dict(default_ps)
    ps.update(user_ps)

    ng = NameGleaner(scan=r'scan=(\d+)', x=r'x=(\d+)', y=r'y=(\d+)',
                     averaged=r'(averaged)')

    tfmr = Transformer(gleaner=ng)
    tfmr.add(10, tfms.scale, params={'xsc': 0.1})
    tfmr.add(20, tfms.flatten_saturation, 
              params={'threshold': ps['thresh'], 'polarity': '+'})
    tfmr.add(25, tfms.center)
    tfmr.add(30, tfms.wrapped_medfilt, params={'ks': ps['filt_ks']})
    tfmr.add(40, tfms.saturation_normalize, params={'thresh': ps['thresh']})
    
    tfmr2 = Transformer(gleaner=ng)
    tfmr2.add(10, tfms.scale, params={'xsc': 0.1})
    tfmr2.add(30, tfms.wrapped_medfilt, params={'ks': ps['filt_ks']})

    clust = Cluster(join(root_path, 'parameters.xml')).to_dict()
    gx, gy = (clust['Rows'], clust['Cols'])

    fig, axarr = plt.subplots(ncols=gx, nrows=gy, 
                              figsize=(10, 10))

    for row in axarr:
        for ax in row:
            ax.xaxis.set_ticklabels([])
            ax.yaxis.set_ticklabels([])
           # ax.set_xlim(-ps['xlim'], ps['xlim'])
            #ax.set_ylim(-ps['ylim'], ps['ylim'])

    Hcs = [[None for i in range(gx)] for i in range(gy)]
    Mrs = [[None for i in range(gx)] for i in range(gy)]
    for f in listdir(root_path):
        gleaned = ng.glean(f)
        if gleaned['averaged']:
            print('Plotting %s' % f)
            x, y = int(gleaned['x']), int(gleaned['y'])
            ax = axarr[y, x]
            Bi, Vi = np.loadtxt(join(root_path, f), usecols=(0, 1), unpack=True, 
                              skiprows=1)
            B,V = tfmr((Bi,Vi),f)
            B2, V2 = tfmr2((Bi, Vi), f)
            cB2, cV2 = tfms.clean(B2,V2)
            
            tfms.x0slope(B,V)            
            
            lsat,rsat=tfms.sat_field(B2,V2)
            
            ax.plot(B,V)
            ax.plot(np.arange(len(B)),np.zeros((len(B))))
            ax.plot(np.arange(len(B)),np.ones((len(B))))

#            ax.plot(cB2[lsat],cV2[lsat],'b*')
#            ax.plot(cB2[rsat],cV2[rsat],'r*')
#
#            ax.plot(cB2,cV2,'k-')

#            try:
#                Hc = tfms.Hc_of(B, V, fit_int=(ps['thresh'], ps['max']))
#                Hcs[y][x] = Hc
#                Mr = tfms.Mrem_of(B, V, fit_int=(ps['thresh'], ps['max']))
#                Mrs[y][x] = Mr
#                zs = np.zeros(3)
#                ax.plot(zs, Mr, 'ro', ms=7)
#                ax.plot(Hc, zs, 'ro', ms=7)
#            except Exception as e:
#                print('\t{}'.format(e))
#                Hcs[y][x] = 0.0
#                Mrs[y][x] = 0.0

    plt.tight_layout(w_pad=0, h_pad=0)
    plt.show()

    Hcs = np.array([x[1] for row in Hcs for x in row]).reshape(gy, gx)
    Mrs = np.array([x[1] for row in Mrs for x in row]).reshape(gy, gx)

    gs = GridSpec(10, 10)
    ax0 = plt.subplot(gs[0:9, :5])
    ax1 = plt.subplot(gs[9, :5])
    ax2 = plt.subplot(gs[0:9, 5:])
    ax3 = plt.subplot(gs[9, 5:])
    fig = ax0.get_figure()
    fig.set_size_inches(12, 8)

# Plot Hc pcolor map
    n = Normalize(vmin=0.0, vmax=5.0, clip=True)
    res = ax0.pcolor(Hcs, cmap='afmhot', norm=n, edgecolors='k')
    plt.colorbar(res, cax=ax1, orientation='horizontal', ticks=(0, 2.5, 5))

# Plot Mr pcolor map
    n = Normalize(vmin=0.0, vmax=1.0, clip=True)
    res = ax2.pcolor(Mrs, cmap='afmhot', norm=n, edgecolors='k')
    plt.colorbar(res, cax=ax3, orientation='horizontal', ticks=(0, 0.5, 1))

    ax0.set_title('Hc (mT)')
    ax0.set_aspect('equal', adjustable='box')
    ax2.set_title('Mrem/Msat')
    ax2.set_aspect('equal', adjustable='box')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    root_path = '/home/jji/Desktop/scanning_moke_test/trial1_5x5_BFO_test_sample'
    # root_path = r'C:\Users\Tor\Desktop\test\trial1_5x5_BFO_test_sample'
    ps = {}
    scmoplot(root_path, ps)
