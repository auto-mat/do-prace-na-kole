from psc.models import PSC


def test_model_verbose_name():
    verbose_name = PSC._meta.verbose_name

    assert verbose_name == "Poštovní směrovací číslo"


def test_model_verbose_name_plural():
    verbose_name = PSC._meta.verbose_name_plural

    assert verbose_name == "Poštovní směrovací čísla"


def test_municipality_name_field_verbose_name():
    verbose_name = PSC._meta.get_field("municipality_name").verbose_name

    assert verbose_name == "Název obce"


def test_municipality_part_name_field_verbose_name():
    verbose_name = PSC._meta.get_field("municipality_part_name").verbose_name

    assert verbose_name == "Název části obce"


def test_district_name_field_verbose_name():
    verbose_name = PSC._meta.get_field("district_name").verbose_name

    assert verbose_name == "Název okresu"


def test_psc_field_verbose_name():
    verbose_name = PSC._meta.get_field("psc").verbose_name

    assert verbose_name == "PSČ"


def test_psc_field_help_text():
    verbose_name = PSC._meta.get_field("psc").help_text

    assert verbose_name == "Např.: „130 00“"


def test_post_name_field_verbose_name():
    verbose_name = PSC._meta.get_field("post_name").verbose_name

    assert verbose_name == "Název pošty"


def test_code_field_verbose_name():
    verbose_name = PSC._meta.get_field("code").verbose_name

    assert verbose_name == "Kód"
