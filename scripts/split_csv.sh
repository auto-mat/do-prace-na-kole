#!/bin/bash
tail "$1" -n+2 > "$1.headless"
split -l 500 "$1.headless" delivery_batches_ --additional-suffix=.csv
head=`head "$1"  -n1`
sed -i "1s/^/$head\n/" delivery_batches_*.csv
