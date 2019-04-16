#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh delivery_batch.pdf delivery_batch.csv

pdftk $1 burst output tmp_pdf/output/pg_%04d.pdf

file_ids=`cat $2 | cut -d";" -f15 | grep -v "Variabilní symbol"`
i=0
for id in $file_ids; do
   i=$((i+1))
   mv `printf "tmp_pdf/output/pg_%04d" $i`.pdf tmp_pdf/output/customer_sheets_$id.gls_label.pdf
done

pdftk tmp_pdf/output/*.pdf* output tmp_pdf/combined_sheets.pdf
pdftk tmp_pdf/combined_sheets.pdf cat 1-endeast output tmp_pdf/combined_sheets-rotated.pdf
