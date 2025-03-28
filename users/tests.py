from django.contrib.auth.models import Group, Permission
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .forms import ProfileUserForm

User = get_user_model()


class UserUpdateViewTest(TestCase):
    """ Тестирование представления обновления пользователя """

    def setUp(self):
        """ Создаем пользователя для тестирования """
        self.user = User.objects.create_user(username='testuser', password='password123', email="test@test.ru")
        self.client.login(username='testuser', password='password123')
        self.url = reverse('users:profile_update', kwargs={'pk': self.user.pk})
        self.url_profile = reverse('users:profile', kwargs={'pk': self.user.pk})

    def test_user_update_view_get_request(self):
        """  Успешный запрос на получение страницы обновления пользователя """

        response = self.client.get(self.url_profile)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertContains(response, 'testuser')

    def test_user_update_view_post_request_success(self):
        """ Успешно обновляем данные пользователя """

        new_data = {
            'username': 'UpdatedUser',
            'email': 'updated@example.com',
            'first_name': 'testov',
            'last_name': 'test',
            'stripe_secret': "ascsa1ewddw33",
        }

        response = self.client.post(self.url, new_data)
        self.assertRedirects(response, reverse('users:profile', kwargs={'pk': self.user.pk}))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'UpdatedUser')
        self.assertEqual(self.user.first_name, 'testov')
        self.assertEqual(self.user.last_name, 'test')
        self.assertEqual(self.user.stripe_secret, "ascsa1ewddw33")

    def test_user_update_view_post_request_invalid_data(self):
        """ Неуспешное обновление данных с использованием неверных данных формы """

        invalid_data = {
            'username': '$',  # Пустое имя пользователя недопустимо
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)  # Ожидаем, что вернется форма с ошибками
        self.assertFormError(ProfileUserForm(invalid_data), 'username',
                             'Введите правильное имя пользователя. '
                             'Оно может содержать только буквы, цифры и знаки @/./+/-/_.', )

    def test_user_update_cache(self):
        """ Проверка, что кэшированная выборка используется при GET запросе """

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Проверяем, что queryset был закэширован
        cached_queryset = cache.get(f'modeluser/users/profile_update/{self.user.pk}/_cache')
        self.assertIsNotNone(cached_queryset, "Queryset should be cached!")
        self.assertEqual(str(cached_queryset[0].username), "testuser")

    def tearDown(self):
        """ Удаление пользователя после завершения тестов """

        self.user.delete()
        cache.clear()


class UserCreateViewTests(TestCase):
    """ Тестирование представления регистрации пользователя """

    def setUp(self):
        """ Создаем группу пользователей и данные пользователя для регистрации """

        self.url = reverse('users:register')
        self.group_name = "Пользователь"
        Group.objects.create(name=self.group_name)
        # отправка данных на создание пользователя
        self.user_client = self.client.post(self.url, {
            'username': 'testuser',
            'email': 'test@test.ru',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
        })

    def test_user_creation_sends_email(self):
        """ Тестирование функции отправки письма """

        response = self.user_client

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:login'))

        # проверка отправки письма
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Добро пожаловать на наш сайт', mail.outbox[0].subject)
        self.assertIn('Для подтверждения регистрации перейдите по ссылке', mail.outbox[0].body)
        self.assertIn('test@test.ru', mail.outbox[0].to)

        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)

    def test_email_verification_activates_user(self):
        """ Тестирование верификации пользователя """

        user = User.objects.get(username='testuser')
        token = user.token

        response = self.client.get(reverse('users:verification', args=[token]))
        self.assertEqual(response.status_code, 302)

        # Проверка после верификации
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.groups.filter(name=self.group_name).exists())
        self.assertRedirects(response, reverse("users:login"))

    def test_email_verification_with_invalid_token(self):
        """ Тестирование верификации пользователя с неправильным токеном """

        response = self.client.get(reverse('users:verification', args=['random_token']))
        self.assertEqual(response.status_code, 404)


class ModerationUsersViewTests(TestCase):
    def setUp(self):
        """ Создаем пользователей с правами и тестового пользователя для блокировки """

        self.superuser = User.objects.create_superuser(username='admin', password='password', email="admin@test.ru")
        self.user_with_permission = User.objects.create_user(username='testuser', password='password',
                                                             email="test@test.ru")
        permission = Permission.objects.get(codename='can_block_user')
        self.user_with_permission.user_permissions.add(permission)

        # Создаем тестового пользователя
        self.test_user = User.objects.create(username='test_user_2', password='password', email="test2@test.ru",
                                             is_active=True)

    def test_user_list_view_with_permission(self):
        """ Проверяем, что testuser с правами может посетить странице модерации """

        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('users:moderation_user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/list_users.html')
        # Проверяем, что возвращаемый контекст содержит пользователя
        self.assertIn('users', response.context)
        self.assertIn(self.test_user, response.context['users'])

    def test_user_block(self):
        """ Проверяем, что testuser с правами может заблокировать пользователя """

        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('users:block_user', args=[self.test_user.id]))

        self.assertRedirects(response, reverse('users:moderation_user_list'))
        self.test_user.refresh_from_db()
        self.assertFalse(self.test_user.is_active)

        # Проверяем сообщение об успешном блокировании
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Пользователь test_user_2 успешно заблокирован.")

    def test_user_unblock(self):
        """ Проверяем, что testuser с правами может разблокировать пользователя """

        self.test_user.is_active = False
        self.test_user.save()

        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('users:block_user', args=[self.test_user.id]))

        self.assertRedirects(response, reverse('users:moderation_user_list'))
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.is_active)

        # Проверяем сообщение об успешном разблокировании
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Пользователь test_user_2 разблокирован.")

    def test_user_list_view_without_permission(self):
        """ Создаем нового пользователя без прав и проверяем доступ к модерации """

        normal_user = User.objects.create_user(username='normaluser', password='password')
        self.client.login(username=normal_user.username, password='password')
        response = self.client.get(reverse('users:moderation_user_list'))
        self.assertEqual(response.status_code, 403)

    def test_user_list_view_with_permissions_and_cache(self):
        """ Тестируем обновление страницы """

        # Входим как суперпользователь
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('users:moderation_user_list'))
        self.assertEqual(response.status_code, 200)

        # Предполагаем, что вошедший testuser видит кэш admin
        self.client.login(username='testuser', password='password')
        self.assertContains(response, 'testuser')
        cached_response = self.client.get(reverse('users:moderation_user_list'))
        cached_queryset = cache.get("moderation_users_cache")
        cached_usernames = [str(user) for user in cached_queryset]

        self.assertCountEqual(cached_usernames,
                              ["admin", "testuser", "test_user_2"])
        self.assertEqual(response.headers, cached_response.headers)  # Сравниваем содержимое
        # self.assertEqual(response.content, cached_response.content)     # не работает!?

    def tearDown(self):
        """ Очищение кеша после тестов """
        cache.clear()


class LoginUsersViewTests(TestCase):
    """ Тест входа на сайт """

    def setUp(self):
        """ Создаем пользователей с правами и тестового пользователя для блокировки """

        self.test_user = User.objects.create(username='test_user', password='password', email="test@test.ru",
                                             is_active=True)

    def test_user_login(self):
        """ Проверяем, что test_user может посетить сайт """

        response = self.client.post(reverse('users:login'), {'username': 'test_user', 'password': 'password'})
        self.assertEqual(response.status_code, 200)

    def test_user_not_login(self):
        """ Проверяем, что test_user может посетить сайт """

        self.test_user.is_active = False
        self.test_user.save()
        self.client.login(username='test_user', password='password')
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)


class UserDetailViewTests(TestCase):
    """ Тест информации профиля """

    def setUp(self):
        """ Создаем тестовых пользователей """

        self.user = User.objects.create_user(username='test_user', password='password', email="test@test.ru")
        self.client.login(username='test_user', password='password')
        self.other_user = User.objects.create_user(username='other_user', password='otherpassword',
                                                   email="test1@test.ru")

    def test_user_detail_view_access(self):
        """ Проверка доступа к профилю текущего пользователя """

        response = self.client.get(reverse('users:profile', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_user_detail_view_access_other_user(self):
        """ Проверка доступа к профилю другого пользователя """

        response = self.client.get(reverse('users:profile', args=[self.other_user.id]))
        self.assertEqual(response.status_code, 404)
