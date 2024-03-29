Generating diplomas
-----------------------

Dopracenakole works with 4 types of diploma:

1. Individual diplomas
2. Team diplomas
3. City diplomas
4. Category winners

The first three are generated semi-automatically, diplomas for category winners are created manually.

Diplomas are generated by overlaying text over a PDF template.

Each campaign we upload new templates to [PDF Sandwich Types](https://dpnk.dopracenakole.cz/admin/smmapdfs/pdfsandwichtype/).

Each sandwich type can have email templates assocated with it. These email templates are used for sending out diplomas. This functionality is only used for individual diplomas as team diplomas are not sent out automatically. There should be one email template per language. Email templates are added directly in the PDF Sandwich Type admin page.

Email templates can contain variables. In the case of individual diplomas, these variables are listed [here](https://github.com/auto-mat/do-prace-na-kole/blob/master/apps/dpnk/models/diploma.py#L56).

Overlayed text is configured using the diploma fields admin pages which can be found at the following links:

1. [User attendance diploma fields](https://dpnk.dopracenakole.cz/admin/dpnk/diplomafield/)
2. [Team diploma fields](https://dpnk.dopracenakole.cz/admin/dpnk/teamdiplomafield/)
3. [City diploma fields](https://dpnk.dopracenakole.cz/admin/dpnk/cityincampaigndiplomafield/)

On the left of each page is a filter box. YOU NEED TO FILTER BY PDF SANDWICH TYPE!

For example, if you are prepairing the user diplomas for the 2022 Lednová Výzva you would select the "Lednová výzva 2022" pdfs sandwich type before configuring fields.

Finally, before you can generate diplomas you need to connect the template to the campaing by opening the [campaign admin](https://dpnk.dopracenakole.cz/admin/dpnk/campaign/) and searching for the "Diplomas" section and setting the sandwitch type.

In order to generate diplomas you need to open up the admin object listing for the given objects and run the "Make PDF sandwich" action on the objects for which you want to generate the diplomas.

1. [User attendance admin listing](https://dpnk.dopracenakole.cz/admin/dpnk/userattendance/)
2. [Team admin listing](https://dpnk.dopracenakole.cz/admin/dpnk/team/) 
3. [City admin listing](https://dpnk.dopracenakole.cz/admin/dpnk/cityincampaign/)

You can view (and in the case of user diplomas send) the newly generated diplomas in the diplomas admin lists.

1. [Use attendance diplomas](https://dpnk.dopracenakole.cz/admin/dpnk/diploma/)
2. [Team diplomas](https://dpnk.dopracenakole.cz/admin/dpnk/teamdiploma/)
3. [City diplomas](https://dpnk.dopracenakole.cz/admin/dpnk/cityincampaigndiploma/)
