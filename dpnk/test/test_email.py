# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings

from dpnk import email
from dpnk.models import Campaign, City, Company, CompanyAdmin, Invoice, Phase, Subsidiary, Team, UserAttendance, UserProfile

from lxml import etree


def language_url_infix(language):
    if language == 'cs':
        return ""
    else:
        return "/en"


@override_settings(
    SITE_ID=123,
)
class TestEmails(TestCase):
    def setUp(self):
        Site.objects.create(domain="dopracenakole.cz", id=123)
        self.campaign = Campaign.objects.create(name="Testing campaign 1", slug="dpnk", email_footer="""
        <p>
Soutěž Do práce na kole 2019 pořádá spolek Auto*Mat ve spolupráci s Pavel Bednařík/Olomouc, Brdonoš/Příbram,
BajkAzyl/Hradec Králové, Cyklisté Liberecka, CykloBudějovice, Cykloklub Kučera/Znojmo, CykloZlín, HAGA Pardubice,
Hranická rozvojová agentura, Plzeň na kole, z.s., SlibyChyby/Jihlava, Nadace Partnerství/Brno,
O-KOLO Hradiště a dále městskými úřady: Břeclav, Hradec Králové, Ostrava, Jihlava, Jindřichův Hradec, Karviná, Most,
Nový Jičín, Říčany, Třebíč, Rožnov pod Radhoštěm, Ústí nad Labem, Znojmo a Žďár nad Sázavou.
</p><p>
Za finanční a mediální podporu děkujeme generálnímu logistickému partnerovi společnosti GLS CZ, Magistrátu hlavního města Prahy,
Velvyslanectví Nizozemského království, společnostem OP TIGER, CK Kudrna, Ortlieb, Hello bank! a mediálnímu partnerům RunCzech,
Běhej․com, Kolo pro život, Dopravní Jednička, Radio Wave, iVelo, Wavemaker,Youradio a Cykloserver,  Urban cyclers,
Kondice, Superlife, Prazdroj Lidem
</p>
            <strong>Soutěž zaštiťuje nezisková organizace <a href="https://www.auto-mat.cz">Auto*Mat</a></strong> <br />
            Neváhejte nás kontaktovat na e-mail <a href="mailto:kontakt@dopracenakole.cz">kontakt@dopracenakole.cz</a><br/>
            nebo zavolejte na telefon 234&nbsp;697&nbsp;810<br />
        """)
        self.phase = Phase.objects.create(
            date_from=datetime.date(year=2010, month=10, day=20),
            date_to=datetime.date(year=2010, month=11, day=20),
            campaign=self.campaign, phase_type='competition',
        )
        self.city = City.objects.create(name="Testing City", slug="testing_city")

        self.company = Company.objects.create(name="Testing Company")
        self.subsidiary = Subsidiary.objects.create(company=self.company, city=self.city)
        self.team = Team.objects.create(name="Testing team", campaign=self.campaign, subsidiary=self.subsidiary)

        self.user = User.objects.create(first_name="Test", last_name="User", username="user1", email="user1@email.com")
        self.userprofile = UserProfile.objects.create(sex='male', user=self.user)
        self.user_attendance = UserAttendance.objects.create(
            userprofile=self.userprofile,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.user_tm1 = User.objects.create(first_name="Team", last_name="Member 1", username="user2", email="user2@email.com")
        self.userprofile_tm1 = UserProfile.objects.create(user=self.user_tm1, language='cs')
        self.user_attendance_tm1 = UserAttendance.objects.create(
            userprofile=self.userprofile_tm1,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.user_tm2 = User.objects.create(first_name="Team", last_name="Member 2", username="user3", email="user3@email.com")
        self.userprofile_tm2 = UserProfile.objects.create(user=self.user_tm2, language='en')
        self.user_attendance_tm2 = UserAttendance.objects.create(
            userprofile=self.userprofile_tm2,
            campaign=self.campaign,
            team=self.team,
            approved_for_team='approved',
        )

        self.company_admin = CompanyAdmin.objects.create(
            userprofile=self.user.userprofile,
            administrated_company=self.company,
            campaign=self.campaign,
            company_admin_approved='undecided',
        )
        self.invoice = Invoice.objects.create(company=self.company, campaign=self.campaign)

        self.parser = etree.XMLParser(resolve_entities=False)
        mail.outbox = []

    def test_send_approval_request_mail(self):
        email.approval_request_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - žádost o ověření členství")
        self.assertInHTML('<title>Testing campaign 1 - žádost o ověření členství</title>', mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[1].subject, "Testing campaign 1 - membership verification request")
        self.assertInHTML('<title>Testing campaign 1 - membership verification request</title>', mail.outbox[1].alternatives[0][0])
        self.assertEqual(mail.outbox[0].to[0], "user2@email.com")
        self.assertEqual(mail.outbox[1].to[0], "user3@email.com")
        etree.fromstring(mail.outbox[0].alternatives[0][0], self.parser)
        etree.fromstring(mail.outbox[1].alternatives[0][0], self.parser)

    def test_send_invitation_register_mail(self):
        email.invitation_register_mail(self.user_attendance, self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/tym/%s/user1@email.com/' % (
            language_url_infix(self.userprofile.language),
            self.user_attendance.team.invitation_token,
        )
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            html_message = (
                '<p>Test User si myslí, že je dnes perfektní den pro jízdu na kole. '
                'Proto Vám posílá pozvánku do svého týmu Testing team v soutěži Testing campaign 1.</p>'
            )
        else:
            html_message = '<p>Fellow colleague Test User wants to ride the bicycle with You in the Testing team team.</p>'
        self.assertInHTML(html_message, msg.alternatives[0][0])
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_register_mail(self):
        email.register_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/' % (language_url_infix(self.userprofile.language))
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            html_message = '<li>Zapamatujte si, že soutěž začíná 20. října 2010 a končí 20. listopadu 2010.</li>'
        else:
            html_message = '<p>Our ride begins at Oct. 20, 2010 and finishes at Nov. 20, 2010.</p>'
        self.assertInHTML(html_message, msg.alternatives[0][0])
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_unfilled_rides_notification(self):
        email.unfilled_rides_mail(self.user_attendance, 5)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(str(msg.subject), "Testing campaign 1 - připomenutí nevyplněných jízd")
        else:
            self.assertEqual(str(msg.subject), "Testing campaign 1 - Unfilled rides notification")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/' % (language_url_infix(self.userprofile.language))
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            message = "Už je to 5 dní a žádná nová jízda."
        else:
            message = "it's been 5 days since You last updated your rides."
        self.assertTrue(message in msg.body)
        if self.userprofile.language == 'cs':
            message = "Jízdy můžete vyplňovat pouze 7 dní zpětně,"
        else:
            message = "You can fill in the rides only for 7 days"
        self.assertTrue(message in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_team_membership_approval_mail(self):
        email.team_membership_approval_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení ověření členství v týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - team membership verification confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_team_membership_denial_mail(self):
        email.team_membership_denial_mail(self.user_attendance, self.user_attendance, "reason of denial")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - ZAMÍTNUTÍ členství v týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - Team membership DENIED")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/tym/' % (language_url_infix(self.userprofile.language))
        self.assertTrue(link in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_team_created_mail(self):
        email.team_created_mail(self.user_attendance, 'Foo team')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - potvrzení vytvoření týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - team creation confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/pozvanky/' % (language_url_infix(self.userprofile.language))
        self.assertTrue(link in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_invitation_mail(self):
        email.invitation_mail(self.user_attendance, "email@email.com")
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - pozvánka do týmu")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - you've been invited to join a team")
        self.assertEqual(msg.from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(msg.to[0], "email@email.com")
        link = 'https://dpnk.dopracenakole.cz%s/registrace/%s/email@email.com/' % (
            language_url_infix(self.userprofile.language),
            self.user_attendance.team.invitation_token,
        )
        self.assertTrue(link in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_payment_confirmation_mail(self):
        email.payment_confirmation_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - přijetí platby")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - payment received")
        self.assertEqual(msg.to[0], "user1@email.com")
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_payment_confirmation_company_mail(self):
        email.payment_confirmation_company_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - přijetí platby")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - payment received")
        self.assertEqual(msg.to[0], "user1@email.com")
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_company_admin_register_competitor_mail(self):
        email.company_admin_register_competitor_mail(self.user_attendance)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            self.assertEqual(msg.subject, "Testing campaign 1 - firemní koordinátor - potvrzení registrace")
        else:
            self.assertEqual(msg.subject, "Testing campaign 1 - Company Coordinator - registration confirmation")
        self.assertEqual(msg.to[0], "user1@email.com")
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_company_admin_register_no_competitor_mail(self):
        email.company_admin_register_no_competitor_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - potvrzení registrace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - registration confirmation")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Dobrý den, Teste\n\npřišla nám zpráva, že se chcete stát firemním koordinátorem organizace Testing\nCompany."
        else:
            message = "Hello, brave Test\n\nthank You for applying. We wish Your dream will come true and You will become"
        self.assertTrue(message in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_company_admin_approval_mail(self):
        email.company_admin_approval_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - schválení správcovství organizace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - company administration approval")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        link = 'https://dpnk.dopracenakole.cz%s/spolecnost/editovat_spolecnost/' % (language_url_infix(self.userprofile.language))
        self.assertTrue(link in msg.body)
        if self.userprofile.language == 'cs':
            message = "Dobrý den, Teste\n\ngratulujeme! Nyní zastupujete společnost Testing Company jako firemní"
        else:
            message = "Congratulations, Test\n\nYou are the Testing Company company coordinator."
        self.assertTrue(message in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_send_company_admin_rejected_mail(self):
        email.company_admin_rejected_mail(self.company_admin)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - firemní koordinátor - zamítnutí správcovství organizace")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Company Coordinator - administrative role denied")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            message = "Dobrý den, Teste\n\nsesedněte z kola, máme pro Vás důležitou zprávu. Nemohli jsme potvrdit Vaši"
        else:
            message = "Sad news, Test\n\nas You already know, we cannot make You a Testing campaign 1 company"
        self.assertTrue(message in msg.body)
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_new_invoice_mail(self):
        email.new_invoice_mail(self.invoice)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - byla Vám vystavena faktura")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - Your invoice has been prepared")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            html_message = '<p>Kompletní přehled faktur najdete ve svém <a href="https://dpnk.dopracenakole.cz/faktury/">profilu</a>.</p>'
        else:
            html_message = '<p>All invoices are guarded in Your <a href="https://dpnk.dopracenakole.cz/en/faktury/">profile</a>.</p>'
        self.assertInHTML(html_message, msg.alternatives[0][0])
        etree.fromstring(msg.alternatives[0][0], self.parser)

    def test_unpaid_invoice_mail(self):
        email.unpaid_invoice_mail(self.invoice)
        self.assertEqual(len(mail.outbox), 1)
        if self.userprofile.language == 'cs':
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - připomenutí nezaplacené faktury")
        else:
            self.assertEqual(mail.outbox[0].subject, "Testing campaign 1 - reminder about unpaid invoice")
        self.assertEqual(mail.outbox[0].to[0], "user1@email.com")
        msg = mail.outbox[0]
        if self.userprofile.language == 'cs':
            html_message = '<p>Všechny faktury můžete zkontrolovat na Vašem <a href="https://dpnk.dopracenakole.cz/faktury/">profilu</a>.</p>'
        else:
            html_message = '<p>You can also check all invoices in <a href="https://dpnk.dopracenakole.cz/en/faktury/">Your profile</a>.</p>'
        self.assertInHTML(html_message, msg.alternatives[0][0])
        etree.fromstring(msg.alternatives[0][0], self.parser)


class TestEmailsEn(TestEmails):
    def setUp(self):
        super().setUp()
        self.userprofile.language = "en"
        self.company_admin.userprofile.language = "en"
        self.userprofile.save()
        self.company_admin.userprofile.save()
