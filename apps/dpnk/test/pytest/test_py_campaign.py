def test_campaign_str(campaign, benchmark):
    cs = benchmark(str, campaign)
    assert cs == "CT1 2021"
