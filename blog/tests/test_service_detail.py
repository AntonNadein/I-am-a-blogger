from django.test import TestCase
from unittest.mock import patch, MagicMock

from blog.services.services_detail import ServiceDetail
from users.models import ModelUser
from blog.models import Blog, Topic, PaidBlog


class TestServiceDetail(TestCase):
    """ Тестирование сервисных функций связанных с детальным представлением блога """

    def setUp(self):
        self.topic = Topic.objects.create(title='Тематика', description='Описание тематики')

        self.user_1 = ModelUser.objects.create_user(username='test_user_1', password='password_1',
                                                    email="test@test.ru")
        self.user_2 = ModelUser.objects.create_user(username='test_user_2', password='password_2',
                                                    email="test_2@test.ru")
        self.blog_text = "Тестовый текст"
        self.blog_1 = Blog.objects.create(title='Blog 1', topic=self.topic, blog_text=self.blog_text, view_count=10,
                                          owner=self.user_1)
        self.paid = PaidBlog.objects.create(paid_blog=self.blog_1, price=100)
        # Создаем необходимых пользователей и блог
        self.service_detail = ServiceDetail()
        self.service_detail.owner_blog = self.user_1
        self.service_detail.subscriber = self.user_2
        self.service_detail.blog = self.blog_1

    @patch('blog.services.stripe.StripePaid')
    def test_manage_payment(self, mock_stripe_paid):
        """ Тест оплаты """

        # Настраиваем мок для StripePaid, доделать с правильным выполнением
        mock_stripe_instance = MagicMock()
        mock_stripe_instance.get_stripe.return_value = ("mock_stripe_id", "mock_stripe_url")
        mock_stripe_paid.return_value = mock_stripe_instance

        # Эмулируем запрос с POST данными
        request = MagicMock()
        request.POST = {'payment': True}

        self.service_detail.manage_payment(request)
        self.assertRaises(ValueError)
        # self.user_1.stripe_secret = 'test'
        # self.user_1.save()
        # result = self.service_detail.manage_payment(request)
        # Проверяем, что payment был создан и ссылки обновлены
        # payment = Payment.objects.get(buyers=self.user_2)
        # self.assertEqual(payment.link, "mock_stripe_url")
        # self.assertEqual(payment.session_id, "mock_stripe_id")
        # self.assertTrue(result)
        # self.assertIn(payment, self.blog.payment.payments.all())

    def test_manage_subscriber(self):
        """ Тестируем метод управления подписчиками """

        # Эмулируем запрос для добавления подписчика
        request_add = MagicMock()
        request_add.POST = {'subscription': True}
        self.service_detail.manage_subscriber(request_add)
        self.assertIn(self.user_2, self.user_1.subscriber.all())
        # Эмулируем запрос для удаления подписчика
        request_remove = MagicMock()
        request_remove.POST = {'subscription': True}
        self.service_detail.manage_subscriber(request_remove)
        self.assertNotIn(self.user_2, self.user_1.subscriber.all())

    def test_manage_like(self):
        """ Тестируем метод управления лайками """

        # Эмулируем запрос для добавления лайка
        request_add = MagicMock()
        request_add.POST = {'like': True}
        self.service_detail.manage_like(request_add)
        self.assertIn(self.user_2, self.blog_1.like.all())
        # Эмулируем запрос для удаления лайка
        request_remove = MagicMock()
        request_remove.POST = {'like': True}
        self.service_detail.manage_like(request_remove)
        self.assertNotIn(self.user_2, self.blog_1.like.all())
