# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2016 o.s. Auto*Mat
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
from unittest.mock import MagicMock, patch

from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from dpnk.templatetags import dpnk_tags

from model_mommy import mommy

import slumber


@override_settings(
    FAKE_DATE=datetime.date(year=2016, month=11, day=20),
)
class DpnkTagsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.campaign = mommy.make("Campaign", wp_api_date_from="2017-01-01")
        self.city = mommy.make("City", name="City", slug="test_city")
        self.factory = RequestFactory()

    @patch('slumber.API')
    def test_no_news(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = ()
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% wp_news campaign city %}")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            feed="content_to_backend",
            _number=5,
            _connected_to='test_city',
            _post_type="post",
            order="DESC",
            orderby="DATE",
            _from='2017-01-01',
        )
        self.assertHTMLEqual(response, '')

    @patch('dpnk.templatetags.dpnk_tags.logger')
    @patch('slumber.API')
    def test_failed_wp_news(self, slumber_mock, mock_logger):
        m = MagicMock()
        m.feed.get.side_effect = slumber.exceptions.SlumberBaseException
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}<div>{% wp_news campaign city %}</div>")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        mock_logger.exception.assert_called_with("Error fetching wp news")
        m.feed.get.assert_called_once_with(
            feed="content_to_backend",
            _number=5,
            _connected_to="test_city",
            _post_type="post",
            order="DESC",
            orderby="DATE",
            _from='2017-01-01',
        )
        self.assertHTMLEqual(response, '<div></div>')

    @patch('dpnk.templatetags.dpnk_tags.logger')
    @patch('slumber.API')
    def test_failed_wp_news_type_error(self, slumber_mock, mock_logger):
        m = MagicMock()
        m.feed.get.return_value = {'Test1': 'Test'}
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}<div>{% wp_news campaign city %}</div>")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            feed="content_to_backend",
            _number=5,
            _connected_to='test_city',
            _post_type="post",
            order="DESC",
            orderby="DATE",
            _from='2017-01-01',
        )
        mock_logger.exception.assert_called_with("Error encoding wp news format", extra={'wp_feed': {'Test1': 'Test'}})
        self.assertHTMLEqual('<div/>', response)

    @patch('slumber.API')
    def test_wp_news_no_slug(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = (
            {
                'published': '2010-01-01',
                'start_date': '2010-01-01',
                'url': 'http://www.test.cz',
                'title': 'Testing title',
                'excerpt': 'Testing excerpt',
                'image': 'http://www.test.cz',
            },
        )
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% wp_news campaign %}")
        context = Context({'campaign': self.campaign})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            _number=5,
            _connected_to=None,
            feed="content_to_backend",
            _post_type="post",
            order="DESC",
            orderby="DATE",
            _from='2017-01-01',
            _global_news=1,
        )
        self.assertHTMLEqual(
            response,
            '''
            <h3>Novinky</h3>
            <div class="wp_news">
               <div class="item">
                  <h4>
                      <a href="http://www.test.cz" target="_blank">
                          Testing title
                      </a>
                  </h4>
                  <span class=""><img src="http://www.test.cz" alt="Obrázek k podnětu"></span>
                  Testing excerpt
               </div>
            </div>
            ''',
        )

    @patch('slumber.API')
    def test_wp_news(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = (
            {
                'published': '2010-01-01',
                'start_date': '2010-01-01',
                'url': 'http://www.test.cz',
                'title': 'Testing title',
                'excerpt': 'Testing excerpt',
                'image': 'http://www.test.cz',
            },
        )
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% wp_news campaign city %}")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            _number=5,
            feed="content_to_backend",
            _post_type="post",
            _connected_to="test_city",
            order="DESC",
            orderby="DATE",
            _from='2017-01-01',
        )
        self.assertHTMLEqual(
            response,
            '''
            <h3>
            Novinky ve městě<a href="http://www.dopracenakole.cz/locations/test_city">City</a>
            </h3>
            <div class="wp_news">
               <div class="item">
                  <h4>
                      <a href="http://www.test.cz" target="_blank">
                          Testing title
                      </a>
                  </h4>
                  <span class=""><img src="http://www.test.cz" alt="Obrázek k podnětu"></span>
                  Testing excerpt
               </div>
            </div>
            ''',
        )

    @patch('slumber.API')
    def test_wp_actions(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = (
            {
                'published': '2010-01-01',
                'start_date': '2010-01-01',
                'url': 'http://www.test.cz',
                'title': 'Testing title',
                'excerpt': 'Testing excerpt',
                'image': 'http://www.test.cz',
            },
        )
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% wp_actions campaign city %}")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            _number=5,
            feed="content_to_backend",
            _page_subtype="event",
            _post_type="locations",
            _post_parent="test_city",
            orderby="start_date",
            _from='2017-01-01',
        )
        self.assertHTMLEqual(
            response,
            '''
            <h3>
            Akce ve městě<a href="http://www.dopracenakole.cz/locations/test_city">
            City
            </a>
            </h3>
            <div class="wp_news">
               <div class="item">
                  <h4>
                      <a href="http://www.test.cz" target="_blank">
                          Testing title
                      </a>
                  </h4>
                  <span class=""><img src="http://www.test.cz" alt="Obrázek k podnětu"></span>
                  Testing excerpt
               </div>
            </div>
            ''',
        )

    @patch('slumber.API')
    def test_wp_prize(self, slumber_mock):
        m = MagicMock()
        m.feed.get.return_value = (
            {
                'published': '2010-01-01',
                'start_date': '2010-01-01',
                'url': 'http://www.test.cz',
                'title': 'Testing title',
                'excerpt': 'Testing excerpt',
                'image': 'http://www.test.cz',
            },
        )
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% wp_prize campaign city %}")
        context = Context({'campaign': self.campaign, 'city': self.city})
        response = template.render(context)
        m.feed.get.assert_called_once_with(
            _number=8,
            feed="content_to_backend",
            _page_subtype="prize",
            _post_type="locations",
            _post_parent="test_city",
            order="ASC",
            orderby='menu_order',
            _from='2017-01-01',
        )
        self.assertHTMLEqual(
            response,
            '''
            <h3>
            Ceny ve městě<a href="http://www.dopracenakole.cz/locations/test_city">City</a>
            </h3>
            <div class="wp_news">
               <div class="item">
                  <h4>
                      <a href="http://www.test.cz" target="_blank">
                          Testing title
                      </a>
                  </h4>
                  <span class="bobble"><img src="http://www.test.cz" alt="Obrázek k podnětu"></span>
               </div>
            </div>
            ''',
        )

    @patch('dpnk.templatetags.dpnk_tags.logger')
    @patch('slumber.API')
    def test_cyklistesobe_fail(self, slumber_mock, mock_logger):
        m = MagicMock()
        m.issues.get.side_effect = slumber.exceptions.SlumberBaseException
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}<div>{% cyklistesobe 'test_slug' %}</div>")
        context = Context()
        response = template.render(context)
        mock_logger.exception.assert_called_with("Error fetching cyklistesobe page")
        self.assertHTMLEqual(response, '<div></div>')

    @patch('slumber.API')
    def test_cyklistesobe(self, slumber_mock):
        m = MagicMock()
        m.issues.get.return_value = {
            'features': (
                {
                    'properties': {
                        'cyclescape_url': 'http://test-url.cz',
                        'title': 'Test title',
                        'vote_count': '5',
                        'description': 'Description',
                        'photo_thumb_url': '/image.png',
                    },
                },
            ),
        }
        slumber_mock.return_value = m
        template = Template("{% load dpnk_tags %}{% cyklistesobe 'test_slug' %}")
        context = Context()
        response = template.render(context)
        m.issues.get.assert_called_once_with(group="test_slug", order="created_at", page=0, per_page=5)
        self.assertHTMLEqual(
            response,
            '''
            <div class="cyklistesobe">
                <h4>
                  <a href="http://test-url.cz" target="_blank">
                      Test title
                      <span class="vote">5</span>
                  </a>
                </h4>
                <img src="https://www.cyklistesobe.cz/image.png" alt="Obrázek k podnětu">
                Description
            </div>
            ''',
        )


class UnquoteHtmlTests(TestCase):
    def test_direct(self):
        self.assertEqual(dpnk_tags.unquote_html('&lt;&gt;'), '<>')


class ChangeLangTests(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_direct(self):
        self.assertEqual(dpnk_tags.change_lang(Context(), lang='en'), '/en')

    def test_change_lang(self):
        template = Template("{% load dpnk_tags %}{% change_lang 'en' %}")
        context = Context()
        response = template.render(context)
        self.assertHTMLEqual(response, '/en')

    def test_change_lang_request_fail(self):
        template = Template("{% load dpnk_tags %}{% change_lang 'en' %}")
        request = self.factory.get(reverse("team_members"))
        context = Context({'request': request})
        response = template.render(context)
        self.assertHTMLEqual(response, '/en/dalsi_clenove/')

    @patch('dpnk.templatetags.dpnk_tags.logger')
    def test_change_lang_request(self, mock_logger):
        template = Template("{% load dpnk_tags %}{% change_lang 'en' %}")
        request = self.factory.get("test")
        context = Context({'request': request})
        response = template.render(context)
        mock_logger.exception.assert_called_with('Error in change lang function', extra={'resolved_path': '/test'})
        self.assertHTMLEqual(response, '/en')

    def test_change_lang_request_no_reverse_match(self):
        template = Template("{% load dpnk_tags %}{% change_lang 'en' %}")
        address = reverse('admin:dpnk_competition_change', args=(6,))
        request = self.factory.get(address)
        context = Context({'request': request})
        response = template.render(context)
        self.assertHTMLEqual(response, '/admin/dpnk/competition/6/change/')


class RoundNumberTests(TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_direct(self):
        self.assertEqual(dpnk_tags.round_number(2.123456), 2.1)

    def test_without_parameters(self):
        template = Template("{% load dpnk_tags %}{{ i|round_number }}")
        context = Context({"i": 2.123456})
        response = template.render(context)
        self.assertHTMLEqual(response, '2,1')

    def test_without_three_places(self):
        template = Template("{% load dpnk_tags %}{{ i|round_number:3 }}")
        context = Context({"i": 2.123456})
        response = template.render(context)
        self.assertHTMLEqual(response, '2,123')

    def test_none(self):
        template = Template("{% load dpnk_tags %}{{ i|round_number:3 }}")
        context = Context({"i": None})
        response = template.render(context)
        self.assertHTMLEqual(response, 'None')

    def test_no_number(self):
        template = Template("{% load dpnk_tags %}{{ i|round_number:3 }}")
        context = Context({"i": "foo"})
        response = template.render(context)
        self.assertHTMLEqual(response, 'foo')
