#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh delivery_batches_*.pdf
# In the directory must CSV files with same names like the PDFs

for pdf_file in $@; do
   csv_file=`echo $pdf_file | sed "s/pdf/csv/g"`
   pdftk $pdf_file burst output pdf_output/pg_%04d.pdf

   file_ids=`cat $csv_file | cut -d";" -f15 | grep -v "Variabilní symbol"`
   i=0
   for id in $file_ids; do
      i=$((i+1))
      mv `printf "pdf_output/pg_%04d" $i`.pdf pdf_output/customer_sheets_$id.a.pdf
   done
done


pdftk pdf_output/*.pdf* output combined_sheets.pdf
pdftk combined_sheets.pdf cat 1-endeast output combined_sheets-rotated.pdf
