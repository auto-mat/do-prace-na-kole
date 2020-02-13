from model_mommy import mommy


class Subsidiaries:
    def __init__(self, cities, companies, **kwargs):
        self.subsidiary = mommy.make(   # pk = 1
            "dpnk.subsidiary",
            address_psc="11111",
            address_street_number="1",
            address_street="Ulice",
            address_city="Praha",
            company=companies.basic,
            city=cities.city,
        )

        self.other_subsidiary = mommy.make(   # pk = 2
            "dpnk.subsidiary",
            address_psc="22222",
            address_street_number="2",
            address_street="Ulice",
            address_city="Brno",
            company=companies.basic,
            city=cities.other_city,
        )
