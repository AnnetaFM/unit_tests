from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authoraized_user = User.objects.create_user(
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
        cls.status_code_url_names = {
            '/': 200,
            f'/group/{cls.group.slug}/': 200,
            f'/profile/{cls.post.author.username}/': 200,
            f'/posts/{cls.post.pk}/': 200,
            '/unexisting_page/': 404,
        }
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.authoraized_user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user_author)

    def test_unuathorized_client_try_pages(self):
        for address, status_code in self.status_code_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_unuathorized_client_try_to_create_post(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_redirect_unuathorized_client(self):
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/', follow=True)
        self.assertRedirects(
            response, (
                f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/')
        )

    def test_uathorized_client_try_to_create_post(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(
            response.status_code, 200
        )

    def test_redirect_uathorized_client_to_post_page(self):
        url_names = {
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response, f'/auth/login/?next={address}'
                )

    def test_author_can_edit_post(self):
        response = self.author_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_urls_use_correct_templates(self):
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
