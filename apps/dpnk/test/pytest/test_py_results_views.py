import datetime
import pytest
import json

from django.test import Client, RequestFactory

from model_mommy import mommy

from dpnk.views_results import CompetitionResultListJson


@pytest.fixture()
def client():
    return Client(HTTP_HOST="testing-campaign.example.com", HTTP_REFERER="test-referer")


@pytest.fixture()
def factory():
    return RequestFactory()


@pytest.fixture()
def team_length_competition(campaign, competition_phase):
    o = mommy.make(
        "dpnk.Competition",
        campaign=campaign,
        competition_type="length",
        competitor_type="team",
        slug="competition",
    )
    yield o
    o.delete()


@pytest.fixture()
def competition_phase(campaign):
    o = mommy.make(
        "dpnk.Phase",
        campaign=campaign,
        phase_type="competition",
        date_from=datetime.date(2021, 2, 1),
        date_to=datetime.date(2021, 12, 31),
    )
    o.save()
    yield o
    o.delete()


@pytest.fixture()
def result1(campaign, team_length_competition):
    o = mommy.make(
        "dpnk.CompetitionResult",
        result="1",
        result_divident="1.2",
        result_divisor="1.1",
        competition=team_length_competition,
        team__campaign=campaign,
        team__member_count=1,
        team__subsidiary__city__name="foo city",
        team__subsidiary__company__name="bar company",
        team__name="foo team",
    )
    yield o
    o.delete()


@pytest.fixture()
def result2(campaign, team_length_competition):
    o = mommy.make(
        "dpnk.CompetitionResult",
        result="0.5",
        result_divident="0.5",
        result_divisor="1.0",
        competition=team_length_competition,
        team__campaign=campaign,
        team__member_count=1,
        team__subsidiary__city__name="a city",
        team__subsidiary__company__name="a company",
        team__name="a team",
    )
    yield o
    o.delete


@pytest.fixture()
def results(result1, result2):
    pass


@pytest.fixture()
def single_frequency_competition(campaign, competition_phase):
    o = mommy.make(
        "dpnk.Competition",
        campaign=campaign,
        competition_type="frequency",
        competitor_type="single_user",
        slug="competition",
    )
    yield o
    o.delete()


@pytest.fixture()
def freq_result1(single_frequency_competition, campaign):
    o = mommy.make(
        "dpnk.CompetitionResult",
        result="1",
        result_divident="3",
        result_divisor="1",
        competition=single_frequency_competition,
        user_attendance__userprofile__nickname="foo user",
        user_attendance__userprofile__user__first_name="Adam",
        user_attendance__userprofile__user__last_name="Rosa",
        user_attendance__campaign=campaign,
        user_attendance__team__campaign=campaign,
        user_attendance__team__member_count=1,
        user_attendance__team__subsidiary__city__name="foo city",
        user_attendance__team__subsidiary__company__name="foo company",
        user_attendance__team__name="foo team",
        id=3,
    )
    yield o
    o.delete()


@pytest.fixture()
def freq_result2(single_frequency_competition, campaign):
    o = mommy.make(
        "dpnk.CompetitionResult",
        result="1",
        result_divident="2",
        result_divisor="1",
        competition=single_frequency_competition,
        user_attendance__userprofile__sex="female",
        user_attendance__userprofile__nickname=None,
        user_attendance__userprofile__user__first_name="Jan",
        user_attendance__userprofile__user__last_name="Novák",
        user_attendance__campaign=campaign,
        user_attendance__team__campaign=campaign,
        user_attendance__team__member_count=1,
        user_attendance__team__subsidiary__city__name="bar city",
        user_attendance__team__subsidiary__company__name="bar company",
        user_attendance__team__name="bar team",
        id=2,
    )
    yield o
    o.delete()


@pytest.fixture()
def freq_results(freq_result1, freq_result2):
    pass


def test_team_length(factory, results):
    """ Test if team length competition result JSON is returned """
    request = factory.get("")
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            ["1.", "1,0", "1,2", "0", "foo team", "bar company", "foo city"],
            ["2.", "0,5", "0,5", "0", "a team", "a company", "a city"],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 2,
    }
    assert json.loads(response.content) == expected_json


def test_team_length_search(factory, results):
    """ Test if searching by string works """
    get_params = {"search[value]": "oo cit"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            ["1.", "1,0", "1,2", "0", "foo team", "bar company", "foo city"],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    json.loads(response.content) == expected_json


def test_team_length_company_search(factory, results):
    """ Test if searching by company name works """
    get_params = {"columns[0][search][value]": "company"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            ["1.", "1,0", "1,2", "0", "foo team", "bar company", "foo city"],
            ["2.", "0,5", "0,5", "0", "a team", "a company", "a city"],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 2,
    }
    assert json.loads(response.content) == expected_json


def test_team_length_company_search_quotes(factory, results):
    """ Test if searching by exact company name works """
    get_params = {"columns[0][search][value]": '"bar company"'}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            ["1.", "1,0", "1,2", "0", "foo team", "bar company", "foo city"],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    json.loads(response.content) == expected_json


def test_get(factory, freq_results):
    """ Test if single user frequency competition result JSON is returned """
    request = factory.get("")
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            [
                "1.&nbsp;-&nbsp;2.",
                "100,0",
                "3",
                "1",
                "foo user",
                "foo team",
                "foo company",
                "-",
                "",
                "foo city",
            ],
            [
                "1.&nbsp;-&nbsp;2.",
                "100,0",
                "2",
                "1",
                "Jan Novák",
                "bar team",
                "bar company",
                "-",
                "Žena",
                "bar city",
            ],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 2,
    }
    json.loads(response.content) == expected_json


def test_paging_filter(factory, freq_results, campaign, single_frequency_competition):
    """
    Test if single user frequency competition result JSON is returned
    Test if paging works correctly when filter is enabled.
    This test ensures, that ranks are correctly counted for filtered items.
    """
    mommy.make(
        "dpnk.CompetitionResult",
        result="1",
        result_divident="2",
        result_divisor="1",
        competition=single_frequency_competition,
        user_attendance__userprofile__nickname="baz user",
        user_attendance__userprofile__occupation__name="Foo ocupation",
        user_attendance__campaign=campaign,
        user_attendance__team__campaign=campaign,
        user_attendance__team__member_count=1,
        user_attendance__team__subsidiary__city__name="baz city",
        user_attendance__team__subsidiary__company__name="baz company",
        user_attendance__team__name="baz team",
        id=1,
    )
    get_params = {
        "length": 1,
        "search[value]": "baz user",
    }
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 3,
        "data": [
            [
                "1.&nbsp;-&nbsp;3.",
                "100,0",
                "2",
                "1",
                "baz user",
                "baz team",
                "baz company",
                "Foo ocupation",
                "",
                "baz city",
            ],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    assert json.loads(response.content) == expected_json


def test_search_user_nickname(factory, freq_results):
    """ Test if searching by user nickname field works """
    get_params = {"search[value]": "oo user"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            [
                "1.&nbsp;-&nbsp;2.",
                "100,0",
                "3",
                "1",
                "foo user",
                "foo team",
                "foo company",
                "-",
                "",
                "foo city",
            ],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    assert json.loads(response.content) == expected_json


def test_search_user_name(factory, freq_results):
    """ Test if searching by user name field works """
    get_params = {"search[value]": "Novak Jan"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            [
                "1.&nbsp;-&nbsp;2.",
                "100,0",
                "2",
                "1",
                "Jan Novák",
                "bar team",
                "bar company",
                "-",
                "Žena",
                "bar city",
            ],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    assert json.loads(response.content) == expected_json


def test_search_sex_female(factory, freq_results):
    """ Test if searching by female sex name field works """
    get_params = {"search[value]": "Žena"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [
            [
                "1.&nbsp;-&nbsp;2.",
                "100,0",
                "2",
                "1",
                "Jan Novák",
                "bar team",
                "bar company",
                "-",
                "Žena",
                "bar city",
            ],
        ],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 1,
    }
    assert json.loads(response.content) == expected_json


def test_search_sex_male(factory, freq_results):
    """ Test if searching by male sex name field works """
    get_params = {"search[value]": "Muž"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 0,
    }
    assert json.loads(response.content) == expected_json


def test_search_user_name_not_found(factory, freq_results):
    """
    If the user has nickname, we can't find by his name,
    otherwise the name can reverse engeneered.
    """
    get_params = {"search[value]": "Rosa"}
    request = factory.get("", get_params)
    request.subdomain = "testing-campaign"
    response = CompetitionResultListJson.as_view()(
        request, competition_slug="competition"
    )
    expected_json = {
        "recordsTotal": 2,
        "data": [],
        "draw": 0,
        "result": "ok",
        "recordsFiltered": 0,
    }
    assert json.loads(response.content) == expected_json
