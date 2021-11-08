import datetime
from itertools import cycle

from django.test import Client, RequestFactory
import pytest
from pytest import fixture

from model_mommy import mommy

from dpnk import models, results, util

from dpnk.test.pytest.util import Mom


@pytest.fixture()
def competition(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        date_from=datetime.date(year=2010, month=11, day=1),
        date_to=datetime.date(year=2010, month=11, day=15),
        minimum_rides_base=23,
    ) as o:
        yield o


def test_get_minimum_rides_base_proportional(competition):
    assert (
        results.get_minimum_rides_base_proportional(
            competition, datetime.date(2010, 11, 1)
        )
        == 1
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition, datetime.date(2010, 11, 7)
        )
        == 10
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition, datetime.date(2010, 11, 15)
        )
        == 23
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition, datetime.date(2010, 11, 30)
        )
        == 23
    )


def test_get_minimum_rides_base_proportional_phase(competition_phase):
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2010, 11, 1)
        )
        == 0
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2010, 11, 7)
        )
        == 5
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2010, 11, 15)
        )
        == 12
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2010, 11, 30)
        )
        == 25
    )


# Get competitors without admission tests
@pytest.fixture()
def mens_frequency_competition_company(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="single_user",
        campaign=campaign,
        sex="male",
        company__name="Foo company",
    ) as o:
        yield o


def test_single_user_frequency(campaign, mens_frequency_competition_company):
    """Test if _filter_query_single_user function returns correct filter_query dict."""
    frequency_competition = mens_frequency_competition_company

    filter_query = results._filter_query_single_user(frequency_competition)
    expected_dict = {
        "approved_for_team": "approved",
        "campaign": campaign,
        "userprofile__user__is_active": True,
        "payment_status__in": ("done", "no_admission"),
        "team__subsidiary__company": frequency_competition.company,
        "userprofile__sex": "male",
    }
    assert filter_query == expected_dict


@pytest.fixture()
def frequency_competition_city(campaign, city):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="single_user",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_single_user_frequency_city(frequency_competition_city):
    """Test if _filter_query_single_user function returns correct filter_query dict with city filter."""
    filter_query = results._filter_query_single_user(frequency_competition_city)
    assert (
        str(filter_query["team__subsidiary__city__in"]) == "<QuerySet [<City: City 1>]>"
    )


@pytest.fixture()
def team_frequency_competition_company(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        company__name="Foo company",
    ) as o:
        yield o


def test_team_frequency(campaign, team_frequency_competition_company):
    """Test if _filter_query_team function returns correct filter_query dict."""
    competition = team_frequency_competition_company
    filter_query = results._filter_query_team(competition)
    expected_dict = {
        "campaign": campaign,
        "subsidiary__company": competition.company,
    }
    assert filter_query == expected_dict


@pytest.fixture()
def team_frequency_competition_city(campaign, city):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_team_frequency_city(campaign, team_frequency_competition_city):
    """Test if _filter_query_team function returns correct filter_query dict with city filter."""
    competition = team_frequency_competition_city
    filter_query = results._filter_query_team(competition)
    assert str(filter_query["subsidiary__city__in"]) == "<QuerySet [<City: City 1>]>"


@pytest.fixture()
def frequency_competition_company(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
        company__name="Foo company",
    ) as o:
        yield o


def test_company_frequency(frequency_competition_company):
    """Test if _filter_query_company function returns correct filter_query dict."""
    competition = frequency_competition_company
    filter_query = results._filter_query_company(competition)
    expected_dict = {
        "pk": competition.company.pk,
    }
    assert filter_query == expected_dict


@pytest.fixture()
def frequency_competition_city_team(city, campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_company_frequency_city(frequency_competition_city_team):
    """Test if _filter_query_company function returns correct filter_query dict with city filter."""
    competition = frequency_competition_city_team
    filter_query = results._filter_query_company(competition)
    assert str(filter_query["subsidiaries__city__in"]) == "<QuerySet [<City: City 1>]>"


# Get competitors tests
@fixture
def single_user_competition(campaign):
    with Mom(
        "dpnk.Competition",
        competitor_type="single_user",
        campaign=campaign,
    ) as o:
        yield o


def test_get_competitors_with_admission_single(ua1, single_user_competition):
    competition = single_user_competition
    query = results.get_competitors(competition)
    assert str(query.all()) == "<QuerySet [<UserAttendance: Foo user>]>"


@fixture
def team_competition(campaign):
    with Mom(
        "dpnk.Competition",
        competitor_type="team",
        campaign=campaign,
    ) as o:
        yield o


def test_get_competitors_with_admission_team(ua1, ua2, team, team_competition):
    competition = team_competition
    query = results.get_competitors(competition)
    assert str(query.all()) == "<QuerySet [<Team: Foo team (Bar user, Foo user)>]>"


@fixture
def company_competition(campaign):
    with Mom(
        "dpnk.Competition",
        competitor_type="company",
        campaign=campaign,
    ) as o:
        yield o


def test_get_competitors_with_admission_company(company, company_competition):
    competition = company_competition
    query = results.get_competitors(competition)
    assert str(query.all()) == "<QuerySet [<Company: Foo company>]>"


@fixture()
def liberos_competition(campaign):
    with Mom(
        "dpnk.Competition",
        competitor_type="liberos",
        campaign=campaign,
    ) as o:
        yield o


def test_get_competitors_liberos(liberos_competition, team, ua1):
    query = results.get_competitors(liberos_competition)
    assert str(query.all()) == "<QuerySet [<UserAttendance: Foo user>]>"
