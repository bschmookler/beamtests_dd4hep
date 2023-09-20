#!/bin/bash
me=$(basename -- "$0")
ROOTDIR=$(realpath $(dirname -- "$0"))
WORKDIR=`pwd`
if [ -z "$DETERCTOR_PATH" ]; then source ${ROOTDIR}/setup.sh; fi

usage(){
    echo "${me} 
    --help		show this help message
    --particle P
    --particleEnergy E	in GeV
    --numberOfEvents N  number of events in each job process 
    --compactFile F
    --steeringFile F
    --outputSuffix S	suffix appended to the output file name
    "
}

# Input simulation parameters
OPTIONS=$(getopt --options h --longoptions  \
help,\
particle:,\
particleEnergy:,\
numberOfEvents:,\
compactFile:,\
steeringFile:,\
outputSuffix:, \
--name "${me}" -- "$@")
if [ $? != 0 ] ; then echo "Terminating..." >&2 ; exit 1 ; fi
eval set -- "$OPTIONS"

# default configurations
particle="e+"
particleEnergy=4	# in GeV
numberOfEvents=1000
compactFile="prototype.xml"
steeringFile="compact/steering.py"
outputSuffix=""

while true; do
    case "$1" in
	-h | --help)	usage;	exit 0 ;;
	--particle)	    particle="$2";	    shift 2 ;;
	--particleEnergy)   particleEnergy="$2";    shift 2 ;;
	--numberOfEvents)   numberOfEvents="$2";    shift 2 ;;
	--compactFile)	    compactFile="$2";	    shift 2 ;;
	--steeringFile)	    steeringFile="$2";	    shift 2 ;;
	--outputSuffix)	    outputSuffix="$2";	    shift 2 ;;
	--) shift; break ;;
	*) break ;;
    esac
done

echo -e "INFO --\trun ${numberOfEvents} ${particle} events with
    \tE=${particleEnergy} GeV
    \tcompactFile=${compactFile}
    \tsteeringFile=${steeringFile}"

# Output file names
output="${particle}_${particleEnergy}GeV"
[ -z "$outputSuffix" ] || output="${output}_${outputSuffix}"
simfile="${WORKDIR}/sim_${output}.edm4hep.root"
recofile="${WORKDIR}/reco_${output}.edm4hep.root"

cd $ROOTDIR
# Running simulation
npsim \
--compactFile ${compactFile} \
--steeringFile ${steeringFile} \
--numberOfEvents ${numberOfEvents} \
--enableGun --gun.particle "$particle" --gun.energy "${particleEnergy}*GeV" \
--outputFile ${simfile}  || exit

# Running reconstruction
export JUGGLER_SIM_FILE=${simfile} JUGGLER_REC_FILE=${recofile} JUGGLER_N_EVENTS=${numberOfEvents}
gaudirun.py prototype_reco.py

# analysis
output=${recofile%.edm4hep.root}
level=reco

make_tree='${ROOTDIR}/beamtests_dd4hep/analysis/sim/make_tree.py'
# plot='${ROOTDIR}/analysis/plot.py'
CONFIG_FILE='${ROOTDIR}/analysis/sim/config.cfg'
$make_tree -c $CONFIG_FILE -o ${output}.root -l $level ${recofile}
# $plot -c $CONFIG_FILE -o ${output}_hist.root ${output}.root
