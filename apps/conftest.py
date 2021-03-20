from  dpnk.models import Campaign, CampaignType
import pytest


@pytest.fixture(scope='function')
def campaign_type(db):
    o = CampaignType.objects.create(
        name="CT1",
        slug="ct1",
    )
    yield o
    o.delete()


@pytest.fixture(scope='function')
def campaign(campaign_type):
    o = Campaign.objects.create(
        campaign_type=campaign_type,
        year="2021",
        slug="c",
        slug_identifier="c2021",
    )
    yield o
    o.delete()
