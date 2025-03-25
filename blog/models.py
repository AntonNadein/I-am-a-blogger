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
    like = models.ManyToManyField(
        ModelUser, blank=True, related_name="blog_subscriber",
        verbose_name="Лайкнули"
    )
    owner = models.ForeignKey(
        ModelUser, on_delete=models.CASCADE, null=True, blank=True, related_name="blog", verbose_name="Владелец"
    )
    is_paid = models.BooleanField(default=False, verbose_name="Платный контент",
                                  help_text="Поставте галочку, что-бы добавить оплату")

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


class PaidBlog(models.Model):
    """Модель платного блога """

    paid_blog = models.OneToOneField(
        Blog, on_delete=models.CASCADE, related_name="payment", verbose_name="Блог"
    )
    price = models.PositiveIntegerField(verbose_name="Цена")
    payments = models.ManyToManyField("Payment", blank=True, related_name="paid", verbose_name="Покупатель")

    def __str__(self):
        return f"{self.paid_blog} Цена: {self.price}"

    class Meta:
        verbose_name = "цена"
        verbose_name_plural = "Цена"


class Payment(models.Model):
    """Модель платеж"""

    PAYMENT_STATUS = [
        ("create", "Создан"),
        ("paid", "Оплачен"),
    ]

    buyers = models.ForeignKey(ModelUser, on_delete=models.CASCADE, related_name="payments", verbose_name="Покупатель")
    payment_date = models.DateField(blank=True, null=True, verbose_name="Дата оплаты")
    link = models.URLField(max_length=400, blank=True, null=True, verbose_name="Ссылка на оплату")
    session_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID сессии")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default="create", verbose_name="Статус оплаты")

    def __str__(self):
        return f"Платеж {self.id} от {self.buyers.username}"

    class Meta:
        verbose_name = "платеж"
        verbose_name_plural = "Платежи"
