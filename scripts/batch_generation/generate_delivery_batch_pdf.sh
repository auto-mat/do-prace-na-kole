#!/bin/bash

# Usage: ./generate_delivery_batch_pdf.sh delivery_batch.pdf

pdfseparate $1 tmp_pdf/output/pg_%04d.pdf

(
   cd tmp_pdf/output
   for file in pg_*.pdf; do
      mv $file customer_sheets_`pdftotext $file - | grep "č. krab." | sed "s/č. krab. \([0-9]*\).*/\\1/"`--gls_label.pdf
   done
)

echo rotate
for i in tmp_pdf/output/*.pdf; do pdfjam --angle '90' --outfile "$i-rot" -- $i; mv "$i-rot" $i; done
pdfjam --angle '90' --outfile "$1-rot" -- $1
mv "$1-rot" $1
echo pdfunite
pdfunite tmp_pdf/output/*.pdf* tmp_pdf/combined_sheets-rotated.pdf
