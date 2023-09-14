#!/bin/bash

input=$1
output=${input%.edm4hep.root}
level=sim
if grep -q "reco" <<< "$input"; then
    level=reco
fi

source /gpfs02/eic/wbzhang/epic/beamtests_dd4hep/setup.sh
cd $(dirname $input)
make_tree='/gpfs02/eic/wbzhang/epic/beamtests_dd4hep/analysis/sim/make_tree.py'
plot='/gpfs02/eic/wbzhang/epic/beamtests_dd4hep/analysis/plot.py'
CONFIG_FILE='/gpfs02/eic/wbzhang/epic/beamtests_dd4hep/analysis/sim/config.cfg'
$make_tree -c $CONFIG_FILE -o ${output}.root -l $level ${input}
$plot -c $CONFIG_FILE -o ${output}_hist.root ${output}.root

