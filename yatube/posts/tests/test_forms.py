import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_ivan = User.objects.create(username='IvanIvanov')
        cls.user_petr = User.objects.create(username='PetrPetrov')
        cls.user_vasya = User.objects.create(username='VasyaVasin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug1',
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user_ivan,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.follow = Follow.objects.create(
            user=cls.user_ivan,
            author=cls.user_vasya,
        )
        cls.form = PostForm()
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_ivan)

    def test_create_post(self):
        """При создании поста происходит добавление записи в БД и
        перенаправление на страницу профайла"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
            'group': PostCreateFormTest.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             args=(self.user_ivan.username, )))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст из формы',
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """При редактировании поста происходит обновление запси в БД
        и перенаправление на страницу детального просмотра записи"""
        posts_count = Post.objects.count()
        picked_post = Post.objects.last()
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostCreateFormTest.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(picked_post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(picked_post.author.username, self.user_ivan.username)
        self.assertRedirects(response, reverse('posts:post_detail',
                             args=(picked_post.id, )))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(Post.objects.get(pk=picked_post.id).text,
                         'Отредактированный текст')

    def test_guest_comment(self):
        """Неавторизованный пользователь не может комментировать посты"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_autorized_comment(self):
        """Авторизованный пользователь может комментировать посты"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_authorized_follow(self):
        """Авторизованный пользователь может подписываться на авторов"""
        follows_count = Follow.objects.filter(user=self.user_ivan.pk).count()
        data = {
            'user': self.authorized_client,
            'author': self.user_petr,
        }
        self.authorized_client.post(
            reverse('posts:profile_follow', args=(self.user_petr,)),
            data=data,
            follow=True
        )
        self.assertEqual(Follow.objects.filter(user=self.user_ivan.pk).count(),
                         follows_count + 1)

    def test_authorized_unfollow(self):
        """Авторизованный пользователь может отписываться от авторов"""
        follows_count = Follow.objects.filter(user=self.user_ivan.pk).count()
        data = {
            'user': self.authorized_client,
            'author': self.user_vasya,
        }
        self.authorized_client.post(
            reverse('posts:profile_unfollow', args=(self.user_vasya,)),
            data=data,
            follow=True
        )
        self.assertEqual(Follow.objects.filter(user=self.user_ivan.pk).count(),
                         follows_count - 1)
