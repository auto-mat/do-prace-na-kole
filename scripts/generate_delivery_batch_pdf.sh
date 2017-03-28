#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh in.pdf in.csv "ids"

pdftk $1 burst output pdf_output/pg_%04d.pdf

mkdir pdf_output

file_ids=`echo $3 | sed s/\.pdf//`
OIFS=$IFS
IFS=';'
i=0
for id in $file_ids
do
   i=$((i+1))
   out_id=`cat $2 | cut -d\; -f 1,8 | tr \; " " | sed 's/"//g' | grep "^$id " | cut -d " " -f 2`
   mv `printf "pdf_output/pg_%04d" $i`.pdf pdf_output/customer_sheets_$out_id.a.pdf
done


pdftk pdf_output/*.pdf output combined_sheets.pdf
pdftk combined_sheets.pdf cat 1-endeast output combined_sheets-rotated.pdf
