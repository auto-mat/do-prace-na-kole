#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh in.pdf gls.csv delivery_batch.csv

pdftk $1 burst output pdf_output/pg_%04d.pdf

file_ids=`cat "$3" | cut -d";" -f15 | grep -v "Variabilní symbol"`
i=0
for id in $file_ids
do
   i=$((i+1))
   mv `printf "pdf_output/pg_%04d" $i`.pdf pdf_output/customer_sheets_$id.a.pdf
done


pdftk pdf_output/*.pdf output combined_sheets.pdf
pdftk combined_sheets.pdf cat 1-endeast output combined_sheets-rotated.pdf
