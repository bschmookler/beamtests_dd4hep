#!/bin/bash

source /opt/detector/setup.sh

# Input simulation parameters
ddsim --compactFile prototype.xml --numberOfEvents 100 --enableGun --gun.particle "e-" --gun.energy "2*GeV" --outputFile prototypeSim.edm4hep.root

# Output file names
info_string="e-_2_GeV"
simfile="prototypeSim.edm4hep.root"
recofile="prototype_reco_${info_string}.edm4hep.root"

# Running reconstruction
export JUGGLER_SIM_FILE=${simfile} JUGGLER_REC_FILE=${recofile} JUGGLER_N_EVENTS=100
gaudirun.py prototype_reco.py
