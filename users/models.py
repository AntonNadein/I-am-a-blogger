import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.contrib.auth.models import AbstractUser
from django.db import models

from config.settings import SECRET_KEY

secret_key = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())


class ModelUser(AbstractUser):
    """Модель пользователя"""

    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    token = models.CharField(max_length=100, null=True, blank=True, verbose_name="Токен")
    subscriber = models.ManyToManyField("self", blank=True, verbose_name="Подписчик")
    _stripe_secret = models.CharField(max_length=250, null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = [
        "email",
    ]

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_block_user", "Can block user"),
        ]

    def __str__(self):
        return self.username

    @property
    def stripe_secret(self):
        """Получение расшифрованного ключа"""
        if self._stripe_secret is None:
            raise ValueError("Stripe secret is not set")
        fernet = Fernet(secret_key)
        try:
            decrypted = fernet.decrypt(self._stripe_secret.encode())  # Декодируем строку в байты
            return decrypted.decode()  # Декодируем байты в строку
        except InvalidToken:
            raise ValueError("Invalid token - decryption failed")

    @stripe_secret.setter
    def stripe_secret(self, secret):
        """Шифрование ключа stripe перед сохранением"""
        if not isinstance(secret, str):
            raise ValueError("Secret must be a string")
        fernet = Fernet(secret_key)
        self._stripe_secret = fernet.encrypt(secret.encode()).decode("utf-8")
