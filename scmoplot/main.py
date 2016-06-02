import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FixedLocator
import numpy as np
from os import listdir
from os.path import join
from .lvxml2dict import Cluster
from .namegleaner import NameGleaner
from .transformer import Transformer
from .transformations import (
    scale, 
    flatten_saturation, 
    center,
    wrapped_medfilt, 
    saturation_normalize, 
    Hc_of, 
    Mrem_of)
import re

""" TODO
  - Need a way to detect non-magnetic areas and normalize them differently...
     - Or don't normalize any curves and just compute the contrast range that
       the pcolor maps should use. This is what we will do if/when we convert
       to polarization rotation eventually.
"""

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
    tfmr.add(10, scale, params={'xsc': 0.1})
#    tfmr.add(20, flatten_saturation, 
#              params={'threshold': ps['thresh'], 'polarity': '+'})
#    tfmr.add(25, center)
    tfmr.add(30, wrapped_medfilt, params={'ks': ps['filt_ks']})
#    tfmr.add(40, saturation_normalize, params={'thresh': ps['thresh']})


    clust = Cluster(join(root_path, 'parameters.xml')).to_dict()
    gx, gy = (clust['Rows'], clust['Cols'])

    fig, axarr = plt.subplots(ncols=gx, nrows=gy, 
                              figsize=(10, 10))


    Hcs = [[None for i in range(gx)] for i in range(gy)]
    Mrs = [[None for i in range(gx)] for i in range(gy)]
    
    vmintemp = []
    vmaxtemp = []    
    for f in listdir(root_path):
        gleaned = ng.glean(f)
        if gleaned['averaged']:
            print('Plotting %s' % f)
            x, y = int(gleaned['x']), int(gleaned['y'])
            ax = axarr[y, x]
            B, V = np.loadtxt(join(root_path, f), usecols=(0, 1), unpack=True, 
                              skiprows=1)
      
            B, V = tfmr((B, V), f)

            vmintemp.append(min(V))
            print(min(V))
            vmaxtemp.append(max(V))                        
            
            ax.plot(B, V, 'k-')

            try:
                Hc = Hc_of(B, V, fit_int=(ps['thresh'], ps['max']))
                Hcs[y][x] = Hc
                Mr = Mrem_of(B, V, fit_int=(ps['thresh'], ps['max']))
                Mrs[y][x] = Mr
                zs = np.zeros(3)
                ax.plot(zs, Mr, 'ro', ms=7)
                ax.plot(Hc, zs, 'ro', ms=7)
            except Exception as e:
                print('\t{}'.format(e))
                Hcs[y][x] = 0.0
                Mrs[y][x] = 0.0

    vmin = min(vmintemp)
    vmax = max(vmaxtemp)
    dif=vmax-vmin
    vmin -= dif*.1
    vmax += dif*.1                
    
    for row in axarr:
        for ax in row:
            ax.xaxis.set_ticklabels([])
            ax.yaxis.set_ticklabels([])
            ax.set_xlim(-ps['xlim'], ps['xlim'])
         #   ax.set_ylim(-ps['ylim'], ps['ylim'])
            ax.set_ylim(vmin, vmax)
 

    plt.tight_layout(w_pad=0, h_pad=0)
    plt.show(block=True)

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
    plt.show(block=True)

if __name__ == '__main__':
    root_path = '/home/jji/Desktop/scanning_moke_test/trial1_5x5_BFO_test_sample'
    # root_path = r'C:\Users\Tor\Desktop\test\trial1_5x5_BFO_test_sample'
    ps = {}
    scmoplot(root_path, ps)
