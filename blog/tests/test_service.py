from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from blog.models import Blog, Topic
from blog.services.index_page import ServiceIndex
from users.models import ModelUser


class ServiceIndexTestCase(TestCase):
    """Тестирование сервисных функций связанных с главной и архивной страницами"""

    def setUp(self):
        """Создаем несколько объектов Blog для тестирования"""

        self.topic = Topic.objects.create(title="Тематика", description="Описание тематики")

        self.user_1 = ModelUser.objects.create_user(
            username="test_user_1", password="password_1", email="test@test.ru"
        )
        self.user_2 = ModelUser.objects.create_user(
            username="test_user_2", password="password_2", email="test_2@test.ru"
        )
        self.user_3 = ModelUser.objects.create_user(
            username="test_user_3", password="password_3", email="test_3@test.ru"
        )
        self.user_4 = ModelUser.objects.create_user(
            username="test_user_4", password="password_4", email="test_4@test.ru"
        )

        self.blog_text = "Тестовый текст"
        self.blog_1 = Blog.objects.create(
            title="Blog 1", topic=self.topic, blog_text=self.blog_text, view_count=10, owner=self.user_1
        )
        self.blog_2 = Blog.objects.create(
            title="Blog 2", topic=self.topic, blog_text=self.blog_text, view_count=25, owner=self.user_1
        )
        self.blog_3 = Blog.objects.create(
            title="Blog 3", topic=self.topic, blog_text=self.blog_text, view_count=5, owner=self.user_2
        )
        self.blog_4 = Blog.objects.create(
            title="Blog 4", topic=self.topic, blog_text=self.blog_text, view_count=20, owner=self.user_2
        )
        self.blog_5 = Blog.objects.create(
            title="Blog 5", topic=self.topic, blog_text=self.blog_text, view_count=30, owner=self.user_2
        )

        # Инициализируем сервисный класс с объектами блога
        self.service_index = ServiceIndex()
        self.service_index.blog_objects = Blog.objects.all()
        self.service_index.queryset_page = Blog.objects.all()

    def test_get_max_view_count(self):
        """Проверяем, что возвращается верный объект с максимальным количеством просмотров"""

        max_view_blog = self.service_index.get_max_view_count()
        self.assertEqual(max_view_blog, self.blog_5)

    def test_get_max_like_today(self):
        """Проверяем, что блог с максимальным количеством просмотров за сегодняшний день возвращается"""

        self.blog_5.created_at = (timezone.now() - timedelta(days=40)).date()
        self.blog_5.save()

        max_view_count_today = self.service_index.get_max_view_count_today()
        self.assertEqual(max_view_count_today, self.blog_2)

    def test_get_max_like_month(self):
        """Проверяем, что блог с максимальным количеством лайков за месяц возвращается"""
        self.blog_2.like.add(self.user_2)
        self.blog_2.like.add(self.user_3)
        self.blog_3.like.add(self.user_4)
        self.blog_5.like.add(self.user_4)

        max_like_month = self.service_index.get_max_like_month()
        self.assertEqual(max_like_month, self.blog_2)

    def test_get_archives(self):
        """Проверяем, возвращение данных в архиве"""

        self.blog_5.created_at = (timezone.now() - timedelta(days=40)).date()
        self.blog_5.save()
        archives = self.service_index.get_archives()
        self.assertEqual(
            len(archives), 2
        )  # Проверка количества месяцев в архиве (если они все в одном месяце, то будет 1)
        expected_year = timezone.now().year
        self.assertIn(
            {"year": expected_year, "month": timezone.now().strftime("%B %Y"), "count": 4}, archives
        )  # Проверка на правильность данных месяца

    def test_queryset_archive(self):
        """Проверяем, возвращение данных в архиве"""

        month = timezone.now().strftime("%B %Y")
        self.blog_5.created_at = (timezone.now() - timedelta(days=40)).date()
        self.blog_5.save()
        self.blog_1.is_published = False
        self.blog_1.save()

        queryset = self.service_index.get_queryset_archive(month)
        self.assertEqual(len(queryset), 3)
        self.assertIn(self.blog_2, queryset)
        self.assertIn(self.blog_3, queryset)
        self.assertIn(self.blog_4, queryset)

        queryset_none = self.service_index.get_queryset_archive(None)
        self.assertEqual(len(queryset_none), 4)
        self.assertNotIn(self.blog_1, queryset)

    def tearDown(self):
        """Очищает данные после тестов"""

        Blog.objects.all().delete()
