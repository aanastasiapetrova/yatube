import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_ivan = User.objects.create(username='IvanIvanov')
        cls.user_petr = User.objects.create(username='PetrPetrov')
        cls.user_vasya = User.objects.create(username='VasyaVasin')
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description="Тестовое описание",
        )
        cls.start_group = Group.objects.create(
            title='Тестовая группа',
            slug='start-group',
            description="Тестовое описание",
        )
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
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.ivans_post = Post.objects.create(
            author=cls.user_ivan,
            text='Тестовый текст',
            image=cls.uploaded,
        )
        cls.petrs_post = Post.objects.create(
            author=cls.user_petr,
            text='Тестовый текст',
            group=cls.test_group,
            image=cls.uploaded,
        )
        cls.follow = Follow.objects.create(
            user=cls.user_ivan,
            author=cls.user_petr,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user_ivan)
        self.new_auth_client = Client()
        self.new_auth_client.force_login(self.user_vasya)

    def test_views_uses_correct_templates(self):
        """Вью-функции используют соответствующие шаблоны"""
        views_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.test_group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user_ivan}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                                                 self.ivans_post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.ivans_post.id}):
            'posts/create_post.html',
        }
        for reverse_name, template in views_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон Index сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.text, 'Тестовый текст')
        self.assertEqual(first_post.image, self.petrs_post.image)
        self.assertEqual(len(response.context['posts']), 2)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:group_list',
                                         args=(PostViewsTests.test_group.slug,
                                               )))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.group.title, 'Тестовая группа')
        self.assertEqual(first_post.group.slug, 'test-group')
        self.assertEqual(first_post.image, self.petrs_post.image)
        self.assertEqual(first_post.group.description, 'Тестовое описание')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:profile',
                                         args=(PostViewsTests.user_petr, )))
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post.author.username,
                         self.user_petr.username)
        self.assertEqual(first_post.image, self.petrs_post.image)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_show_correct_context(self):
        """Шаблон Post_detail сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('posts:post_detail',
                                         args=(PostViewsTests.ivans_post.id,
                                               )))
        picked_post = response.context['post']
        self.assertEqual(picked_post.id, self.ivans_post.id)
        self.assertEqual(picked_post.author.username,
                         self.ivans_post.author.username)
        self.assertEqual(picked_post.text, self.ivans_post.text)
        self.assertEqual(picked_post.image, self.ivans_post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правльным контекстом"""
        response = self.auth_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.auth_client.get(reverse('posts:post_edit',
                                        args=(PostViewsTests.ivans_post.id,
                                              )))
        picked_post = response.context['post']
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        self.assertEqual(picked_post.id, self.ivans_post.id)
        self.assertEqual(picked_post.author.username,
                         self.ivans_post.author.username)

    def test_post_creation_process(self):
        """При создании пост появлется на главной странице,
        странице группы и в профалйе пользователя"""
        self.another_petrs_post = Post.objects.create(
            author=self.user_petr,
            text='Тестовый текст',
            group=self.start_group,
        )
        response = self.guest_client.get(reverse('posts:index'))
        posts = response.context['posts'].filter(pk__contains=3).count()
        self.assertEqual(posts, 1)
        response = self.guest_client.get(reverse('posts:group_list',
                                         args=(PostViewsTests.test_group.slug,
                                               )))
        posts = response.context['page_obj'].object_list[0]
        self.assertNotEqual(posts.pk, 3)
        response = self.guest_client.get(reverse('posts:profile',
                                         args=(PostViewsTests.user_petr, )))
        posts = response.context['page_obj'].object_list[0]
        self.assertEqual(posts.pk, 3)
        response = self.guest_client.get(reverse('posts:group_list',
                                         args=(PostViewsTests.start_group.slug,
                                               )))
        posts = response.context['page_obj'].object_list[0]
        self.assertEqual(posts.pk, 3)

    def test_cache_index_page(self):
        """Посты на главной странице кэшируются"""
        post = Post.objects.create(
            text='Кешируемый пост',
            author=self.user_ivan)
        added = self.auth_client.get(reverse('posts:index')).content
        post.delete()
        deleted = self.auth_client.get(reverse('posts:index')).content
        self.assertEqual(added, deleted)
        cache.clear()
        cleaned = self.auth_client.get(reverse('posts:index')).content
        self.assertNotEqual(added, cleaned)

    def test_follow_index(self):
        """При создании нового поста он отображается в ленте подписчиков автора
        и не отражается в лентах пользователей, на него не подисанных"""
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user_petr)
        follower = self.auth_client.get(reverse('posts:follow_index'))
        follower_context = follower.context['page_obj']
        unfollower = self.new_auth_client.get(reverse('posts:follow_index'))
        unfollower_context = unfollower.context['page_obj']
        self.assertIn(new_post, follower_context)
        self.assertNotIn(new_post, unfollower_context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_ivan = User.objects.create(username='IvanIvanov')
        cls.user_petr = User.objects.create(username='PetrPetrov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description="Тестовое описание",
        )
        for post in range(12):
            cls.petrs_post = Post.objects.create(
                author=cls.user_petr,
                text='Тестовый текст',
            )
        for post in range(12):
            cls.ivans_post = Post.objects.create(
                author=cls.user_ivan,
                text='Тестовый текст',
                group=cls.group,
            )

    def setUp(self):
        self.client = Client()

    def test_first_index_page_contains_ten_records(self):
        """На первой странице index 10 объектов"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_records(self):
        """На второй странице index 10 объектов"""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_third_page_contains_four_records(self):
        """На третьей странице index 4 объекта"""
        response = self.client.get(reverse('posts:index') + '?page=3')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_first_group_list_page_contains_ten_records(self):
        """На первой странице group_list 10 объектов"""
        response = self.client.get(reverse('posts:group_list',
                                   args=(PaginatorViewsTest.group.slug, )))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_ten_records(self):
        """На второй странице group_list 2 объекта"""
        response = self.client.get(reverse('posts:group_list',
                                   args=(PaginatorViewsTest.group.slug, ))
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_first_profile_page_contains_ten_records(self):
        """На первой странице profile 10 объектов"""
        response = self.client.get(reverse('posts:profile',
                                   args=(PaginatorViewsTest.user_petr.username,
                                         )))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_two_records(self):
        """На первой странице profile 2 объекта"""
        response = self.client.get(reverse('posts:profile',
                                   args=(PaginatorViewsTest.user_petr.username,
                                         )) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)
