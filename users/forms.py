from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import ModelUser


class MixinForms:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

    def clean_avatar(self):
        """ Проверка изображения на соответствие параметров """
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            valid_formats = ["image/jpeg", "image/png"]
            if hasattr(avatar, "content_type"):
                if avatar.content_type not in valid_formats:
                    raise ValidationError("Неверный формат файла. Допустимые форматы: JPEG, PNG.")

            size = avatar.size
            if size > 1024 * 1024 * 1:
                raise ValidationError("Размер файла превышает 1Мб")
            return avatar
        elif not avatar:
            return avatar


class UserAuthenticationForm(MixinForms, AuthenticationForm):
    """Форма авторизации"""

    pass


class UserPasswordResetForm(MixinForms, PasswordResetForm):
    """Форма ввода E-mail для сброса пароля"""

    pass


class UserSetPasswordForm(MixinForms, SetPasswordForm):
    """Форма сброса пароля"""

    pass


class CustomUserCreationForm(MixinForms, UserCreationForm):
    """Форма регистрации профиля"""

    username = forms.CharField(max_length=100, required=True)

    class Meta:
        model = ModelUser
        fields = (
            "email",
            "username",
            "password1",
            "password2",
            "avatar",
        )


class ProfileUserForm(MixinForms, forms.ModelForm):
    """Форма профиля"""

    stripe_secret = forms.CharField(max_length=250, required=False, label='Stripe Secret')

    class Meta:
        model = ModelUser
        fields = ("last_name", "first_name", "username", "avatar")

    def save(self, commit=True):
        """ Добавление stripe_secret через сеттер """

        user = super().save(commit=False)
        stripe_secret = self.cleaned_data.get('stripe_secret')
        if stripe_secret:
            user.stripe_secret = stripe_secret
        if commit:
            user.save()
        return user
