1. `apt install qgis`
1. nastavit security groups v AWS abych měl přístup z lokálního počítače
![](screenshots_qgis/Screenshot2.png)
1. nastavit PSQL připojení (it is necessary to add your IP address to the RDS security group in the AWS console. This security group is linked from the about information in the RDS db admin).
![](screenshots_qgis/Screenshot1.png)
1. stáhnout vrstvu `dpnk_trip_anonymized`
![](screenshots_qgis/Screenshot3.png)
1. Klikní na tlačitko 'Select features using an expression'
1. Zadavej expression v tvaru `"city" = 'olomouc'`
1. uložit vrstvu jako `ESRI Shapefile` (případně jiný formát)
![](screenshots_qgis/Screenshot5.png)
1. pokud chceme uložit jen výběr, tak to zaškrtnout
![](screenshots_qgis/Screenshot4.png)
