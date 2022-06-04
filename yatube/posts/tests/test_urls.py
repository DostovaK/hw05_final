from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.urls = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            f'/profile/{PostsURLTests.post.author.username}/': HTTPStatus.OK,
            f'/posts/{PostsURLTests.post.pk}/': HTTPStatus.OK,
            '/anything_not_existing/': HTTPStatus.NOT_FOUND,
            '/follow/': HTTPStatus.FOUND,
            f'/posts/{PostsURLTests.post.pk}/comment/': HTTPStatus.FOUND,
            f'/profile/{PostsURLTests.post.author.username}/follow/':
                HTTPStatus.FOUND,
            f'/profile/{PostsURLTests.post.author.username}/unfollow/':
                HTTPStatus.FOUND
        }
        cls.expected_urls_code = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'pk': PostsURLTests.post.pk})
        ]
        cls.expected_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'pk': PostsURLTests.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'pk': PostsURLTests.post.pk}
            ): 'posts/post_create.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsURLTests.post.author.username}
            ): 'posts/profile.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client.force_login(self.user)

    def test_urls_exist_in_expected_location(self):
        """Проверяем доступность страниц любым пользователям."""
        for url, status_code in self.urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code,
                    status_code
                )

    def test_post_id_redirects_nonauthor(self):
        """
        Страница /posts/post_id/edit/ перенаправляет пользователя-неавтора
        на страницу просмотра поста.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'pk': PostsURLTests.post.pk}),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'pk': PostsURLTests.post.pk})
        )

    def test_post_create_and_edit_for_authorized_client_or_author(self):
        """
        Страница доступна авторизованному пользователю и/или автору поста.
        """
        self.authorized_client.force_login(PostsURLTests.post.author)
        for url in self.expected_urls_code:
            with self.subTest(url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.authorized_client.force_login(PostsURLTests.post.author)
        for url, expected_value in self.expected_template.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.authorized_client.get(url),
                    expected_value
                )
