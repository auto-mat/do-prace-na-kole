from model_mommy import mommy

class Companies:
    def __init__(self, cities, **kwargs):
        self.basic = mommy.make(  #pk=1
            "dpnk.company",
            name = "Testing company",
            ico = "11111",
            dic = "CZ1234567890",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )

        self.no_admin = mommy.make(  #pk=2
            "dpnk.company",
            name = "Testing company without admin",
            ico = "11111",
            address_psc = "11111",
            address_street_number = "1",
            address_street = "Ulice",
            address_city = "Praha",
        )
