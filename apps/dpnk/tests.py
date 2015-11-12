from django.test import TestCase, RequestFactory
try:
    from django.test.utils import override_settings
except ImportError:
    from subdomains.compat.tests import override_settings
from subdomains.utils import reverse


class AdminFilterTests(TestCase):
    fixtures = ['testdata']

    def setUp(self):
                # Every test needs access to the request factory.
        self.factory = RequestFactory()

    @override_settings(
        SUBDOMAIN_URLCONFS={
            None: 'project.urls',
            'testing-campaign': 'project.urls',
        },
    )
    def run(self, *args, **kwargs):
        super(AdminFilterTests, self).run(*args, **kwargs)

    def test_admin_views(self):
        """
        test if the admin pages work
        """
        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(reverse("admin:dpnk_userattendance_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_dpnk_views_no_login(self):
        response = self.client.get(reverse('registrace', subdomain='testing-campaign'))
        print response
        self.assertEqual(response.status_code, 200)

    def test_dpnk_views(self):
        """
        test if the user pages work
        """
        self.assertTrue(self.client.login(username='test', password='test'))
        response = self.client.get(reverse('upravit_profil', subdomain='testing-campaign'))
        self.assertEqual(response.status_code, 200)
