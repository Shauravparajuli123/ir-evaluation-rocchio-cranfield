#!/bin/sh
# Reruns every Rocchio experiment (a few minutes, about 1 GB of temporary files).
# Needs Java 21+, Python 3 and numpy. The last step also needs: pip install ranx
mkdir -p bin results/grid
javac -nowarn -cp ../lib/lucene-10.5.0.jar -d bin src/*.java || exit 1
java -cp "../lib/lucene-10.5.0.jar:bin" RocchioExperiment ../data results results/grid || exit 1
rm -f results/grid/gamma1_check.tmp
cd src
python3 rocchio_eval.py ../../data ../results ../results/grid ../../part_b_c/results/partc_TF-IDF.run || exit 1
python3 verify_rocchio.py ../../data ../results
cd ..
rm -rf results/grid
