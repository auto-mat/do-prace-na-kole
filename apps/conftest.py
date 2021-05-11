import datetime

from model_mommy import mommy
import pytest
from pytest import fixture

from dpnk.models import Campaign, CampaignType, Team

from dpnk.test.pytest.util import Mom


@pytest.fixture(autouse=True)
def setup_mommy():
    mommy.generators.add(
        "smart_selects.db_fields.ChainedForeignKey",
        "model_mommy.random_gen.gen_related",
    )


@pytest.fixture(scope="function")
def campaign_type(db):
    o = CampaignType.objects.create(
        name="CT1",
        slug="ct1",
    )
    yield o
    o.delete()


@pytest.fixture(scope="function")
def campaign(campaign_type):
    o = Campaign.objects.create(
        campaign_type=campaign_type,
        year="2021",
        slug="testing_campaign",
        slug_identifier="c2021",
    )
    yield o
    o.delete()


@fixture()
def competition_phase(campaign):
    with Mom(
        "dpnk.Phase",
        phase_type="competition",
        date_from=datetime.date(year=2010, month=11, day=1),
        date_to=datetime.date(year=2010, month=11, day=30),
        campaign=campaign,
    ) as o:
        yield o


@pytest.fixture()
def city(db):
    with Mom("dpnk.City", name="City 1") as o:
        yield o


@fixture()
def company(db):
    with Mom(
        "dpnk.Company",
        name="Foo company",
    ) as o:
        yield o


@pytest.fixture()
def team(campaign):
    with Mom(
        "dpnk.Team",
        name="Foo team",
        campaign=campaign,
    ) as o:
        yield o


@fixture()
def ua1(team, campaign, competition_phase):
    with Mom(
        "dpnk.UserAttendance",
        userprofile__nickname="Foo user",
        team=team,
        campaign=campaign,
        approved_for_team="approved",
    ) as o:
        Team.objects.get(pk=team.pk).save()
        yield o


@fixture()
def ua2(team, campaign, competition_phase):
    with Mom(
        "dpnk.UserAttendance",
        userprofile__nickname="Bar user",
        team=team,
        campaign=campaign,
        approved_for_team="approved",
    ) as o:
        Team.objects.get(pk=team.pk).save()
        yield o
