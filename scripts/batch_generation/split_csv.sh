#!/bin/bash
tail "$1" -n+2 > "$1.headless"
split -l $2 "$1.headless" tmp_gls/delivery_batch_splitted_ --additional-suffix=.csv
head=`head "$1"  -n1`
sed -i "1s/^/$head\n/" tmp_gls/delivery_batch_splitted_*.csv
