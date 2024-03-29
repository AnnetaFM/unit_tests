from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': cls.post.author.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': cls.post.id}): 'posts/post_detail.html',
            reverse('posts:edit', kwargs={
                'post_id': cls.post.id}): 'posts/create_post.html',
            reverse('posts:create'): 'posts/create_post.html',
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post_info(self, post):
        """Информация о посте корректна."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

    def test_pages_uses_correct_template(self):
        """Views-функции используют правильные html-шаблоны."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Сontext в шаблоне index.html соответствует ожиданиям."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.check_post_info(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Сontext в шаблоне group_list.html соответствует ожиданиям."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_info(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Сontext в шаблоне profile.html соответствует ожиданиям."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.context['author'], self.user)
        self.check_post_info(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Сontext в шаблоне post_detail.html соответствует ожиданиям."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        self.check_post_info(response.context['post'])

    def test_forms_for_create_posts(self):
        """Сontext в шаблоне create_post.html соответствует ожиданиям."""
        context = [
            reverse('posts:create'),
            reverse('posts:edit', kwargs={'post_id': self.post.id})
        ]
        for reverse_page in context:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIsInstance(
                    response.context['form'].fields['text'],
                    forms.fields.CharField)
                self.assertIsInstance(
                    response.context['form'].fields['group'],
                    forms.fields.ChoiceField)

    def test_showing_post_on_pages(self):
        """Проверка отображения поста на выделенных страницах."""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_not_in_wrong_group(self):
        """Проверка, что пост в нужной группе."""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.number_of_posts = 13
        cls.posts_on_first_page = 10
        cls.posts_on_second_page = 3
        cls.url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
        ]
        cls.post = []
        for _ in range(0, cls.number_of_posts):
            cls.post.append(Post(author=cls.user, group=cls.group))
        Post.objects.bulk_create(cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_on_pages(self):
        """Проверка пагинации."""
        for reverse_ in self.url_pages:
            with self.subTest(reverse_=reverse_):
                self.assertEqual(len(self.authorized_client.get(
                    reverse_).context.get('page_obj')),
                    self.posts_on_first_page
                )
                self.assertEqual(len(self.authorized_client.get(
                    reverse_ + '?page=2').context.get('page_obj')),
                    self.posts_on_second_page
                )
