#!/bin/bash

DIR=${1:-.}
cd $DIR
i=1
ls *.edm4hep.root | while read f
do
    prefix=${f%.edm4hep.root}
    rename ${prefix} ${i} ${prefix}*.root
    let i++
done
