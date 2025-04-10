import secrets

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView

from blog.services.cache import CachedViewMixin
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
        messages.success(
            self.request,
            "На вашу почту отправлено письмо, для подтверждения" " регистрации перейдите по ссылке в описании",
        )
        return super().form_valid(form)

    def send_welcome_mail(self, user_email, url):
        """Отправка приветственного сообщения"""

        subject = "Добро пожаловать на наш сайт"
        message = (
            f"Спасибо, что зарегистрировались на нашем сервисе!\n"
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
    group = Group.objects.get(name="Пользователь")
    user.groups.add(group)
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


class UserUpdateView(LoginRequiredMixin, CachedViewMixin, UpdateView):
    """Представление редактирования профиля"""

    model = ModelUser
    form_class = ProfileUserForm
    template_name = "users/register.html"
    cache_timeout = 300

    def get_queryset(self):
        """Фильтрует queryset для владельца объекта с использованием кэша"""
        if not self.request.method == "POST":
            queryset = self.get_cached_queryset()
            if queryset is not None:
                return queryset

        queryset = super().get_queryset()
        user_id = self.request.user.id
        queryset = queryset.filter(id=user_id)
        self.cache_queryset(queryset)
        return queryset

    def get_initial(self):
        """Добавление цены в форму, если цена существует"""
        initial = super().get_initial()
        user_profile = self.get_object()
        try:
            initial["stripe_secret"] = user_profile.stripe_secret
        except ValueError:
            # Если нет связанного PaidBlog, просто не добавляем цену
            initial["stripe_secret"] = ""

        return initial

    def get_success_url(self):
        return reverse_lazy("users:profile", kwargs={"pk": self.object.pk})


class ModerationUsersView(LoginRequiredMixin, PermissionRequiredMixin, CachedViewMixin, ListView):
    """Просмотр списка пользователей сервиса"""

    model = ModelUser
    context_object_name = "users"
    template_name = "users/list_users.html"
    permission_required = "users.can_block_user"
    cache_key = "moderation_users_cache"

    def get_queryset(self):
        """Получает queryset, пытаясь использовать кэш."""

        queryset = self.get_cached_queryset()
        if queryset is not None:
            return queryset

        queryset = super().get_queryset()
        self.cache_queryset(queryset)
        return queryset

    def post(self, request, pk):
        """Блокировка пользователя"""
        user = get_object_or_404(ModelUser, id=pk)

        if not request.user.has_perm("users.can_block_user"):
            return HttpResponseForbidden("У вас нет прав для блокировки пользователей.")

        if user.is_active:
            user.is_active = False
            messages.success(request, f"Пользователь {user.username} успешно заблокирован.")
        else:
            user.is_active = True
            messages.success(request, f"Пользователь {user.username} разблокирован.")
        user.save()
        self.clear_cached()
        return redirect("users:moderation_user_list")
