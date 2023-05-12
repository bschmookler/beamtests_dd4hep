#!/usr/bin/env python3
# coding: utf-8

'''
read and correct data

usage: ./plot.py [-c config.cfg] [-o output.root] input.edm4hep.root

'''

import os
import sys
import numpy as np
import scipy
import statistics
import uproot as ur
from ROOT import TFile, TTree, TH1F, TH2F, TGraphErrors, TCanvas
from ROOT import gROOT, TGaxis, gStyle, gPad

# constants
kLayers = 10    # number of total layers
kCells = 4      # number of cells in one layer
# ADC2MIP = 1/0.000465; # 0.3 cm
ADC2MIP = 1/0.000975;   # 0.62 cm

gROOT.SetBatch(1)
TGaxis.SetMaxDigits(3)
gStyle.SetOptStat(111110)
gStyle.SetOptFit(111)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def usage():
    print(f'{sys.argv[0]}: -c config.cfg -o output.root input.edm4hep.root')

class ADC:
    data_file = ''
    conf_file = ''
    config = {}

    layerMIPs = [[],[],[],[],[],[],[],[],[],[]]
    eventMIPs = []

    MIP_cut = 0

    h1 = {}     # 1D histogram
    h2 = {}     # 2D hist
    h1_layer = []
    h1_cell = []
    h1['hit_layer_id'] = TH1F('hit_layer_id', 'Layer id', 20, 0, 20)
    h1['hit_cell_id'] = TH1F('hit_cell_id', 'cell id', 45, 0, 45);
    h1['hit_x'] = TH1F('hit_x', 'x', 100, -50, 50);
    h1['hit_y'] = TH1F('hit_y', 'y', 100, -50, 50);
    h1['hit_z'] = TH1F('hit_z', 'z', 60, 5000, 5300);
    h1['hit_energy'] = TH1F('hit_energy', 'Hit energy (MIPs)', 100, 0, 0.003*ADC2MIP);
    h1['hit_event_energy'] = TH1F('event_energy', 'Event Energy (MIP)', 100, 0, 300);
    for l in range(kLayers):
        h1_layer.append(TH1F(f'layer{l}_energy', f'Layer{l} Energy (MIPs)', 100, 0, 80)) 
    for i in range(kLayers*kCells):
        h1_cell.append(TH1F(f'cell{i}_energy', f'Cell{i} Energy (MIPs)', 100, 0, 40)) 

    h2['hit_x_vs_y'] = TH2F('hit_x_vs_y', 'x vs y', 100, -50, 50, 100, -50, 50);
    h2['hit_x_vs_z'] = TH2F('hit_x_vs_z', 'x vs z', 100, -50, 50, 100, 5000, 5300);
    h2['hit_y_vs_z'] = TH2F('hit_y_vs_z', 'y vs z', 100, -50, 50, 100, 5000, 5300);

    graph = {}  # root graph
    graph['layer_med_energy'] = TGraphErrors()
    graph['layer_med_energy'].SetMarkerStyle(20)
    graph['layer_med_energy'].SetName('layer_med_energy')
    graph['layer_med_energy'].SetTitle('Layer median energy (MIPs)')

    events = []

    fout = TFile()

    def __init__(self, data_file, conf_file, out_file):
        self.data_file = data_file
        self.conf_file = conf_file
        self.out_file = out_file
        # read the config file
        with open(conf_file, 'r') as fin:
            print(f'INFO -- the configuration:')
            for line in fin.readlines():
                key, value = line.split(':')
                key = key.strip()
                value = value.strip()
                self.config[key] = value
                print(f'\t{key}: {value}')

        self.MIP_cut = float(self.config['MIP_cut'])

        self.events = ur.open(f'{data_file}:events')
        self.fout = TFile(out_file, 'recreate')

    ###############################
    def read_data(self):
        arrays = self.events.arrays()
        hit_cellID = arrays["HCALHits.cellID"]
        hit_x = arrays['HCALHits.position.x']
        hit_y = arrays['HCALHits.position.y']
        hit_z = arrays['HCALHits.position.z']
        hit_energy = arrays['HCALHits.energy']
        # hit_layer_id = arrays['HCALHits.cellID']

        zero_event = 0
        print('INFO -- reading tree')
        for i in range(len(hit_x)):
            if (i%10000 == 0):
                print(f'\tevent {i}')
            event_energy = 0
            layer_energy = []
            for l in range(kLayers):
                layer_energy.append(0)

            for hi in range(len(hit_energy[i])):
                event_energy += hit_energy[i][hi]*ADC2MIP

            if (event_energy > self.MIP_cut):
                self.eventMIPs.append(event_energy)
                self.h1['hit_event_energy'].Fill(event_energy)

                for hi in range(len(hit_energy[i])):
                    system_id = (hit_cellID[i][hi] & 0xFF)
                    layer_id = (hit_cellID[i][hi] & 0xFF00) >> 8
                    layer = 4*(system_id-1) + layer_id - 1
                    cell = 4*layer + 2*(hit_y[i][hi] < 0) + (hit_x[i][hi] > 0)
                    energy = hit_energy[i][hi]*ADC2MIP
                    if (1 == cell) or (7 == cell):
                        continue

                    layer_energy[layer] += energy
                    self.h1_cell[cell].Fill(energy)
                    self.h1['hit_layer_id'].Fill(2*layer+1)
                    self.h1['hit_cell_id'].Fill(cell);
                    self.h1['hit_energy'].Fill(energy);
                    self.h1['hit_x'].Fill(hit_x[i][hi]);
                    self.h1['hit_y'].Fill(hit_y[i][hi]);
                    self.h1['hit_z'].Fill(hit_z[i][hi]);
                    self.h2['hit_x_vs_y'].Fill(hit_x[i][hi], hit_y[i][hi]);
                    self.h2['hit_x_vs_z'].Fill(hit_x[i][hi], hit_z[i][hi]);
                    self.h2['hit_y_vs_z'].Fill(hit_y[i][hi], hit_z[i][hi]);

                for l in range(kLayers):
                    self.layerMIPs[l].append(layer_energy[l])
                    self.h1_layer[l].Fill(layer_energy[l])
            else:
                zero_event+=1

        print(f'INFO -- zero energy event: {zero_event}')

        self.h1['hit_event_energy'].Fit('gaus')
        delta = self.h1['hit_event_energy'].GetFunction('gaus').GetParameter(2)
        print(f'INFO -- Energy resolution: {delta} MIPs')

        for l in range(kLayers):
            self.graph['layer_med_energy'].SetPoint(l+1, l+1, statistics.median(self.layerMIPs[l]))
            self.graph['layer_med_energy'].SetPointError(l+1, 0, statistics.pstdev(self.layerMIPs[l]))

    ###############################
    def plot(self):
        c = TCanvas('c', 'c', 800, 800)
        for (var, hist) in self.h1.items():
            hist.Draw()
            c.SaveAs(f'{var}.png')
            self.fout.cd()
            hist.Write()
        for (var, hist) in self.h2.items():
            hist.Draw()
            c.SaveAs(f'{var}.png')
            self.fout.cd()
            hist.Write()

        self.graph['layer_med_energy'].Draw('AP')
        c.SaveAs('layer_med_energy.png')

        c = TCanvas('c', 'c', 4000, 1600)
        c.Divide(5, 2)
        for l in range(kLayers):
            c.cd(l+1)
            gPad.SetLogy()
            self.h1_layer[l].Draw()

            self.fout.cd()
            self.h1_layer[l].Write()
        c.SaveAs('hit_layer_energy.png')

        c = TCanvas('c', 'c', 500*kLayers, 500*kCells)
        c.Divide(kLayers, kCells)
        for i in range(kLayers*kCells):
            c.cd(10*(i%4) + i//4 + 1)
            gPad.SetLogy()
            self.h1_cell[i].Draw()

            self.fout.cd()
            self.h1_cell[i].Write()
        c.SaveAs('hit_cell_energy.png')


        self.fout.cd()
        self.graph['layer_med_energy'].Write()

        self.fout.Write()
        self.fout.Close()

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
    data_ADC.read_data()
    data_ADC.plot()
