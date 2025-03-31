from django.test import TestCase

from blog.models import Blog, ModelUser, PaidBlog, Topic
from blog.services.services_create_update import ServiceForm


class ServiceFormTests(TestCase):
    """Тестирование сервисных функций связанных с добавлением и обновлением блога"""

    def setUp(self):
        self.topic = Topic.objects.create(title="Тематика", description="Описание тематики")
        self.user_1 = ModelUser.objects.create_user(
            username="test_user_1", password="password_1", email="test@test.ru"
        )
        self.blog_text = "Тестовый текст"
        self.blog_1 = Blog.objects.create(
            title="Blog 1", topic=self.topic, blog_text=self.blog_text, view_count=10, owner=self.user_1
        )
        self.paid = PaidBlog.objects.create(paid_blog=self.blog_1, price=100)

        # Создание экземпляра ServiceForm
        self.service_form = ServiceForm()
        self.service_form.blog = self.blog_1
        self.service_form.is_paid = True
        self.service_form.price = 200  # Новая цена для теста

    def test_update_price_existing_payment(self):
        """Тестируем обновление цены, если платеж существует"""

        self.service_form.update_price()
        self.assertEqual(self.paid.price, 200)

    def test_update_price_new_payment(self):
        """Тестируем создание нового платежа, если его нет"""

        self.service_form.blog = Blog.objects.create(
            title="Blog 2", topic=self.topic, blog_text=self.blog_text, view_count=5, owner=self.user_1
        )
        self.service_form.update_price()
        new_paid = PaidBlog.objects.get(paid_blog=self.service_form.blog)
        self.assertEqual(new_paid.price, 200)

    def test_initial_price_existing_payment(self):
        """Тестируем получение начальной цены, если платеж существует"""

        self.service_form.blog_instance = self.blog_1
        initial_price = self.service_form.initial_prise()
        self.assertEqual(initial_price, 100)

    def test_initial_price_no_payment(self):
        """Тестируем получение начальной цены, если платежа нет"""

        self.service_form.blog_instance = Blog.objects.create(
            title="Blog 3", topic=self.topic, blog_text=self.blog_text, view_count=5, owner=self.user_1
        )
        initial_price = self.service_form.initial_prise()
        self.assertIsNone(initial_price)
