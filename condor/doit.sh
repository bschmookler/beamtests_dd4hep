#!/bin/bash

OUTPUT_DIR=${1:-condor}
OUTPUT_PREFIX=${2:-condor}
cd /gpfs02/eic/wbzhang/epic/beamtests_dd4hep
source setup.sh
npsim --compactFile prototype.xml --steeringFile geometry/steering.py --numberOfEvents 10000 --enableGun --outputFile ${OUTPUT_DIR}/${OUTPUT_PREFIX}.edm4hep.root

cd ${OUTPUT_DIR}
EXEC='/gpfs02/eic/wbzhang/epic/beamtests_dd4hep/analysis/sim/plot.py'
CONFIG_FILE='/gpfs02/eic/wbzhang/epic/beamtests_dd4hep/analysis/sim/config.cfg'
$EXEC -c $CONFIG_FILE -o ${OUTPUT_PREFIX}.hist.root ${OUTPUT_PREFIX}.edm4hep.root

