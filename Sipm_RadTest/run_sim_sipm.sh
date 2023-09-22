#!/bin/bash

compactFile=${1:-sipm_stack.xml}
nEvent=${2:-100000}
source /opt/detector/setup.sh

# Input simulation parameters -- Proton
npsim --compactFile sipm_stack.xml --numberOfEvents ${nEvent} --enableGun --gun.particle "proton" --gun.energy "325.9*MeV" --outputFile Sipm_proton.edm4hep.root

#Input simulation patameters -- Neutron
npsim --compactFile sipm.xml --numberOfEvents ${nEvent} --enableGun --gun.particle "neutron" --gun.energy "43.4*MeV" --outputFile Sipm_neutron.edm4hep.root

