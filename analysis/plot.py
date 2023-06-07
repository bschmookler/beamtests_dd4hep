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
    h1['hit_cell_id'] = TH1F('hit_cell_id', 'Hit Cell ID', 45, 0, 45)
    h1['hit_layer_id'] = TH1F('hit_layer_id', 'Hit Layer ID', 20, 0, 20)
    h1['hit_x'] = TH1F('hit_x', 'Hit X;mm', 80, -40, 40)
    h1['hit_y'] = TH1F('hit_y', 'Hit Y;mm', 80, -40, 40)
    h1['hit_energy'] = TH1F('hit_energy', 'Hit Energy;MIP', 100, 0, 40)

    for i in range(kLayers*kCells):
        h1[f'cell{i}_energy'] = TH1F(f'cell{i}_energy', f'Cell{i} Energy;MIP', 100, 0, 40)

    for l in range(kLayers):
        h1[f'layer{l}_x'] = TH1F(f'layer{l}_x', f'Layer{l} X;mm', 80, -40, 40)
        h1[f'layer{l}_y'] = TH1F(f'layer{l}_y', f'Layer{l} Y;mm', 80, -40, 40)
        h1[f'layer{l}_energy'] = TH1F(f'layer{l}_energy', f'Layer{l} Energy;MIP', 100, 0, 80)

    h1['event_x'] = TH1F('event_x', 'Event X;mm', 80, -40, 40)
    h1['event_y'] = TH1F('event_y', 'Event Y;mm', 80, -40, 40)
    h1['event_energy'] = TH1F('event_energy', 'Event Energy;MIP', 100, 0, 300)

    h2['hit_x_vs_y'] = TH2F('hit_x_vs_y', 'Hit x vs y;mm;mm', 80, -40, 40, 80, -40, 40)
    h2['hit_x_vs_z'] = TH2F('hit_x_vs_z', 'Hit x vs z;mm', 80, -40, 40, 10, 0, 10)
    h2['hit_y_vs_z'] = TH2F('hit_y_vs_z', 'Hit y vs z;mm', 80, -40, 40, 10, 0, 10)

    graph = {}  # root graph
    graph['layer_med_energy'] = TGraphErrors()
    graph['layer_med_energy'].SetMarkerStyle(20)
    graph['layer_med_energy'].SetName('layer_med_energy')
    graph['layer_med_energy'].SetTitle('Layer Median Energy;MIP')
    graph['layer_x_avg'] = TGraphErrors()
    graph['layer_x_avg'].SetMarkerStyle(20)
    graph['layer_x_avg'].SetName('layer_x_avg')
    graph['layer_x_avg'].SetTitle('Energy Weighted Layer X Mean;mm')
    graph['layer_y_avg'] = TGraphErrors()
    graph['layer_y_avg'].SetMarkerStyle(20)
    graph['layer_y_avg'].SetName('layer_y_avg')
    graph['layer_y_avg'].SetTitle('Energy Weighted Layer Y Mean;mm')

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
                line = line.strip()
                if line.startswith('#'):
                    continue
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
        hit_cellID = arrays["hit_cellID"]
        hit_energy = arrays['hit_energy']

        zero_event = 0
        print('INFO -- reading tree')
        for i in range(len(hit_cellID)):
            if (i%10000 == 0):
                print(f'\tevent {i}')
            event_x = 0
            event_y = 0
            event_energy = 0
            layer_x = []
            layer_y = []
            layer_energy = []
            for l in range(kLayers):
                layer_x.append(0)
                layer_y.append(0)
                layer_energy.append(0)

            for hi in range(len(hit_cellID[i])):
                cell = hit_cellID[i][hi]
                layer = cell//4
                energy = hit_energy[i][hi]
                if (1 == cell) or (7 == cell) or (energy < self.MIP_cut) or (16 == cell and energy >= 32.4) or (17 == cell and energy >= 33.5):
                    continue

                x = 1 if (cell%2) > 0 else -1
                x *= 23.7   # mm
                y = 1 if (cell%4) < 2 else -1
                y *= 23.7   # mm

                layer_energy[layer] += energy
                event_energy += energy
                layer_x[layer] += x*energy      # energy weighted
                event_x += x*energy
                layer_y[layer] += y*energy      # energy weighted
                event_y += y*energy

                self.h1['hit_cell_id'].Fill(cell);
                self.h1['hit_layer_id'].Fill(2*layer+1)
                self.h1['hit_x'].Fill(x);
                self.h1['hit_y'].Fill(y);
                self.h1['hit_energy'].Fill(energy);
                self.h2['hit_x_vs_y'].Fill(x, y);
                self.h2['hit_x_vs_z'].Fill(x, layer);
                self.h2['hit_y_vs_z'].Fill(y, layer);

                self.h1[f'cell{cell}_energy'].Fill(energy)

            if (event_energy > 0):
                self.eventMIPs.append(event_energy)
                self.h1['event_energy'].Fill(event_energy)
                self.h1['event_x'].Fill(event_x/event_energy)
                self.h1['event_y'].Fill(event_y/event_energy)
                for l in range(kLayers):
                    self.layerMIPs[l].append(layer_energy[l])
                    self.h1[f'layer{l}_energy'].Fill(layer_energy[l])
                    if layer_energy[l] > 0:
                        self.h1[f'layer{l}_x'].Fill(layer_x[l]/layer_energy[l])
                        self.h1[f'layer{l}_y'].Fill(layer_y[l]/layer_energy[l])
            else:
                zero_event+=1

        print(f'INFO -- zero energy event: {zero_event}')

        self.h1['event_energy'].Fit('gaus')
        delta = self.h1['event_energy'].GetFunction('gaus').GetParameter(2)
        print(f'INFO -- Energy resolution: {delta} MIPs')

        for l in range(kLayers):
            self.graph['layer_med_energy'].SetPoint(l, l+1, statistics.median(self.layerMIPs[l]))
            self.graph['layer_med_energy'].SetPointError(l, 0, statistics.pstdev(self.layerMIPs[l]))
            self.graph['layer_x_avg'].SetPoint(l, l+1, self.h1[f'layer{l}_x'].GetMean())
            self.graph['layer_x_avg'].SetPointError(l, 0, self.h1[f'layer{l}_x'].GetMeanError())
            self.graph['layer_y_avg'].SetPoint(l, l+1, self.h1[f'layer{l}_y'].GetMean())
            self.graph['layer_y_avg'].SetPointError(l, 0, self.h1[f'layer{l}_y'].GetMeanError())

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

        for (var, g) in self.graph.items():
            g.Draw('AP')
            c.SaveAs(f'{var}.png')
            self.fout.cd()
            g.Write()


        c = TCanvas('c', 'c', 4000, 1600)
        c.Divide(5, 2)
        for l in range(kLayers):
            c.cd(l+1)
            gPad.SetLogy()
            self.h1[f'layer{l}_energy'].Draw()

            self.fout.cd()
            self.h1[f'layer{l}_energy'].Write()
            self.h1[f'layer{l}_x'].Write()
            self.h1[f'layer{l}_y'].Write()
        c.SaveAs('layer_energy.png')

        for l in range(kLayers):
            c.cd(l+1)
            gPad.Clear()
            gPad.SetLogy()
            self.h1[f'layer{l}_x'].Draw()
        c.SaveAs('layer_x.png')

        for l in range(kLayers):
            c.cd(l+1)
            gPad.Clear()
            gPad.SetLogy()
            self.h1[f'layer{l}_y'].Draw()
        c.SaveAs('layer_y.png')

        c = TCanvas('c', 'c', 500*kLayers, 500*kCells)
        c.Divide(kLayers, kCells)
        for i in range(kLayers*kCells):
            c.cd(10*(i%4) + i//4 + 1)
            gPad.SetLogy()
            self.h1[f'cell{i}_energy'].Draw()

            self.fout.cd()
            self.h1[f'cell{i}_energy'].Write()
        c.SaveAs('cell_energy.png')


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
