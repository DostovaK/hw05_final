from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import User
from users.forms import CreationForm

User = get_user_model()


class UserCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_form_create_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Test',
            'last_name': 'Testovich',
            'username': 'test_form_user',
            'email': 'hjjdv@njcg.com',
            'password1': 'hdfsds123!',
            'password2': 'hdfsds123!',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            User.objects.count(),
            users_count + 1
        )
        self.assertTrue(
            User.objects.filter(
                username='test_form_user',
                email='hjjdv@njcg.com'
            ).exists()
        )
        self.assertRedirects(response, reverse('posts:index'))
