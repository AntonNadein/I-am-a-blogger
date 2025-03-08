from django.contrib.auth.models import AbstractUser
from django.db import models


class ModelUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    token = models.CharField(max_length=100, null=True, blank=True, verbose_name="Токен")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = [
        "email",
    ]

    def __str__(self):
        return f'{self.username}-{self.email}'

    class Meta:
        verbose_name = "пользователя"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_block_user", "Can block user"),
        ]

