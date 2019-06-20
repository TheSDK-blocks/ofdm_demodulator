#!/usr/bin/env bash
DIR="$( cd "$( dirname $0 )" && pwd )"
cd $DIR

git submodule sync
for module in \
    ./chisel; do
    git submodule update --init $module
    cd ./$module
    if [ -f ./init_submodles.sh ]; then
        ./init_submodules.sh
    fi
    sbt publishLocal
    cd $DIR
done

exit 0



