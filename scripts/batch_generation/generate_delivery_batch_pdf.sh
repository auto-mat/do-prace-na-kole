#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh delivery_batch.pdf

pdftk $1 burst output tmp_pdf/output/pg_%04d.pdf

(
   cd tmp_pdf/output
   for file in pg_*.pdf; do
      mv $file customer_sheets_`pdftotext $file - | grep "č. krab." | sed "s/č. krab. \([0-9]*\).*/\\1/"`__gls_label.pdf
   done
)

echo concatenate pdf
pdftk `ls tmp_pdf/output/*.pdf* | sort` cat output tmp_pdf/combined_sheets.pdf
echo rotate
pdftk A=tmp_pdf/combined_sheets.pdf rotate Awest output tmp_pdf/combined_sheets-rotated.pdf
