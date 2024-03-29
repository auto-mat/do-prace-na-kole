import datetime
from itertools import cycle

from django.test import Client, RequestFactory
import pytest
from pytest import fixture

from model_mommy import mommy

from dpnk import models, results, util

from dpnk.test.pytest.util import Mom


@pytest.fixture()
def competition_team_frequency(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        date_from=datetime.date(year=2010, month=11, day=1),
        date_to=datetime.date(year=2010, month=11, day=15),
        minimum_rides_base=23,
        campaign=campaign,
    ) as o:
        yield o


def test_get_minimum_rides_base_proportional(competition_team_frequency):
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


def test_team_get_remaining_rides_count_empty_team(team):
    assert team.get_remaining_rides_count() == 0


def test_team_get_remaining_rides_count_empty_team(team, may_fifth, ua1, ua2):
    assert team.get_remaining_rides_count() == 60


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
def mens_frequency_competition_company(campaign, company):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="single_user",
        campaign=campaign,
        sex="male",
        company=company,
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
def team_frequency_competition_company(campaign, company):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        company=company,
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
def frequency_competition_company(campaign, company):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
        company=company,
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
        date_from=datetime.date(year=2010, month=11, day=1),
        date_to=datetime.date(year=2010, month=11, day=15),
        minimum_rides_base=23,
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


def test_get_minimum_rides_base_proportional(team_competition):
    assert (
        results.get_minimum_rides_base_proportional(
            team_competition, datetime.date(2010, 11, 1)
        )
        == 1
    )
    assert (
        results.get_minimum_rides_base_proportional(
            team_competition, datetime.date(2010, 11, 7)
        )
        == 10
    )
    assert (
        results.get_minimum_rides_base_proportional(
            team_competition, datetime.date(2010, 11, 15)
        )
        == 23
    )
    assert (
        results.get_minimum_rides_base_proportional(
            team_competition, datetime.date(2010, 11, 30)
        )
        == 23
    )


def test_get_minimum_rides_base_proportional_phase(competition_phase):
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2017, 4, 2)
        )
        == 0
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2017, 4, 11)
        )
        == 5
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2017, 4, 24)
        )
        == 11
    )
    assert (
        results.get_minimum_rides_base_proportional(
            competition_phase, datetime.date(2017, 5, 1)
        )
        == 15
    )


@fixture()
def company_competition_single_user(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="single_user",
        campaign=campaign,
        sex="male",
        company__name="Foo company",
    ) as o:
        yield o


def test_single_user_frequency_competitor_without_admission(
    company_competition_single_user, campaign
):
    """Test if _filter_query_single_user function returns correct filter_query dict."""
    competition = company_competition_single_user
    filter_query = results._filter_query_single_user(competition)
    expected_dict = {
        "approved_for_team": "approved",
        "campaign": campaign,
        "userprofile__user__is_active": True,
        "payment_status__in": ("done", "no_admission"),
        "team__subsidiary__company": competition.company,
        "userprofile__sex": "male",
    }
    assert filter_query == expected_dict


@fixture()
def city_competition_single_user(campaign, city):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="single_user",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_single_user_frequency_city_competitor_without_admission(
    city_competition_single_user,
):
    """Test if _filter_query_single_user function returns correct filter_query dict with city filter."""
    filter_query = results._filter_query_single_user(city_competition_single_user)
    assert (
        str(filter_query["team__subsidiary__city__in"]) == "<QuerySet [<City: City 1>]>"
    )


@fixture()
def company_competition_team(campaign):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        company__name="Foo company",
    ) as o:
        yield o


def test_team_frequency_competitor_without_admission(
    campaign, company_competition_team
):
    """Test if _filter_query_team function returns correct filter_query dict."""
    competition = company_competition_team
    filter_query = results._filter_query_team(competition)
    expected_dict = {
        "campaign": campaign,
        "subsidiary__company": competition.company,
    }
    assert filter_query == expected_dict


@fixture()
def city_competition_team_frequency(campaign, city):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_team_frequency_city_competitor_without_admission(
    city_competition_team_frequency,
):
    """Test if _filter_query_team function returns correct filter_query dict with city filter."""
    competition = city_competition_team_frequency
    filter_query = results._filter_query_team(competition)
    assert str(filter_query["subsidiary__city__in"]) == "<QuerySet [<City: City 1>]>"


@fixture()
def company_competition_company_frequency(campaign, company):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
        company=company,
    ) as o:
        yield o


def test_company_frequency_competitor_without_admission(
    company_competition_company_frequency,
):
    """Test if _filter_query_company function returns correct filter_query dict."""
    competition = company_competition_company_frequency
    filter_query = results._filter_query_company(competition)
    expected_dict = {
        "pk": competition.company.pk,
    }
    assert filter_query == expected_dict


@fixture()
def city_competition_company_frequency(campaign, company, city):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
        city=[city],
    ) as o:
        yield o


def test_company_frequency_city_competitor_without_admission(
    city_competition_company_frequency,
):
    """Test if _filter_query_company function returns correct filter_query dict with city filter."""
    competition = city_competition_company_frequency
    filter_query = results._filter_query_company(competition)
    assert str(filter_query["subsidiaries__city__in"]) == "<QuerySet [<City: City 1>]>"


# Get competitor tests
def test_get_competitors(team, ua1, ua2, campaign):
    competition = mommy.make(
        "dpnk.Competition",
        competitor_type="team",
        campaign=campaign,
    )
    query = results.get_competitors(competition)
    assert str(query.all()) == "<QuerySet [<Team: Foo team (Bar user, Foo user)>]>"


@pytest.fixture()
def competition_single_user_length(campaign):
    with Mom(
        "Competition",
        competition_type="length",
        competitor_type="single_user",
        campaign=campaign,
        date_from=datetime.date(2017, 4, 3),
        date_to=datetime.date(2017, 5, 23),
        commute_modes=models.CommuteMode.objects.filter(
            slug__in=("bicycle", "by_foot")
        ),
    ) as o:
        yield o


def test_get_competitors_with_admission_single(ua1, competition_single_user_length):
    mommy.make("Payment", status=99, userattendance=ua1)
    query = results.get_competitors(competition_single_user_length)
    assert str(query.all()), "<QuerySet [<UserAttendance: Foo user>]"


def test_get_competitors_with_admission_team(
    ua1, ua2, competition_team_frequency, team
):
    mommy.make("Payment", status=99, userattendance=ua1).save()
    mommy.make("Payment", status=99, userattendance=ua2).save()
    query = results.get_competitors(competition_team_frequency)
    assert str(query.all()) == "<QuerySet [<Team: Foo team (Bar user, Foo user)>]>"


@fixture()
def competition_company_frequency(campaign, company):
    with Mom(
        "dpnk.Competition",
        competition_type="frequency",
        competitor_type="company",
        campaign=campaign,
    ) as o:
        yield o


def test_get_competitors_with_admission_company(competition_company_frequency):
    query = results.get_competitors(competition_company_frequency)
    assert str(query.all()) == "<QuerySet [<Company: Foo company>]>"


def test_get_competitors_liberos(ua1, team, competition_single_user_length):
    query = results.get_competitors(competition_single_user_length)
    assert str(query.all()) == "<QuerySet [<UserAttendance: Foo user>]>"


# Test results
@fixture()
def results_trips(ua1, bicycle, by_foot, no_work, by_other_vehicle):
    mommy.make(
        "Trip",
        commute_mode=bicycle,
        distance="1",
        direction="trip_to",
        user_attendance=ua1,
        date="2017-05-01",
    ).save()
    mommy.make(
        "Trip",
        commute_mode=no_work,
        direction="trip_to",
        date="2017-05-02",
        user_attendance=ua1,
    ).save()
    mommy.make(
        "Trip",
        commute_mode=no_work,
        direction="trip_from",
        date="2017-05-02",
        user_attendance=ua1,
    ).save()
    mommy.make(
        "Trip",
        commute_mode=by_foot,
        distance="1",
        direction="trip_from",
        date="2017-05-03",
        user_attendance=ua1,
    ).save()
    ua1.save()


@fixture
def may_fifth(settings):
    settings.FAKE_DATE = datetime.date(year=2017, month=5, day=5)


def test_get_userprofile_length(
    campaign,
    ua1,
    results_trips,
    may_fifth,
):
    competition = mommy.make(
        "Competition",
        competition_type="length",
        competitor_type="single_user",
        campaign=campaign,
        date_from=datetime.date(2017, 4, 3),
        date_to=datetime.date(2017, 5, 23),
        commute_modes=models.CommuteMode.objects.filter(
            slug__in=("bicycle", "by_foot")
        ),
    )
    result = results.get_userprofile_length([ua1], competition)
    assert result == 2.0

    util.rebuild_denorm_models([ua1])
    ua1.refresh_from_db()

    result = ua1.trip_length_total
    assert result == 2.0


def test_get_userprofile_frequency(ua1, ua2, campaign, results_trips, may_fifth):
    competition = mommy.make(
        "Competition",
        competition_type="frequency",
        competitor_type="team",
        campaign=campaign,
        date_from=datetime.date(2017, 4, 3),
        date_to=datetime.date(2017, 5, 23),
        commute_modes=models.CommuteMode.objects.filter(
            slug__in=("bicycle", "by_foot")
        ),
    )
    mommy.make("Payment", status=99, userattendance=ua1)
    mommy.make("Payment", status=99, userattendance=ua2)

    util.rebuild_denorm_models([ua1, ua2, ua1.team])
    ua1.refresh_from_db()
    ua2.refresh_from_db()
    ua1.team.refresh_from_db()

    result = ua1.get_rides_count_denorm
    assert result == 2

    result = ua1.get_working_rides_base_count()
    assert result == 47

    result = ua1.frequency
    assert result == 0.0425531914893617

    result = ua2.frequency
    assert result == 0

    result = ua1.team.frequency
    assert result == 0.0212765957446809

    result = ua1.team.get_rides_count_denorm
    assert result == 2

    result = results.get_working_trips_count(ua1, competition)
    assert result == 47

    result = results.get_working_trips_count(ua2, competition)
    assert result == 48

    result = ua1.team.get_working_trips_count()
    assert result == 95

    result = results.get_userprofile_frequency(ua1, competition)
    assert result == (2, 47, 2 / 47.0)

    result = results.get_team_frequency(ua1.team.members, competition)
    assert result == (2, 95, 2 / 95.0)


def test_get_userprofile_length_by_foot(ua1, campaign, results_trips, may_fifth):
    competition = mommy.make(
        "Competition",
        competition_type="length",
        competitor_type="single_user",
        campaign=campaign,
        date_from=datetime.date(2017, 4, 1),
        date_to=datetime.date(2017, 5, 31),
        commute_modes=models.CommuteMode.objects.filter(slug__in=("by_foot",)),
    )
    result = results.get_userprofile_length([ua1], competition)
    assert result == 1.0
