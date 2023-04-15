#!/usr/bin/env python3
# coding: utf-8

'''
read and correct data

usage: ./data.py [beam.pkl] [ped_file.json]

TODO: read in a config file for configurations
'''

import sys
import numpy as np
import scipy
import matplotlib.pyplot as plt
import mplhep as hep
from scipy.optimize import curve_fit
import pandas as pd
import statistics
import json

# constants
kLayers = 10    # number of total layers
kCells = 4      # number of cells in one layer

plt.style.use(hep.style.ROOT)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

fname = r'./BEAM_LG50_HG50_4k_R27.pkl'
if (len(sys.argv) > 1):
    fname = sys.argv[1]
df = pd.read_pickle(fname)
#set to 1 for 4k files, 2 for 8k files
ADCmult = 1

# plot raw spectra
xmax = {'LG': 4000, 'HG': 4000}
bad_channels = []
for gain in ["LG", "HG"]:
    print('processing {}'.format(gain))
    fig, axs=plt.subplots(nrows=kCells, ncols=kLayers, sharex=True, sharey=True, figsize=(40, 15))
    fig.suptitle('raw spectra ({})'.format(gain))
    fig.supxlabel("ADC Units")
    fig.supylabel("Counts")

    for i in range(round(len(df.columns)/2)):
        if i%kCells == 0: 
            print('layer {}'.format(i//kCells))

        channel = 'Ch_{:02d}_{}'.format(i, gain)
        values = getattr(df, channel)

        hist, bin_edges = np.histogram(np.array(values), range=(0, xmax[gain]*ADCmult), bins=100)
        bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

        # check bad channel with too little data points
        if (np.count_nonzero(hist)/100 < 0.2):
            bad_channels.append(i)

        ax = axs[i%kCells][i//kCells]
        ax.set_title('Ch_{:02d}'.format(i))
        ax.set_yscale("log")
        ax.scatter(bin_centres, hist)
       
    plt.tight_layout()
    plt.rcParams['savefig.bbox']='tight'
    plt.savefig('raw_data_{}.png'.format(gain))

for i in set(bad_channels):
    print("bad channel: {}".format(i), file=sys.stderr)

#Apply cuts, and create new lists to record spectra for each layer (4 channels at a time), 
#total energy spectra, and calibrated (to minimum ionizing particle units) and uncalibrated versions of both

# pedestals
ped_file = 'pedestal.json'
if (len(sys.argv) > 2):
    ped_file = sys.argv[2]
pedestal = json.load(open(ped_file, 'r'))
pedMeans = [pedestal['LG']['{}'.format(i)][0] for i in range(kLayers*kCells)]
pedStds = [pedestal['LG']['{}'.format(i)][1] for i in range(kLayers*kCells)]

layerADCs = [[],[],[],[],[],[],[],[],[],[]]
layerMIPs = [[],[],[],[],[],[],[],[],[],[]]
totADCs = []
totMIPs = []

#values taken from a previous cosmic data run, hard coded for now
mips = [52.74750277855359, 48.30860848773839, 53.943404039851835, 44.92190677955567, 61.26714324627709, 65.86727404494636,
50.49966238440961, 55.02522837553596, 46.61446015527332, 60.39973772203866, 55.30173491280392, 62.707398178412745,
50.482420120919734, 62.40987646935536, 59.02966599638661, 55.30173491280392, 123.13587491197416, 118.85827154485337,
93.36027551977364, 104.55347745998186, 88.72268957494947, 87.9317698337502, 99.4048611423608, 109.98290193288523,
102.39942115610283, 82.29288341793296, 93.36027551977364, 93.1310966604848, 120.5428145522235, 96.02936108638767,
107.29564320373284, 93.36027551977364, 78.16073077714876, 62.53205599751284, 90.81216227164441, 90.71800272849238,
109.00527397085415, 109.68782873235487, 85.36866495961932, 93.52544458950403]
mips = [i*ADCmult for i in mips]

maxEvts = 0 # number of max out event
for evtn in range(len(df)): 
    hasMax = 0
    if evtn%20000 == 0:
        print("event {}".format(evtn))

    totADC = 0
    totMIP = 0
    for l in range(0, kLayers):
        layerADC = 0
        layerMIP = 0
        for ch in range(l*kCells, (l+1)*kCells):
            ADC = getattr(df, "Ch_{:02d}_LG".format(ch))[evtn] 
            ADC_cor = ADC - pedMeans[ch]

            if ADC >= 8000:
                hasMax = 1

            if ADC_cor >= 3*pedStds[ch]:
                layerADC += ADC_cor
                totADC += ADC_cor
                
                MIP = ADC_cor/mips[ch]
                if MIP > 0.3:
                    layerMIP += MIP
                    totMIP += MIP
            
        layerMIPs[l].append(layerMIP)
        layerADCs[l].append(layerADC)

    totMIPs.append(totMIP)
    totADCs.append(totADC)
    
    if hasMax == 1:
        maxEvts += 1

print("number of max out event: {}".format(maxEvts), file=sys.stderr)

# plot calibrated total ADC/energy spectra, 
# this is where we get our detector resolution
maxE = {'ADC': 17000*ADCmult, 'MIP': 300*ADCmult}
yvalue = {'ADC': totADCs, 'MIP': totMIPs}
p0 = {'ADC': [20000., 5000., 2000.], 'MIP': [6000., 80., 50.]}
for var in ['ADC', 'MIP']:
    fig = plt.figure( figsize=(8, 6))
    fig.suptitle("Summed Energy")
    fig.supxlabel('Total Energy ({}s)'.format(var))
    fig.supylabel('Count')
    plt.rcParams['savefig.facecolor']='white'
    plt.rcParams['savefig.bbox']='tight'

    hist, bin_edges = np.histogram(np.array(yvalue[var]), bins=50, range=(0, maxE[var]))
    bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

    coeff, var_matrix = curve_fit(gauss, bin_centres, hist, p0=p0[var])
    hist_fit = gauss(np.linspace(0, maxE[var], 5000), *coeff)
    res = 100*abs(coeff[2])/coeff[1]
    print("{} resolution: {}".format(var, res))

    plt.plot(np.linspace(0, maxE[var], 5000), hist_fit, label='$\mu$=%2.0f\n$\sigma=$%2.0f\nResolution=%2.2f%%'%(coeff[1],abs(coeff[2]),res))
    plt.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist),fmt='o')
    plt.legend(fontsize=17,loc='upper right')
    plt.savefig('data_total_{}.png'.format(var))


# plot calibrated layer by layer energy spectra
# record median values for each layer
layerMed = {'ADC': [], 'MIP': []}
layerErr = {'ADC': [], 'MIP': []}
xmax = {'ADC': 5000*ADCmult, 'MIP': 80}
for var in ['ADC', 'MIP']:
    fig, axs=plt.subplots(nrows=2, ncols=5, sharex=True, sharey=True, figsize=(25, 10))
    fig.suptitle("Layer Energy Spectra ({}s)".format(var))
    fig.supxlabel("Layer Energy ({}s)".format(var))
    fig.supylabel("Counts")

    for l in range(kLayers):
        layerMed[var].append(statistics.median(layerMIPs[l]))
        layerErr[var].append(statistics.pstdev(layerMIPs[l]))

        hist, bin_edges = np.histogram(np.array(layerMIPs[l]), range=(0,80), bins=50)
        bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
        
        ax = axs[l//5][l%5]
        ax.set_title("Layer {:02d}".format(l))
        ax.set_yscale("log") 
        ax.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist), fmt='o')

    plt.rcParams['savefig.facecolor']='white'
    plt.rcParams['savefig.bbox']='tight'
    plt.tight_layout()    
    plt.savefig('cor_layer_{}.png'.format(var))

    #plot median energy deposited per layer. 
    fig = plt.figure(figsize=(8, 6))
    fig.suptitle("Layer Median Energy")
    fig.supxlabel('Layer')
    fig.supylabel('Median Energy ({}s)'.format(var))
    plt.rcParams['savefig.facecolor']='white'
    plt.rcParams['savefig.bbox']='tight'

    plt.errorbar(range(0, 10), layerMed[var], yerr=layerErr[var], fmt="o")
    plt.savefig('cor_layer_med_{}.png'.format(var))


#plot timestamp of measurement events, compare with next cell to see if different rates give different energies
#can also use this cell to ensure you are only selecting events when beam is off if you only want cosmic data

fig = plt.figure(figsize=(20, 16))
plt.rcParams['savefig.facecolor']='white'
plt.rcParams['savefig.bbox']='tight'
minTime = min(getattr(df,"TimeStamps"))
maxTime = max(getattr(df,"TimeStamps"))
times = []
for evtn in range(len(df)):
    times.append(getattr(df,"TimeStamps")[evtn] - minTime)

hist, bin_edges = np.histogram(np.array(getattr(df,"TimeStamps")), range=(minTime, maxTime), bins = round((maxTime-minTime)/1000000))
bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

plt.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist),fmt='o')
fig.suptitle("Event Times")
fig.supxlabel('Time')
fig.supylabel('Rate (Hz)')
plt.savefig('rate.png')

#plot average event energies over time, should be constant while beam is on, no matter the rate

tbins = 100
tenergy = [0]*tbins
tnums = [0]*tbins
energy = [0]*tbins

tcenters = []
current = (maxTime - minTime)/200
for i in range(tbins):
    tcenters.append(current)
    current += (maxTime - minTime)/100

for evtn in range(len(df)):
    evtTime = times[evtn]
    nbin = int(evtTime/(maxTime - minTime)*tbins)
    if nbin == tbins:
        nbin -= 1
    tenergy[nbin] += totMIPs[evtn]
    tnums[nbin] += 1

for i in range(tbins):
    if tnums[i] != 0:
        energy[i] = tenergy[i]/tnums[i]

plt.scatter(tcenters, energy)
fig.suptitle('Event Energy vs Time')
fig.supxlabel('Time')
fig.supylabel('Average Event Energy (MIPs)')
plt.savefig('MIP_rate.png')
