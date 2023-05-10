#!/bin/bash

njob=${1:-1}
nprocess=${2:-5}

for (( i=1; i<=$njob; i++ ))
do
    CONDOR_JOB=condor_${i}.job
    [ -f $CONDOR_JOB ] && rm $CONDOR_JOB
    cat << END >> ${CONDOR_JOB}
Universe        = vanilla
Notification    = Never
Executable      = run_eic.csh
Arguments       = /gpfs02/eic/wbzhang/epic/beamtests_dd4hep/condor/ \$(ClusterID)_\$(ProcID)
Requirements    = (CPU_Speed >= 2)
Rank		= CPU_Speed
request_memory  = 2GB
request_cpus    = 1
Priority        = 20
GetEnv          = False
Initialdir      = /gpfs02/eic/wbzhang/epic/beamtests_dd4hep/condor/
Input           = doit.sh
# transfer_input_files = file1,file2
Output          = \$(ClusterID)_\$(ProcID).out
Error           = \$(ClusterID)_\$(ProcID).err
Log             = \$(ClusterID)_\$(ProcID).log
should_transfer_files = IF_NEEDED
when_to_transfer_output = ON_EXIT_OR_EVICT
PeriodicHold    = (NumJobStarts >= 1 && JobStatus == 1)
Notify_user     = weibinz@ucr.edu
Queue ${nprocess}
END
    condor_submit ${CONDOR_JOB}
done
