#!/usr/bin/env python3
# coding: utf-8

'''
make tree from the pkl file 

usage: ./make_tree.py [beam.pkl] [-c config.cfg] -o output.root 

'''

import os
import sys
import pandas as pd
import json
import awkward as ak
import uproot

# constants
kLayers = 10    # number of total layers
kCells = 4      # number of cells in one layer
ADCmult = 1     #set to 1 for 4k files, 2 for 8k files
#values taken from a previous cosmic data run, hard coded for now
mips = [
    52.74750277855359,  48.30860848773839,  53.943404039851835, 44.92190677955567, 
    61.26714324627709,  65.86727404494636,  50.49966238440961,  55.02522837553596, 
    46.61446015527332,  60.39973772203866,  55.30173491280392,  62.707398178412745,
    50.482420120919734, 62.40987646935536,  59.02966599638661,  55.30173491280392, 
    123.13587491197416, 118.85827154485337, 93.36027551977364,  104.55347745998186, 
    88.72268957494947,  87.9317698337502,   99.4048611423608,   109.98290193288523,
    102.39942115610283, 82.29288341793296,  93.36027551977364,  93.1310966604848, 
    120.5428145522235,  96.02936108638767,  107.29564320373284, 93.36027551977364, 
    78.16073077714876,  62.53205599751284,  90.81216227164441,  90.71800272849238,
    109.00527397085415, 109.68782873235487, 85.36866495961932,  93.52544458950403, ]
mips = [i*ADCmult for i in mips]

def usage():
    print(f'{sys.argv[0]} -c config.cfg [-o output.root] data.pkl')

class ADC:
    data_file = ''
    conf_file = ''
    out_file = ''
    ped_file = ''
    config = {}
    pedestal = []
    ped_means = []
    ped_stds = []
    df = []

    MIP_cut = 0

    def __init__(self, data_file, conf_file, out_file):
        self.data_file = data_file
        self.conf_file = conf_file
        self.out_file = out_file
        # read the config file
        with open(conf_file, 'r') as fin:
            print(f'INFO -- the configuration:')
            for line in fin.readlines():
                line = line.strip()
                if line.startswith('#'):
                    continue
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

    ######################
    def make_tree(self):
        ''' Apply cuts, and record them in a ROOT tree '''

        nHit = []
        hit_cellID = []
        hit_energy = []

        print(f'INFO -- reading events:')
        for evtn in range(len(self.df)): 
            if evtn%20000 == 0:
                print(f"\tevent {evtn}")

            n = 0
            cellID = []
            energy = []
            for ch in range(0, kLayers*kCells):
                ADC = getattr(self.df, "Ch_{:02d}_LG".format(ch))[evtn] 
                ADC_cor = ADC - self.ped_means[ch]
                if ADC_cor >= 3*self.ped_stds[ch]:
                    MIP = ADC_cor/mips[ch]
                    if MIP > self.MIP_cut:
                        # a signal hit
                        n+=1
                        cellID.append(ch)
                        energy.append(MIP)
            if (n > 0):
                nHit.append(n)
                hit_cellID.append(cellID)
                hit_energy.append(energy)

        with uproot.recreate(self.out_file) as fout:
            fout['events'] = { 'hit': ak.zip({'cellID': hit_cellID, 'energy': hit_energy}) }

if __name__ == '__main__':
    # read in command line arguments
    data_file=''
    conf_file=''
    out_file =''
    i=1
    while i<len(sys.argv):
        if '-h' == sys.argv[i]:
            usage()
            exit(0)
        elif '-c' == sys.argv[i]:
            conf_file=sys.argv[i+1]
            print(f'INFO -- using config file: {conf_file}')
            i+=1
        elif '-o' == sys.argv[i]:
            out_file = sys.argv[i+1]
            print(f'INFO -- output root file: {out_file}')
            i+=1
        else:
            data_file = sys.argv[i]
            print(f'INFO -- will process {data_file}')
        i+=1

    if '' == data_file:
        print(f'FATAL -- no data file specified')
        exit(2)
    if '' == conf_file:
        print(f'WARNING -- no config file specified, use the default one: config.cfg')
        conf_file='config.cfg'
    if '' == out_file:
        print(f'WARNING -- no output file specified, use the default one: output.root')
        out_file='output.root'

    for f in [conf_file, data_file]:
        if not os.path.isfile(f):
            print(f'FATAL -- file doesn\'t exist: {f}')
            exit(4)

    data_ADC = ADC(data_file, conf_file, out_file)
    data_ADC.make_tree()
