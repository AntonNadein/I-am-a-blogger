import secrets

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView

from config.settings import EMAIL_HOST_USER
from users.forms import CustomUserCreationForm, ProfileUserForm, UserAuthenticationForm
from users.models import ModelUser


class UserCreateView(CreateView):
    """Представление регистрации профиля"""

    model = ModelUser
    form_class = CustomUserCreationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form):
        """Верификация зарегистрированного пользователя"""
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f"http://{host}/users/confirm/{token}/"

        self.send_welcome_mail(user.email, url)
        return super().form_valid(form)

    def send_welcome_mail(self, user_email, url):
        """Отправка приветственного сообщения"""
        subject = "Добро пожаловать на наш сайт"
        message = (
            f"Спасибо, что зарегистрировались в нашем интернет магазине!\n"
            f"Для подтверждения регистрации перейдите по ссылке {url}"
        )
        from_email = EMAIL_HOST_USER
        recipient_list = [
            user_email,
        ]
        send_mail(subject, message, from_email, recipient_list)


def email_verification(request, token):
    """Активация и добавление прав пользователю"""
    user = get_object_or_404(ModelUser, token=token)
    user.is_active = True
    # group = Group.objects.get(name="Пользователь")
    # user.groups.add(group)
    user.save()
    return redirect(reverse("users:login"))


class UserLoginView(LoginView):
    """Представление авторизации"""

    form_class = UserAuthenticationForm
    template_name = "users/login.html"


class UserDetailView(DetailView):
    """Представление профиля"""

    model = ModelUser
    template_name = "users/profile.html"
    context_object_name = "user"

    def get_queryset(self):
        """Фильтрует queryset для владельца обьекта"""
        queryset = super().get_queryset()
        user_id = self.request.user.id
        return queryset.filter(id=user_id)


class UserUpdateView(LoginRequiredMixin, UpdateView):
    """Представление редактирования профиля"""

    model = ModelUser
    form_class = ProfileUserForm
    template_name = "users/register.html"

    def get_queryset(self):
        """Фильтрует queryset для владельца обьекта"""
        queryset = super().get_queryset()
        user_id = self.request.user.id
        return queryset.filter(id=user_id)

    def get_success_url(self):
        return reverse_lazy("users:profile", kwargs={"pk": self.object.pk})
