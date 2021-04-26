from model_mommy import mommy
import pytest

from dpnk.models import Campaign, CampaignType


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
