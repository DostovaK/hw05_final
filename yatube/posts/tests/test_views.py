import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=PostsPagesTests.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.group_with_post = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group_with_post,
            image=cls.uploaded
        )
        cls.group_without_posts = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug_2',
            description='Тестовое описание 2',
        )
        cls.expected_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'pk': PostsPagesTests.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'pk': PostsPagesTests.post.pk}
            ): 'posts/post_create.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.post.author.username}
            ): 'posts/profile.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        cls.urls = [
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.post.author}
            )
        ]
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ChoiceField,
            'image': forms.fields.ImageField,
        }
        cls.expected_redirections = {
            reverse('posts:post_create'):
                (reverse('users:login') + '?next=/create/'),
            reverse('posts:post_edit', kwargs={'pk': PostsPagesTests.post.pk}):
                (reverse('users:login') + '?next='
                 + reverse(
                     'posts:post_edit', kwargs={'pk': PostsPagesTests.post.pk}
                )),
            reverse(
                'posts:add_comment', kwargs={'pk': PostsPagesTests.post.pk}
            ): (reverse('users:login') + '?next='
                + reverse(
                    'posts:add_comment', kwargs={'pk': PostsPagesTests.post.pk}
            )),
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsPagesTests.post.author.username}
            ): (reverse('users:login') + '?next='
                + reverse(
                    'posts:profile_follow',
                    kwargs={'username': PostsPagesTests.post.author.username}
            )),
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsPagesTests.post.author.username}
            ): (reverse('users:login') + '?next='
                + reverse(
                    'posts:profile_unfollow',
                    kwargs={'username': PostsPagesTests.post.author.username}
            )),
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.post.author)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.expected_template.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def attributes_for_context_tests(self, post):
        self.assertEqual(post.text, PostsPagesTests.post.text)
        self.assertEqual(post.author, PostsPagesTests.post.author)
        self.assertEqual(post.group, PostsPagesTests.post.group)
        self.assertEqual(post.image, PostsPagesTests.post.image)

    def test_index_profile_shows_correct_context(self):
        """Шаблоны index и profile сформированы с правильным контекстом."""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.attributes_for_context_tests(
                    response.context['page_obj'][0]
                )

    def test_group_list_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group_with_post.slug}
            )
        )
        group = response.context['group']
        self.assertEqual(group.title, PostsPagesTests.group_with_post.title)
        self.assertEqual(group.slug, PostsPagesTests.group_with_post.slug)
        self.assertEqual(
            group.description,
            PostsPagesTests.group_with_post.description
        )
        self.attributes_for_context_tests(response.context['page_obj'][0])

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'pk': PostsPagesTests.post.pk}
            )
        )
        self.attributes_for_context_tests(response.context['post'])

    def test_post_edit_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={'pk': PostsPagesTests.post.pk}
            )
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_shows_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_guest_redirection(self):
        """
        Запрошенная страница перенаправляет неавторизованного пользователя.
        """
        for url, expected_value in self.expected_redirections.items():
            with self.subTest(url=url):
                self.assertRedirects(
                    self.guest_client.get(url, follow=True),
                    expected_value
                )

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug_2'}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_add_comment(self):
        """Авторизованный пользователь может оставлять комментарии."""
        form_data = {
            'text': 'Test comment',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'pk': PostsPagesTests.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Test comment',
                author=PostsPagesTests.user
            ).exists()
        )


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_POST_QUANTITY = 14
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post.objects.create(
                text=f'Тестовый пост для пагинатора {i}',
                author=cls.user,
                group=cls.group,
            ) for i in range(cls.TEST_POST_QUANTITY)
        ]
        cls.urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTests.user}
            )
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTests.user)

    def test_first_page_contains_ten_records(self):
        """На первой странице выводится десять постов"""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE
                )

    def test_second_page_contains_remaining_records(self):
        """На второй странице выводится десять постов"""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.TEST_POST_QUANTITY - settings.POSTS_PER_PAGE
                )


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_works_index_page(self):
        """Кэширование страницы index."""
        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Cache test',
            author=CacheTests.user,
        )
        cache.clear()
        new_response = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response.context, new_response.context)

    def test_cache_works_index_page_after_post_delete(self):
        """Кэширование страницы index после удаления поста."""
        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(pk=CacheTests.post.pk).delete()
        new_response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, new_response.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='test_user')
        cls.user_following = User.objects.create_user(username='test_user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый пост',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_authorized_user_able_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        followers_count = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count + 1)

    def test_authorized_user_able_unfollow(self):
        """Авторизованный пользователь может отписаться
        от других пользователей."""
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        followers_count = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.count(), followers_count - 1)

    def test_new_post_see_only_follower(self):
        """Новый пост появляется только в ленте подписавшихся."""
        response = self.following_client.get(reverse('posts:follow_index'))
        self.assertNotIn(FollowTests.post, response.context['page_obj'])
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowTests.user_following.username}
            )
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertIn(FollowTests.post, response.context['page_obj'])
