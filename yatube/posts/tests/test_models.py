from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class ProjectModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.expected_verbose_name = {
            'author': 'Автор',
            'group': 'Группа',
        }
        cls.expected_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

    def test_model_correct_object_name(self):
        """Проверяем, что у модели корректно работает __str__."""
        post = ProjectModelsTest.post
        group = ProjectModelsTest.group
        expected_name = {
            post: post.text[:settings.SHAWN_SYMBOLS],
            group: group.title,
        }
        for model, expected_value in expected_name.items():
            with self.subTest(model=model):
                self.assertEqual(
                    expected_value,
                    str(model)
                )

    def test_verbose_name_post(self):
        """Проверяем, что у модели Post корректно работает verbose_name."""
        task = ProjectModelsTest.post
        for field, expected_value in self.expected_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_post(self):
        """Проверяем, что у модели Post корректно работает help_text."""
        task = ProjectModelsTest.post
        for field, expected_value in self.expected_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    task._meta.get_field(field).help_text,
                    expected_value
                )
