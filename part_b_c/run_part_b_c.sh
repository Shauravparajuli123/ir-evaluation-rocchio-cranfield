#!/bin/sh
# Reruns Part B and Part C on Cranfield (a few minutes). Needs Java 21+, Python 3, numpy and scipy.
# The last step also needs: pip install ranx
mkdir -p bin results
python3 code/part_b.py results || exit 1
javac -nowarn -cp ../lib/lucene-10.5.0.jar -d bin code/LuceneExperiment.java || exit 1
java -cp "../lib/lucene-10.5.0.jar:bin" LuceneExperiment ../data results || exit 1
cd code
python3 part_c_eval.py ../../data ../results || exit 1
python3 verify.py ../../data ../results
