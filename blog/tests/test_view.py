from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from blog.forms import BlogCreationForm
from blog.models import Blog, PaidBlog, Topic, Payment
from users.models import ModelUser


class BlogViewTest(TestCase):
    """ Тестирование представлений блога """

    def setUp(self):
        """ Создаем пользователя для тестирования """
        self.user = ModelUser.objects.create_user(username='testuser', password='password123', email="test@test.ru")
        self.user_2 = ModelUser.objects.create_user(username='testuser_2', password='password', email="test2@test.ru")

        self.topic = Topic.objects.create(title='Тематика', description='Описание тематики')

        self.blog_text = "Тестовый текст"
        self.blog_1 = Blog.objects.create(title='Blog 1', topic=self.topic, blog_text=self.blog_text,
                                          image="avatars/unnamed.jpg", view_count=10,
                                          owner=self.user)
        self.blog_2 = Blog.objects.create(title='Blog 2', topic=self.topic, blog_text=self.blog_text,
                                          image="avatars/unnamed.jpg", view_count=20, is_paid=True,
                                          owner=self.user_2)

        self.paid = PaidBlog.objects.create(paid_blog=self.blog_2, price=100)

        self.client.login(username='testuser', password='password123')
        self.url_index = reverse('blog:index')

    def test_get_index_page(self):
        """  Тест получения главной страницы """

        response = self.client.get(self.url_index)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/index.html')
        self.assertContains(response, 'Тематика')
        self.assertContains(response, 'Blog 1')
        self.assertContains(response, 'Blog 2')

    def test_get_archive_page(self):
        """  Тест получения страницы архива """

        url = reverse('blog:archive')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/archive.html')
        self.assertContains(response, 'Тематика')
        self.assertContains(response, 'Blog 1')
        self.assertContains(response, 'Blog 2')

    def test_get_blog_list_view(self):
        """  Тест получения страниц мой блог """

        url = reverse('blog:blog_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/blog_list.html')
        self.assertContains(response, 'Тематика')
        self.assertContains(response, 'Blog 1')
        self.assertNotContains(response, 'Blog 2')

    def test_get_blog_detail_view(self):
        """  Тест получения детальной страницы """

        url = reverse('blog:blog_detail', kwargs={'pk': self.blog_2.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/blog_detail.html')
        self.assertContains(response, 'Тематика')
        self.assertContains(response, 'Просмотры')
        self.assertContains(response, 'Blog 2')
        self.assertContains(response, 'Купить')
        self.assertNotContains(response, 'Blog 1')

        response_2 = self.client.post(url, name="like")
        self.assertRedirects(response_2, reverse('blog:blog_detail', kwargs={'pk': self.blog_2.pk}))

        response_3 = self.client.post(url, name="subscription")
        self.assertRedirects(response_3, reverse('blog:blog_detail', kwargs={'pk': self.blog_2.pk}))

    def test_blog_create_view(self):
        """  Тест создания новой записи """

        url = reverse('blog:blog_create')
        data_create = {
            'title': 'Blog 3',
            'topic': self.topic.pk,
            'blog_text': 'Новый текст',
        }
        response = self.client.post(url, data_create)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('blog:blog_list'))

        bad_data_create = {
            'title': '$',
            'topic': self.topic,
        }
        response_2 = self.client.post(url, bad_data_create)
        self.assertEqual(response_2.status_code, 200)
        self.assertFormError(BlogCreationForm(bad_data_create), 'blog_text', "Обязательное поле.")

    def test_blog_update_view(self):
        """ Обновляем данные блога """

        self.client.login(username='testuser', password='password123')
        url = reverse('blog:blog_update', kwargs={'pk': self.blog_1.pk})
        new_data = {
            'title': 'Blog 3',
            'topic': self.topic.pk,
            'is_published': True,
            'blog_text': 'Новый текст',
            'is_paid': False,
        }

        form = BlogCreationForm(data=new_data)
        self.assertTrue(form.is_valid(), msg=form.errors)

        response = self.client.post(url, new_data)
        self.blog_1.refresh_from_db()
        self.assertRedirects(response, reverse('blog:blog_detail', kwargs={'pk': self.blog_1.pk}))
        self.assertEqual(self.blog_1.title, 'Blog 3')
        self.assertEqual(self.blog_1.blog_text, 'Новый текст')

        bad_data = {
            'title': '$',
            'topic': self.topic,
        }
        response_2 = self.client.post(url, bad_data)
        self.blog_1.refresh_from_db()
        self.assertEqual(response_2.status_code, 200)
        self.assertFormError(BlogCreationForm(bad_data), 'blog_text', "Обязательное поле.")

    def test_get_topic_detail(self):
        """  Тест получения статей с темами """

        url = reverse('blog:topic_detail', kwargs={'title': self.topic.title})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/topic_detail.html')
        self.assertContains(response, 'Тематика')
        self.assertContains(response, 'Blog 1')
        self.assertContains(response, 'Blog 2')

    def test_blog_search_view(self):
        """  Тест поисковика """

        self.blog_3 = Blog.objects.create(title='Blog 3', topic=self.topic, blog_text=self.blog_text,
                                          is_published=False, owner=self.user)
        response = self.client.get(reverse('blog:search'), {'search': 'Blog'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Blog 1')
        self.assertContains(response, 'Blog 2')
        self.assertNotContains(response, 'Blog 3')
        self.assertTemplateUsed(response, 'blog/search_results.html')

        response_2 = self.client.get(reverse('blog:search'), {'search': 'ненайденная информация'})
        self.assertEqual(response_2.status_code, 200)
        self.assertContains(response_2, 'Нет результатов по вашему запросу')

    def test_payment_detail_view(self):
        """  Тест получения детальной страницы """

        pay_1 = Payment.objects.create(buyers=self.user)
        pay_1.save()
        url = reverse('blog:payment_detail', kwargs={'pk': pay_1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/payment.html')
        self.assertContains(response, 'testuser')

        url = reverse('blog:confirmation', kwargs={'pk': pay_1.pk})
        response_2 = self.client.get(url)
        pay_1.refresh_from_db()
        self.assertEqual(response_2.status_code, 200)
        self.assertTemplateUsed(response_2, 'blog/payment_confirmation.html')
        self.assertEqual(pay_1.status, "paid")
        self.assertEqual(pay_1.payment_date, datetime.utcnow().date())
