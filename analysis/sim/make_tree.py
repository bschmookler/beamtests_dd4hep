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
level = "sim"

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def usage():
    print(f'{sys.argv[0]}: -c config.cfg -o output.root -l level input.edm4hep.root')

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
        branch = 'HCALHits'
        amplitude_var = 'HCALHits.energy'
        if level == "reco":
            branch = 'HCALHitsReco'
            amplitude_var = 'HCALHitsDigi.amplitude'
        arrays = self.events.arrays()
        hit_cellID = arrays[f'{branch}.cellID']
        hit_x = arrays[f'{branch}.position.x']
        hit_y = arrays[f'{branch}.position.y']
        hit_z = arrays[f'{branch}.position.z']
        hit_energy = arrays[f'{branch}.energy']
        hit_amplitude = arrays[amplitude_var]

        hit_cellID_out = []
        hit_layer_out = []
        hit_energy_out = []
        hit_x_out = []
        hit_y_out = []
        hit_z_out = []
        hit_amplitude_out = []

        print('INFO -- reading tree')

        blocks = 4
        hexagon_layers = 7
        hexagon_cells_per_layer = blocks*7
        square_cells_per_layer = blocks*4
        for i in range(len(hit_cellID)):
            if (i%10000 == 0):
                print(f'\tevent {i}')

            cellID_b = []
            layer_b = []
            energy_b = []
            x_b = []
            y_b = []
            z_b = []
            amplitude_b = []
            for hi in range(len(hit_cellID[i])):
                system_id = (int(hit_cellID[i][hi]) & 0x0000FF)
                layer_id  = (int(hit_cellID[i][hi]) & 0x00FF00) >> 8
                cell_id   = (int(hit_cellID[i][hi]) & 0xFF0000) >> 16
                layer = hexagon_layers*(system_id-1) + (layer_id-1)

                cell = cell_id-1
                if (layer < hexagon_layers):
                    cell = cell + hexagon_cells_per_layer*layer
                else:
                    cell = cell + hexagon_layers*hexagon_cells_per_layer + square_cells_per_layer*(layer - hexagon_layers)

                energy = hit_energy[i][hi]*self.ADC2MIP
                amplitude = hit_amplitude[i][hi]

                cellID_b.append(cell)
                layer_b.append(layer)
                energy_b.append(energy) 
                x_b.append(hit_x[i][hi]) 
                y_b.append(hit_y[i][hi]) 
                z_b.append(hit_z[i][hi]) 
                amplitude_b.append(amplitude)

            if (len(hit_cellID[i]) > 0):
                hit_cellID_out.append(cellID_b)
                hit_layer_out.append(layer_b)
                hit_energy_out.append(energy_b)
                hit_x_out.append(x_b)
                hit_y_out.append(y_b)
                hit_z_out.append(z_b)
                hit_amplitude_out.append(amplitude_b)

        with ur.recreate(self.out_file) as fout:
            if level == "sim":
                fout['events'] = { 'hit': ak.zip({'cellID': hit_cellID_out, 'energy': hit_energy_out}) }
            elif level == "reco":
                fout['events'] = { 'hit': ak.zip({'cellID': hit_cellID_out, 'layer': hit_layer_out, 'energy': hit_energy_out, 'x': hit_x_out, 'y': hit_y_out, 'z': hit_z_out, 'amplitude': hit_amplitude_out}) }


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
        elif '-l' == sys.argv[i]:
            level = sys.argv[i+1]
            if level not in ["sim", "reco"]:
                print(f'ERROR -- unknown particle level: {level}')
                print(f'\tAvailbale choices: sim, reco')
                exit(5)
            print(f'INFO -- particle level: {level}')
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
