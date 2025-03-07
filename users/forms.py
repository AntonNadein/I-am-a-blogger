from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import ModelUser


class MixinForms:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class MixinValidUsers:
    """Миксин для проверки валидности получаемых данных"""
#     def clean_phone_number(self):
#         phone_number = self.cleaned_data.get("phone_number")
#         if phone_number and not phone_number.isdigit():
#             raise forms.ValidationError("Номер телефона должен состоять только из цифр")
#         return phone_number

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


class CustomUserCreationForm(MixinForms, UserCreationForm, MixinValidUsers):
    """Форма регистрации профиля"""

    username = forms.CharField(max_length=100, required=True)

    class Meta:
        model = ModelUser
        fields = (
            "email",
            "username",
            # "phone_number",
            "password1",
            "password2",
            "avatar",
        )


class ProfileUserForm(MixinForms, forms.ModelForm, MixinValidUsers):
    """Форма профиля"""

    class Meta:
        model = ModelUser
        fields = ("last_name", "first_name", "username", "avatar",)
