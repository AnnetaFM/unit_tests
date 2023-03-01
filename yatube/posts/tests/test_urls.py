from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='UserAutorized'
        )
        cls.user_author = User.objects.create_user(
            username='UserAuthor'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группц',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_author,
            group=cls.group,
        )
        cls.public_url_names = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.post.author.username}/',
            f'/posts/{cls.post.id}/',
        ]
        cls.private_url_names = [
            '/create/',
            f'/posts/{cls.post.id}/edit/',
        ]
        cls.public_templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
        }
        cls.private_templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user_author)

    def test_public_pages_by_guest(self):
        """Проверка доступности публичных адресов учеткой гостя."""
        for address in self.public_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_pages_by_guest(self):
        """Проверка доступности приватных адресов учеткой гостя."""
        for address in self.private_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response,
                                     f'{reverse("login")}?next={address}'
                                     )

    def test_edit_page_for_author(self):
        """Проверка возможности автора редактировать пост."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_for_authorized_client(self):
        """Проверка возможности авторизированного пользователя содать пост."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_uses_correct_templates(self):
        """Проверка соответствия шаблонов для публичных адресов."""
        for address, template in self.public_templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_templates(self):
        """Проверка соответствия шаблонов для приватных адресов."""
        for address, template in self.private_templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redaction_post_by_not_author(self):
        """Проверка доступности редактирования поста не автором."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_at_desired_location(self):
        """Проверка несуществующей страницы."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
