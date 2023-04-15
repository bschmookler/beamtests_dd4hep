#!/usr/bin/env python3
# coding: utf-8

'''
This script will read the random trigger (pedestal) data and extract the pedestal
value for each channel.
'''

import sys
import numpy as np
import scipy
import matplotlib.pyplot as plt
import mplhep as hep
from scipy.optimize import curve_fit
import pandas as pd
import json

plt.style.use(hep.style.ROOT)

#random trigger data
fname = r'./PTRIG_LG50_HG50_4k_R28.pkl'
if (len(sys.argv) > 1):
    fname = sys.argv[1]

df = pd.read_pickle(fname)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

# plot random trigger spectra for each low/high gain channel. 
# Fit to gaussian and record pedestals for cuts later
xmax = {'LG': 100, 'HG': 400}
sigma = {'LG': 3, 'HG': 50}
fitrange = {'LG': 100, 'HG': 160}
pedestal = {'LG': {}, 'HG': {}}
for gain in ["LG", "HG"]:
    print('processing {}'.format(gain))
    fig, axs=plt.subplots(nrows=4, ncols=10, sharex=True, sharey=True, figsize=(40, 15))
    fig.suptitle('pedestal spectra ({})'.format(gain))
    fig.supxlabel("ADC Units")
    fig.supylabel("Counts")

    pedMeans = []
    pedStds = []

    for i in range(round(len(df.columns)/2)):
        if i%4 == 0: 
            print('layer {}'.format(i//4))

        channel = 'Ch_{:02d}_{}'.format(i, gain)
        values = getattr(df, channel)

        hist, bin_edges = np.histogram(np.array(values), range=(0, xmax[gain]), bins=xmax[gain])
        bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
        
        p0 = [max(hist), sum(values)/len(values), sigma[gain]]   # parameter initialization
        coeff, var_matrix = curve_fit(gauss, bin_centres, hist, p0=p0)
        hist_fit = gauss(np.linspace(0, fitrange[gain], 5000), *coeff)

        ax = axs[i%4][i//4]
        ax.set_title('Ch_{:02d}'.format(i))
        ax.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist), fmt='o')
        ax.plot(np.linspace(0, fitrange[gain], 5000), hist_fit, label='$\mu$=%2.0f\n$\sigma=$%2.0f'%(coeff[1],abs(coeff[2])))
        ax.legend(fontsize=17, loc='upper right')
     
        pedMeans.append(coeff[1])
        pedStds.append(abs(coeff[2]))

    plt.tight_layout()
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.savefig('ped_spectra_{}.png'.format(gain))

    # plot pedestals means and stds for low gain
    fig = plt.figure(figsize=(8, 6))
    fig.supxlabel('Channel')
    fig.supylabel('Pedestal (ADC Units)')
    fig.suptitle("{} Pedestal".format(gain))
    plt.scatter(range(0,40), pedMeans)
    plt.errorbar(range(0,40), pedMeans, yerr=pedStds, fmt="o")
    plt.savefig('pedestal_{}.png'.format(gain))

    # json output
    pedestal[gain] = {i: (pedMeans[i], pedStds[i]) for i in range(40)}

with open('pedestal.json', 'w') as fout:
    fout.write(json.dumps(pedestal))
