#!/usr/bin/env python3
# coding: utf-8

'''
read and correct data

usage: ./data.py [beam.pkl] [ped_file.json]

TODO: read in a config file for configurations
'''

import os
import sys
import numpy as np
import scipy
import matplotlib.pyplot as plt
import mplhep as hep
from scipy.optimize import curve_fit
import pandas as pd
import statistics
import json
from ROOT import TFile, TH1F, TGraphErrors

# constants
kLayers = 10    # number of total layers
kCells = 4      # number of cells in one layer
ADCmult = 1     #set to 1 for 4k files, 2 for 8k files
#values taken from a previous cosmic data run, hard coded for now
mips = [52.74750277855359, 48.30860848773839, 53.943404039851835, 44.92190677955567, 61.26714324627709, 65.86727404494636,
50.49966238440961, 55.02522837553596, 46.61446015527332, 60.39973772203866, 55.30173491280392, 62.707398178412745,
50.482420120919734, 62.40987646935536, 59.02966599638661, 55.30173491280392, 123.13587491197416, 118.85827154485337,
93.36027551977364, 104.55347745998186, 88.72268957494947, 87.9317698337502, 99.4048611423608, 109.98290193288523,
102.39942115610283, 82.29288341793296, 93.36027551977364, 93.1310966604848, 120.5428145522235, 96.02936108638767,
107.29564320373284, 93.36027551977364, 78.16073077714876, 62.53205599751284, 90.81216227164441, 90.71800272849238,
109.00527397085415, 109.68782873235487, 85.36866495961932, 93.52544458950403]
mips = [i*ADCmult for i in mips]

plt.style.use(hep.style.ROOT)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def usage():
    print(f'{sys.argv[0]}: -c config.cfg data.pkl')

class ADC:
    data_file = ''
    conf_file = ''
    ped_file = ''
    config = {}
    pedestal = []
    ped_means = []
    ped_stds = []
    df = []

    layerADCs = [[],[],[],[],[],[],[],[],[],[]]
    layerMIPs = [[],[],[],[],[],[],[],[],[],[]]
    totADCs = []
    totMIPs = []

    MIP_cut = 0

    hist = {}   # root histogram
    graph = {}  # root graph
    fout = TFile("data.root", "recreate")

    def __init__(self, data_file, conf_file):
        self.data_file = data_file
        self.conf_file = conf_file
        # read the config file
        with open(conf_file, 'r') as fin:
            print(f'INFO -- the configuration:')
            for line in fin.readlines():
                key, value = line.split(':')
                key = key.strip()
                value = value.strip()
                self.config[key] = value
                print(f'\t{key}: {value}')

        # pedestals
        self.ped_file = self.config['pedestal_file']
        self.pedestal = json.load(open(self.ped_file, 'r'))
        self.ped_means = [self.pedestal['LG'][f'{i}'][0] for i in range(kLayers*kCells)]
        self.ped_stds = [self.pedestal['LG'][f'{i}'][1] for i in range(kLayers*kCells)]

        self.MIP_cut = float(self.config['MIP_cut'])

        self.df = pd.read_pickle(data_file)

    # plot raw ADC distribution
    def plot_raw_spectra(self):
        xmax = {'LG': 4000, 'HG': 4000}
        bad_channels = []
        for gain in ["LG", "HG"]:
            print(f'INFO -- processing {gain}')
            fig, axs=plt.subplots(nrows=kCells, ncols=kLayers, sharex=True, sharey=True, figsize=(40, 15), gridspec_kw = {'wspace': 0, 'hspace': 0})
            fig.suptitle(f'raw spectra ({gain})')
            fig.supxlabel("ADC Units")
            fig.supylabel("Counts")

            for i in range(round(len(self.df.columns)/2)):
                if i%kCells == 0: 
                    print('\tlayer {}'.format(i//kCells))

                channel = 'Ch_{:02d}_{}'.format(i, gain)
                values = getattr(self.df, channel)

                hist, bin_edges = np.histogram(np.array(values), range=(0, xmax[gain]*ADCmult), bins=100)
                bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

                # check bad channel with too little data points
                if (np.count_nonzero(hist)/100 < 0.2):
                    bad_channels.append(i)

                ax = axs[i%kCells][i//kCells]
                ax.set_title('Ch_{:02d}'.format(i), y=0.8)
                ax.set_yscale("log")
                ax.scatter(bin_centres, hist)
                # ax.label_outer()
               
            plt.tight_layout()
            plt.rcParams['savefig.bbox']='tight'
            plt.savefig(f'raw_data_{gain}.png')

        for i in set(bad_channels):
            print(f"WARNING -- bad channel: {i}", file=sys.stderr)

    ######################
    def read_data(self):
        '''
        Apply cuts, and create new lists to record spectra for each layer, 
        total energy spectra, and calibrated (to minimum ionizing particle units) 
        and uncalibrated versions of both
        '''
        maxEvts = 0 # number of max out event

        for l in range(0, kLayers):
            self.hist[f'layer{l}_MIP'] = TH1F(f'layer{l}_energy', f'Layer {l} energy (MIPs)', 100, 0, 80)

        self.hist["total_MIP"] = TH1F("event_energy", "Total Energy (MIPs)", 100, 0, 300)

        print(f'INFO -- reading events:')
        for evtn in range(len(self.df)): 
            hasMax = 0
            if evtn%20000 == 0:
                print(f"\tevent {evtn}")

            totADC = 0
            totMIP = 0
            for l in range(0, kLayers):
                layerADC = 0
                layerMIP = 0
                for ch in range(l*kCells, (l+1)*kCells):
                    ADC = getattr(self.df, "Ch_{:02d}_LG".format(ch))[evtn] 
                    ADC_cor = ADC - self.ped_means[ch]

                    if ADC >= 8000:
                        hasMax = 1

                    if ADC_cor >= 3*self.ped_stds[ch]:
                        layerADC += ADC_cor
                        totADC += ADC_cor
                        
                        MIP = ADC_cor/mips[ch]
                        if MIP > self.MIP_cut:
                            layerMIP += MIP
                            totMIP += MIP
                    
                self.layerMIPs[l].append(layerMIP)
                self.layerADCs[l].append(layerADC)
                self.hist[f'layer{l}_MIP'].Fill(layerMIP)

            self.totMIPs.append(totMIP)
            self.totADCs.append(totADC)
            self.hist['total_MIP'].Fill(totMIP)
            
            if hasMax == 1:
                maxEvts += 1

        print(f'WARNING -- number of max out event: {maxEvts}')

        self.fout.cd()
        for l in range(0, kLayers):
            self.hist[f'layer{l}_MIP'].Write()
        self.hist['total_MIP'].Write()


    ######################
    def plot_cor_spectra(self):
        # total ADC/MIP: this is where we get our detector resolution
        maxE = {'ADC': 17000*ADCmult, 'MIP': 300*ADCmult}
        yvalue = {'ADC': self.totADCs, 'MIP': self.totMIPs}
        p0 = {'ADC': [20000., 5000., 2000.], 'MIP': [6000., 80., 50.]}
        for var in ['ADC', 'MIP']:
            fig = plt.figure( figsize=(8, 6) )
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
            print(f'{var} resolution: {res}')

            plt.plot(np.linspace(0, maxE[var], 5000), hist_fit, label='$\mu$=%2.0f\n$\sigma=$%2.0f\nResolution=%2.2f%%'%(coeff[1], abs(coeff[2]), res))
            plt.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist), fmt='o')
            plt.legend(fontsize=17, loc='upper right')
            plt.savefig(f'data_total_{var}.png')

        # layer ADC/MIP
        self.graph['layer_med_MIP'] = TGraphErrors()
        self.graph['layer_med_MIP'].SetMarkerStyle(20)
        self.graph['layer_med_MIP'].SetName('layer_med_energy')
        self.graph['layer_med_MIP'].SetTitle('Layer Median Energy (MIPs)')

        layerMed = {'ADC': [], 'MIP': []}
        layerErr = {'ADC': [], 'MIP': []}
        xmax = {'ADC': 5000*ADCmult, 'MIP': 80}
        for var in ['ADC', 'MIP']:
            fig, axs=plt.subplots(nrows=2, ncols=5, sharex=True, sharey=True, figsize=(25, 10), gridspec_kw = {'wspace': 0, 'hspace': 0})
            fig.suptitle("Layer Energy Spectra ({}s)".format(var))
            fig.supxlabel("Layer Energy ({}s)".format(var))
            fig.supylabel("Counts")

            for l in range(kLayers):
                layerMed[var].append(statistics.median(self.layerMIPs[l]))
                layerErr[var].append(statistics.pstdev(self.layerMIPs[l]))

                hist, bin_edges = np.histogram(np.array(self.layerMIPs[l]), range=(0,80), bins=50)
                bin_centres = (bin_edges[:-1] + bin_edges[1:])/2
                
                ax = axs[l//5][l%5]
                ax.set_title(f'Layer {l}', y=0.8)
                ax.set_yscale("log") 
                ax.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist), fmt='o')

            if 'MIP' == var:
                for l in range(kLayers):
                    self.graph['layer_med_MIP'].SetPoint(l+1, l+1, layerMed[var][l])
                    self.graph['layer_med_MIP'].SetPointError(l+1, 0, layerErr[var][l])
                self.fout.cd()
                self.graph['layer_med_MIP'].Write()

            plt.rcParams['savefig.facecolor']='white'
            plt.rcParams['savefig.bbox']='tight'
            plt.tight_layout()    
            plt.savefig(f'cor_layer_{var}.png')

            # median energy deposited per layer. 
            fig = plt.figure(figsize=(8, 6))
            fig.suptitle("Layer Median Energy")
            fig.supxlabel('Layer')
            fig.supylabel('Median Energy ({}s)'.format(var))
            plt.rcParams['savefig.facecolor']='white'
            plt.rcParams['savefig.bbox']='tight'

            plt.errorbar(range(0, 10), layerMed[var], yerr=layerErr[var], fmt="o")
            plt.savefig(f'cor_layer_med_{var}.png')

        self.fout.Close()

#plot timestamp of measurement events, compare with next cell to see if different rates give different energies
#can also use this cell to ensure you are only selecting events when beam is off if you only want cosmic data

    def plot_rate(self):
        fig = plt.figure(figsize=(20, 16))
        plt.rcParams['savefig.facecolor']='white'
        plt.rcParams['savefig.bbox']='tight'
        minTime = min(getattr(self.df, "TimeStamps"))
        maxTime = max(getattr(self.df, "TimeStamps"))
        times = []
        for evtn in range(len(self.df)):
            times.append(getattr(self.df,"TimeStamps")[evtn] - minTime)

        hist, bin_edges = np.histogram(np.array(getattr(self.df, "TimeStamps")), range=(minTime, maxTime), bins = round((maxTime-minTime)/1000000))
        bin_centres = (bin_edges[:-1] + bin_edges[1:])/2

        plt.errorbar(bin_centres, y=hist, yerr=np.sqrt(hist), fmt='o')
        fig.suptitle("Event Times")
        fig.supxlabel('Time')
        fig.supylabel('Rate (Hz)')
        plt.savefig('rate.png')

        # average event energies over time, should be constant while beam is on, no matter the rate
        tbins = 100
        tenergy = [0]*tbins
        tnums = [0]*tbins
        energy = [0]*tbins

        tcenters = []
        current = (maxTime - minTime)/200
        for i in range(tbins):
            tcenters.append(current)
            current += (maxTime - minTime)/100

        for evtn in range(len(self.df)):
            evtTime = times[evtn]
            nbin = int(evtTime/(maxTime - minTime)*tbins)
            if nbin == tbins:
                nbin -= 1
            tenergy[nbin] += self.totMIPs[evtn]
            tnums[nbin] += 1

        for i in range(tbins):
            if tnums[i] != 0:
                energy[i] = tenergy[i]/tnums[i]

        plt.scatter(tcenters, energy)
        fig.suptitle('Event Energy vs Time')
        fig.supxlabel('Time')
        fig.supylabel('Average Event Energy (MIPs)')
        plt.savefig('MIP_rate.png')


if __name__ == '__main__':
    # read in command line arguments
    data_file=''
    conf_file=''
    i=1
    while i<len(sys.argv):
        if '-h' == sys.argv[i]:
            usage()
            exit(0)
        elif '-c' == sys.argv[i]:
            conf_file=sys.argv[i+1]
            print(f'INFO -- using config file: {config}')
            i+=1
        else:
            data_file = sys.argv[1]
            print(f'INFO -- will process {data_file}')
        i+=1

    if '' == conf_file:
        print(f'WARNING -- no config file specified, use the default one: config.cfg')
        conf_file='config.cfg'
    if '' == data_file:
        print(f'FATAL -- no data file specified')
        exit(2)

    for f in [conf_file, data_file]:
        if not os.path.isfile(f):
            print(f'FATAL -- file doesn\'t exist: {f}')
            exit(4)

    data_ADC = ADC(data_file, conf_file)
    data_ADC.plot_raw_spectra()
    data_ADC.read_data()
    data_ADC.plot_cor_spectra()
    data_ADC.plot_rate()
