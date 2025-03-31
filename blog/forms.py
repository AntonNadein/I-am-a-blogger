from django import forms
from django.core.exceptions import ValidationError

from blog.models import Blog
from users.forms import MixinForms


class BlogCreationForm(MixinForms, forms.ModelForm):
    """Форма создания и редактирования блога"""

    price = forms.CharField(max_length=100, required=False, label="Цена")

    class Meta:
        model = Blog
        fields = (
            "title",
            "topic",
            "is_published",
            "blog_text",
            "image",
            "is_paid",
        )

    def __init__(self, *args, **kwargs):
        """Изменение формы чекбокса"""

        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["is_published"].widget.attrs.update(
            {
                "class": "form-check-label",
            }
        )
        self.fields["is_paid"].widget.attrs.update(
            {
                "class": "form-check-label",
                "onclick": "togglePriceField(this)",
            }
        )
        self.fields["price"].widget.attrs.update(
            {
                "disabled": "disabled",  # price изначально неактивно
            }
        )
        self.fields["price"].widget.attrs["id"] = "id_price"

    def clean_image(self):
        """Проверка размера и формата загружаемого изображения"""
        image = self.cleaned_data.get("image")
        if image:
            valid_formats = ["image/jpeg", "image/png"]
            if hasattr(image, "content_type"):
                if image.content_type not in valid_formats:
                    raise ValidationError("Неверный формат файла. Допустимые форматы: JPEG, PNG.")

            size = image.size
            if size > 1024 * 1024 * 2:
                raise ValidationError("Размер файла превышает 2Мб")
            return image
        elif not image:
            return image

    def clean_is_paid(self):
        is_paid = self.cleaned_data.get("is_paid")

        if self.request and is_paid:
            try:
                self.request.user.stripe_secret
            except ValueError:
                raise ValidationError(
                    "У вас нет действительной привязки к источнику оплаты. "
                    "Пожалуйста, добавьте информацию о платёжной системе. "
                    "Это можно сделать в редакторе профиля трока Stripe secret"
                )
        return is_paid

        # if is_paid:
        #     if price != '':
        #         if not price.isdigit():
        #             raise ValidationError("Введите численное значение")
        #         else:
        #             if int(price) > 500000:
        #                 raise ValidationError("Превышен максимальный порог цены")
        #     else:
        #         if self.initial.get("price") is None or self.initial.get("price") == "":
        #             raise ValidationError("Вы забыли добавить цену, снимите галочку оплаты или добавьте цену")
        #
        #
        # return cleaned_data

    def clean_price(self):
        """Валидация цены"""

        if self.cleaned_data.get("is_paid"):
            price = self.cleaned_data.get("price")
            if price != "":
                if not price.isdigit():
                    raise ValidationError("Введите численное положительное значение")
                else:
                    if int(price) > 500000:
                        raise ValidationError("Превышен максимальный порог цены")
            else:
                price = self.initial.get("price")
                if price is None or price == "":
                    raise ValidationError("Вы забыли добавить цену, снимите галочку оплаты или добавьте цену")
            return price
        return None
