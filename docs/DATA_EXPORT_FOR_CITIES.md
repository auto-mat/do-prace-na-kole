Data exports for cities
-----------------------

Track data can be exported on a per city basis for further analysis.

To generate data, start by opening the ["City in Campaign" admin](https://dpnk.dopracenakole.cz/admin/dpnk/cityincampaign/).

Then select the cities you want to generate data for, and run the "Vytvořit tabulka anoninymních jízd a vytvořit .shp soubor pro export GIS data" action.

![image](https://user-images.githubusercontent.com/1391608/176537849-a75652ed-f5bb-41c1-8500-e5755fff671e.png)

The admin action will run the task in celery and it will take up to several hours to complete.

Finding the data
================

As admin
--------

Once the action is done you can download it in the admin by opening up a specific city.

![image](https://user-images.githubusercontent.com/1391608/176538832-92f39e9f-d6d2-430a-a917-15e656e577cf.png)

The data is stored in an encrypted ZIP file. The password is visible in the admin. **Do not send the encrypted ZIP file and password in the same message, always use two methods of sending, for exmaple send the file via google drive and the password via SMS**.

As city coordinator
-------------------

The data is also accessible to city coordinators. They can get it by clicking on the "Městský koordinator" item in the main menu:

![image](https://user-images.githubusercontent.com/1391608/176545395-e20a03f4-ccca-440f-826b-187d877d764e.png)


