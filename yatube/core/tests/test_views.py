from django.test import Client, TestCase
from django.urls import reverse


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expected_template = {
            reverse(
                'posts:group_list',
                kwargs={'slug': 'not_existing'}
            ): 'core/404.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.expected_template.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
