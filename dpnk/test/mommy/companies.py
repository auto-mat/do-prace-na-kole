from dpnk import models
from model_mommy import mommy

class Companies():
    def __init__(self, cities):
        self.company = mommy.make(
            "dpnk.company",
            name = "Testing company",
            ico = "11111",
            dic = "CZ1234567890",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )

        self.company_no_admin = mommy.make(
            "dpnk.company",
            name = "Testing company without admin",
            ico = "11111",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )

        self.subsidiary = mommy.make(
            "dpnk.subsidiary",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
            company = self.company,
            city = cities.city,
        )

        self.other_subsidiary = mommy.make(
            "dpnk.subsidiary",
            address_psc = "22222",
            address_street_number = "2",
            address_street = "Ulice",
            address_city = "Brno",
            company = self.company,
            city = self.other_city,
        )
