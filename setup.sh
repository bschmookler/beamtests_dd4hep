source /opt/detector/setup.sh
DIR=$(cd -- $(dirname -- "${BASH_SOURCE[0]}") &> /dev/null  && pwd)
export LD_LIBRARY_PATH="${DIR}/install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
