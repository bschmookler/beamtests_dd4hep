#!/bin/tcsh

setenv EIC_SHELL_PREFIX '/gpfs02/eic/wbzhang/epic/local/'
setenv SINGULARITY_BINDPATH '/gpfs02,/gpfs01,/gpfs'
/usr/bin/singularity exec $EIC_SHELL_PREFIX/lib/jug_xl-nightly /bin/bash -c "./doit.sh $argv[1-]"
