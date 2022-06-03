from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expected_template = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса статичных страниц."""
        for url in self.expected_template.keys():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов статичных страниц."""
        for reverse_name, template in self.expected_template.items():
            with self.subTest(template=template):
                self.assertTemplateUsed(
                    self.guest_client.get(reverse_name),
                    template
                )
