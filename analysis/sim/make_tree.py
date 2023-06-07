#!/usr/bin/env python3
# coding: utf-8

'''
make tree from edm4hep.root files

usage: ./make_tree.py -c config.cfg [-o output.root] input.edm4hep.root

'''

import os
import sys
import numpy as np
import scipy
import statistics
import uproot as ur
import awkward as ak

# constants
kLayers = 10    # number of total layers
kCells = 4      # number of cells in one layer
# ADC2MIP = 1/0.000465; # 0.3 cm

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def usage():
    print(f'{sys.argv[0]}: -c config.cfg -o output.root input.edm4hep.root')

class ADC:
    data_file = ''
    conf_file = ''
    config = {}

    fout = "out.root"

    ADC2MIP = 1

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
                    ''' comments '''
                    continue
                key, value = line.split(':')
                key = key.strip()
                value = value.strip()
                self.config[key] = value
                print(f'\t{key}: {value}')

        if ('ADC2MIP' in self.config):
            self.ADC2MIP = eval(self.config['ADC2MIP'])

        self.events = ur.open(f'{data_file}:events')

    ###############################
    def make_tree(self):
        arrays = self.events.arrays()
        hit_cellID = arrays["HCALHits.cellID"]
        hit_x = arrays["HCALHits.position.x"]
        hit_y = arrays["HCALHits.position.y"]
        hit_energy = arrays['HCALHits.energy']

        hit_cellID_out = []
        hit_energy_out = []

        print('INFO -- reading tree')

        for i in range(len(hit_cellID)):
            if (i%10000 == 0):
                print(f'\tevent {i}')

            cellID_b = []
            energy_b = []
            for hi in range(len(hit_cellID[i])):
                system_id = (int(hit_cellID[i][hi]) & 0xFF)
                layer_id = (int(hit_cellID[i][hi]) & 0xFF00) >> 8
                layer = 4*(system_id-1) + layer_id - 1
                cell = 4*layer + 2*(hit_y[i][hi] < 0) + (hit_x[i][hi] > 0)

                energy = hit_energy[i][hi]*self.ADC2MIP

                cellID_b.append(cell)
                energy_b.append(energy) 

            if (len(hit_cellID[i]) > 0):
                hit_cellID_out.append(cellID_b)
                hit_energy_out.append(energy_b)


        with ur.recreate(self.out_file) as fout:                            
             fout['events'] = { 'hit': ak.zip({'cellID': hit_cellID_out, 'energy': hit_energy_out}) }


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

    for f in [data_file, conf_file]:
        if not os.path.isfile(f):
            print(f'FATAL -- file doesn\'t exist: {f}')
            exit(4)

    data_ADC = ADC(data_file, conf_file, out_file)
    data_ADC.make_tree()
