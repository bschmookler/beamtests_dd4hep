#!/bin/bash

DIR=${1:-.}
cd $DIR
shift

i=1
if [ $# -ge 1 ]; then
    i=$1
fi

ls *_hist.root | while read f
do
    id=$(echo $f | egrep -o '[0-9]+_[0-9]+')
    if [ -z "$id" ]; then
	continue
    fi
    rename ${id} ${i} *${id}*.root
    let i++
done
