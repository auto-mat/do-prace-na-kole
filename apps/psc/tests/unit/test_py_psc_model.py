import pytest
from django.utils.translation import activate, deactivate
from psc.models import PSC


class SetupError(AssertionError):
    """ Used to signal something went wrong during test setup """


@pytest.fixture(scope="function", name="switch_language")
def switch_language_fixture(request):
    if request.param not in ("cs", "en"):
        raise SetupError(f"Invalid language option: '{request.param}'!")

    activate(request.param)
    yield
    deactivate()


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Poštovní směrovací číslo"),
        pytest.param("en", "ZIP code"),
    ],
    indirect=["switch_language"],
)
def test_model_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Poštovní směrovací čísla"),
        pytest.param("en", "ZIP codes"),
    ],
    indirect=["switch_language"],
)
def test_model_verbose_name_plural(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.verbose_name_plural

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Název obce"),
        pytest.param("en", "Municipality name"),
    ],
    indirect=["switch_language"],
)
def test_municipality_name_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("municipality_name").verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Název části obce"),
        pytest.param("en", "Municipality part name"),
    ],
    indirect=["switch_language"],
)
def test_municipality_part_name_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("municipality_part_name").verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Název okresu"),
        pytest.param("en", "District name"),
    ],
    indirect=["switch_language"],
)
def test_district_name_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("district_name").verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "PSČ"),
        pytest.param("en", "ZIP code"),
    ],
    indirect=["switch_language"],
)
def test_psc_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("psc").verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_help_text",
    [
        pytest.param("cs", "Např.: „130 00“"),
        pytest.param("en", "e.g. „130 00“"),
    ],
    indirect=["switch_language"],
)
def test_psc_field_help_text(switch_language, expected_help_text):
    actual_help_text = PSC._meta.get_field("psc").help_text

    assert actual_help_text == expected_help_text


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Název pošty"),
        pytest.param("en", "Post office name"),
    ],
    indirect=["switch_language"],
)
def test_post_name_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("post_name").verbose_name

    assert actual_verbose_name == expected_verbose_name


@pytest.mark.parametrize(
    "switch_language, expected_verbose_name",
    [
        pytest.param("cs", "Kód"),
        pytest.param("en", "Code"),
    ],
    indirect=["switch_language"],
)
def test_code_field_verbose_name(switch_language, expected_verbose_name):
    actual_verbose_name = PSC._meta.get_field("code").verbose_name

    assert actual_verbose_name == expected_verbose_name
