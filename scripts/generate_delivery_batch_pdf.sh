#!/bin/bash

pdftk $1 burst


file_ids=`echo $3 | sed s/\.pdf//`
OIFS=$IFS
IFS=';'
i=0
for id in $file_ids
do
   i=$((i+1))
   out_id=`cat $2 | cut -d\; -f 1,2 | tr \; " " | sed 's/"//g' | grep "^$id " | cut -d " " -f 2`
   mv pg_`printf "%04d" $i`.pdf pdf_output/customer_sheets_$out_id.a.pdf
done


pdftk pdf_output/* output combined_sheets.pdf
pdftk combined_sheets.pdf  cat 1-endeast output combined_sheets-rotated.pdf
