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
        date_from=datetime.date(year=2017, month=4, day=2),
        date_to=datetime.date(year=2017, month=5, day=20),
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


@fixture()
def bicycle(db):
    with Mom(
        "dpnk.CommuteMode",
        name="Kolo",
        name_en="Bicycle",
        name_cs="Kolo",
        name_dsnkcs=None,
        slug="bicycle",
        order=0,
        tooltip="Nejprve si vyberte zp\u016fsob dopravy a pak zadejte po\u010det kilometr\u016f.",
        tooltip_en=None,
        tooltip_cs="Nejprve si vyberte zp\u016fsob dopravy a pak zadejte po\u010det kilometr\u016f.",
        tooltip_dsnkcs=None,
        button_html='<span class="fas fa-bicycle"></span>',
        icon_html='<i class="fa fa-bicycle xs"></i>',
        add_command="Zapsat {{distance}} km j\u00edzdy na kolech {{direction}}.",
        add_command_en=None,
        add_command_cs="Zapsat {{distance}} km j\u00edzdy na kolech {{direction}}.",
        add_command_dsnkcs=None,
        choice_description="Chcete si zapsat: {{distance}} km j\u00edzdy na kole, kolob\u011b\u017ece nebo brusl\u00edch.<br/> Te\u010f ozna\u010dte kliknut\u00edm na ikony '+' v kalend\u00e1\u0159i v\u0161echny dny a sm\u011bry, pro kter\u00e9 plat\u00ed tyto \u00fadaje.",
        choice_description_en=None,
        choice_description_cs="Chcete si zapsat: {{distance}} km j\u00edzdy na kole, kolob\u011b\u017ece nebo brusl\u00edch.<br/> Te\u010f ozna\u010dte kliknut\u00edm na ikony '+' v kalend\u00e1\u0159i v\u0161echny dny a sm\u011bry, pro kter\u00e9 plat\u00ed tyto \u00fadaje.",
        choice_description_dsnkcs=None,
        does_count=True,
        eco=True,
    ) as o:
        yield o


@fixture()
def by_foot(db):
    with Mom(
        "dpnk.CommuteMode",
        name="P\u011b\u0161ky",
        name_en="Walk/run",
        name_cs="P\u011b\u0161ky",
        name_dsnkcs=None,
        slug="by_foot",
        order=2,
        tooltip="Nejprve si vyberte zp\u016fsob dopravy a pak zadejte po\u010det kilometr\u016f.",
        tooltip_en=None,
        tooltip_cs="Nejprve si vyberte zp\u016fsob dopravy a pak zadejte po\u010det kilometr\u016f.",
        tooltip_dsnkcs=None,
        button_html='<span class="fas fa-running"></span>\r\n<span class="fas fa-slash fa-rotate-90"></span>\r\n<span class="fab fa-accessible-icon"></span>',
        icon_html='<i class="fa fa-running xs"></i>',
        add_command="Zapsat {{distance}} km b\u011bhu (ch\u016fze) {{direction}}.",
        add_command_en=None,
        add_command_cs="Zapsat {{distance}} km b\u011bhu (ch\u016fze) {{direction}}.",
        add_command_dsnkcs=None,
        choice_description="Chcete si zapsat: {{distance}} km b\u011bhu nebo ch\u016fze. <br/>Te\u010f ozna\u010dte kliknut\u00edm na ikony '+' v kalend\u00e1\u0159i v\u0161echny dny a sm\u011bry, pro kter\u00e9 plat\u00ed tyto \u00fadaje.",
        choice_description_en=None,
        choice_description_cs="Chcete si zapsat: {{distance}} km b\u011bhu nebo ch\u016fze. <br/>Te\u010f ozna\u010dte kliknut\u00edm na ikony '+' v kalend\u00e1\u0159i v\u0161echny dny a sm\u011bry, pro kter\u00e9 plat\u00ed tyto \u00fadaje.",
        choice_description_dsnkcs=None,
        does_count=True,
        eco=True,
    ) as o:
        yield o


@fixture()
def by_other_vehicle(db):
    with Mom(
        "dpnk.CommuteMode",
        name="Jinak",
        name_en="Other",
        name_cs="Jinak",
        name_dsnkcs=None,
        slug="by_other_vehicle",
        order=3,
        tooltip="Komu se nelen\u00ed, tomu se kalend\u00e1\u0159 zapsan\u00fdch j\u00edzd zelen\u00ed. Kdy\u017e jedete autem \u010di tramvaj\u00ed, m\u00edsta v kalend\u00e1\u0159i \u010dervenaj\u00ed.",
        tooltip_en=None,
        tooltip_cs="Komu se nelen\u00ed, tomu se kalend\u00e1\u0159 zapsan\u00fdch j\u00edzd zelen\u00ed. Kdy\u017e jedete autem \u010di tramvaj\u00ed, m\u00edsta v kalend\u00e1\u0159i \u010dervenaj\u00ed.",
        tooltip_dsnkcs=None,
        button_html='<span class="fas fa-subway"></span>\r\n<span class="fas fa-slash fa-rotate-90"></span>\r\n <span class="fas fa-bus"></span>\r\n<span class="fas fa-slash fa-rotate-90"></span>\r\n<span class="fas fa-car"></span>',
        icon_html='<span class="fas fa-bus"></span>',
        add_command="Zapsat j\u00edzdu autem (autobusem, tramvaj\u00ed) {{direction}}.",
        add_command_en=None,
        add_command_cs="Zapsat j\u00edzdu autem (autobusem, tramvaj\u00ed) {{direction}}.",
        add_command_dsnkcs=None,
        choice_description="Chcete si zapsat: j\u00edzdu autem (autobusem, tramvaj\u00ed).<br/><br/>Te\u010f ozna\u010dte kliknut\u00edm v kalend\u00e1\u0159i v\u0161echny dny, kdy u v\u00e1s zv\u00edt\u011bzila pasivn\u00ed neekologick\u00e1 j\u00edzda do pr\u00e1ce.",
        choice_description_en=None,
        choice_description_cs="Chcete si zapsat: j\u00edzdu autem (autobusem, tramvaj\u00ed).<br/><br/>Te\u010f ozna\u010dte kliknut\u00edm v kalend\u00e1\u0159i v\u0161echny dny, kdy u v\u00e1s zv\u00edt\u011bzila pasivn\u00ed neekologick\u00e1 j\u00edzda do pr\u00e1ce.",
        choice_description_dsnkcs=None,
        does_count=True,
        eco=False,
    ) as o:
        yield o


@fixture()
def no_work(db):
    with Mom(
        "dpnk.CommuteMode",
        name="\u017d\u00e1dn\u00e1 cesta",
        name_en="No trip",
        name_cs="\u017d\u00e1dn\u00e1 cesta",
        name_dsnkcs=None,
        slug="no_work",
        order=4,
        tooltip="Bez pr\u00e1ce nejsou cesty do pr\u00e1ce.\r\n(star\u00e9 \u010d\u00ednsk\u00e9 p\u0159\u00edslov\u00ed)",
        tooltip_en=None,
        tooltip_cs="Bez pr\u00e1ce nejsou cesty do pr\u00e1ce.\r\n(star\u00e9 \u010d\u00ednsk\u00e9 p\u0159\u00edslov\u00ed)",
        tooltip_dsnkcs=None,
        button_html='<span class="fas fa-umbrella-beach"></span>',
        icon_html='<span class="fas fa-umbrella-beach"></span>',
        add_command="Zapsat volno.",
        add_command_en=None,
        add_command_cs="Zapsat volno.",
        add_command_dsnkcs=None,
        choice_description="Chcete si zapsat: den volna.<br/><br/>Te\u010f ozna\u010dte kliknut\u00edm v kalend\u00e1\u0159i v\u0161echny dny, kdy nep\u016fjdete do pr\u00e1ce.",
        choice_description_en=None,
        choice_description_cs="Chcete si zapsat: den volna.<br/><br/>Te\u010f ozna\u010dte kliknut\u00edm v kalend\u00e1\u0159i v\u0161echny dny, kdy nep\u016fjdete do pr\u00e1ce.",
        choice_description_dsnkcs=None,
        does_count=False,
        eco=True,
    ) as o:
        yield o
