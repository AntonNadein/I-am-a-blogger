from django.test import TestCase, Client

from blog.models import Topic, Blog
from users.models import ModelUser


class ModelTests(TestCase):
    def setUp(self):
        self.user = ModelUser.objects.create(username="Testov", email="test@test.ru", password="1234")
        self.topic = Topic.objects.create(
            title="Название рубрики",
            description="Описание",
        )

        self.blog = Blog.objects.create(
            title="Ни о чем",
            topic=self.topic,
            blog_text="Тут пример текста блога",
            owner=self.user
        )

    def test_topic_str(self):
        """ Тест строкового представления тематики """
        self.assertEqual(str(self.topic), "Название рубрики")

    def test_blog_str(self):
        """ Тест строкового представления блога """
        self.assertEqual(str(self.blog), "Ни о чем")

    def test_topic_blog(self):
        """ Тест связи блога и тематики """
        self.assertEqual(self.blog.topic, self.topic)
        self.assertEqual(self.topic.topic.first(), self.blog)

    def test_owner_blog(self):
        """ Тест связи блога и владельца """
        self.assertEqual(self.blog.owner, self.user)

