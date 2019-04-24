#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh delivery_batch.pdf delivery_batch.csv

pdfseparate $1 tmp_pdf/output/pg_%04d.pdf

file_ids=`cat $2 | cut -d";" -f15 | grep -v "Variabilní symbol"`
i=0
for id in $file_ids; do
   i=$((i+1))
   mv `printf "tmp_pdf/output/pg_%04d" $i`.pdf tmp_pdf/output/customer_sheets_$id.gls_label.pdf
done

echo pdfunite
pdfunite tmp_pdf/output/*.pdf* tmp_pdf/combined_sheets.pdf
echo pdf90
rm tmp_pdf/output/ -R
pdf90 tmp_pdf/combined_sheets.pdf --outfile tmp_pdf/combined_sheets-rotated.pdf
