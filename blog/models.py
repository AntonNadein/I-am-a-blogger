from ckeditor.fields import RichTextField
from django.db import models

from users.models import ModelUser


class Blog(models.Model):
    """ Модель блога """
    title = models.CharField(max_length=250, verbose_name="Заголовок")
    topic = models.ForeignKey("Topic", on_delete=models.PROTECT, related_name="topic", verbose_name="Тематика блога")
    blog_text = RichTextField(verbose_name="Содержимое статьи")
    image = models.ImageField(upload_to="blog/%Y/%m/%d/", null=True, blank=True, verbose_name="Превью (изображение)")
    created_at = models.DateField(auto_now_add=True, verbose_name="Дата создания")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовать",
                                       help_text="Поставте галочку, что-бы запись видели все")
    view_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    like = models.PositiveIntegerField(default=0, verbose_name="Количество лайков")
    owner = models.ForeignKey(
        ModelUser, on_delete=models.CASCADE, null=True, blank=True, related_name="blog", verbose_name="Владелец"
    )
    subscriber = models.ManyToManyField(
        ModelUser, blank=True, related_name="blog_subscriber", verbose_name="Подписчик"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Статью"
        verbose_name_plural = "Статьи"
        ordering = ["created_at", ]


class Topic(models.Model):
    """ Модель тематик для блога """

    title = models.CharField(max_length=50, verbose_name="Краткое название тематики")
    description = models.CharField(max_length=50, verbose_name="Небольшое описание тематики")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "тематику"
        verbose_name_plural = "Тематика"
        ordering = ["title", ]
