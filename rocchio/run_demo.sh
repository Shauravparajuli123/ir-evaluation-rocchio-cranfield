#!/bin/sh
# Interactive class demo. Needs Java 21 or newer. Run from this folder: sh run_demo.sh
mkdir -p bin
javac -nowarn -cp ../lib/lucene-10.5.0.jar -d bin src/*.java || exit 1
java -cp "../lib/lucene-10.5.0.jar:bin" RocchioDemo ../data
