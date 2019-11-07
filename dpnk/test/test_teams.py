from django.core.exceptions import ValidationError
from django.test import TestCase

from dpnk import models

from model_mommy import mommy


class TestTeams(TestCase):
    def setUp(self):
        self.campaign = mommy.make(models.Campaign, max_team_members=3)
        self.campaign.save()
        subsidiary = mommy.make(models.Subsidiary)
        self.team = mommy.make(models.Team, subsidiary=subsidiary, campaign=self.campaign)
        self.team.save()

    def test_team_filling_all_approved(self):
        campaign = self.campaign
        team = self.team
        up1 = mommy.make(models.UserProfile)
        up1.save()
        ua1 = models.UserAttendance(userprofile=up1, campaign=campaign, team=team, approved_for_team='approved')
        up2 = mommy.make(models.UserProfile)
        up2.save()
        ua2 = models.UserAttendance(userprofile=up2, campaign=campaign, team=team, approved_for_team='approved')
        up3 = mommy.make(models.UserProfile)
        up3.save()
        ua3 = models.UserAttendance(userprofile=up3, campaign=campaign, team=team, approved_for_team='approved')
        up4 = mommy.make(models.UserProfile)
        up4.save()
        ua4 = models.UserAttendance(userprofile=up4, campaign=campaign, team=team, approved_for_team='approved')
        ua1.save()
        ua1.clean()
        ua2.save()
        ua2.clean()
        ua3.save()
        ua3.clean()
        ua4.save()
        with self.assertRaises(ValidationError):
            ua4.clean()

    def test_team_filling_with_undecided(self):
        campaign = self.campaign
        team = self.team
        up1 = mommy.make(models.UserProfile)
        up1.save()
        ua1 = models.UserAttendance(userprofile=up1, campaign=campaign, team=team, approved_for_team='approved')
        up2 = mommy.make(models.UserProfile)
        up2.save()
        ua2 = models.UserAttendance(userprofile=up2, campaign=campaign, team=team, approved_for_team='undecided')
        up3 = mommy.make(models.UserProfile)
        up3.save()
        ua3 = models.UserAttendance(userprofile=up3, campaign=campaign, team=team, approved_for_team='approved')
        up4 = mommy.make(models.UserProfile)
        up4.save()
        ua4 = models.UserAttendance(userprofile=up4, campaign=campaign, team=team, approved_for_team='approved')
        up5 = mommy.make(models.UserProfile)
        up5.save()
        ua5 = models.UserAttendance(userprofile=up5, campaign=campaign, team=team, approved_for_team='approved')
        ua1.save()
        ua1.clean()
        ua2.save()
        ua2.clean()
        ua3.save()
        ua3.clean()
        ua4.save()
        ua4.clean()
        ua5.save()
        with self.assertRaises(ValidationError):
            ua5.clean()
