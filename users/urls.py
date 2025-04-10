from django.contrib.auth.views import (LogoutView, PasswordResetCompleteView, PasswordResetConfirmView,
                                       PasswordResetDoneView, PasswordResetView)
from django.urls import path, reverse_lazy

from users.apps import UsersConfig

from . import views
from .forms import UserPasswordResetForm, UserSetPasswordForm

app_name = UsersConfig.name

urlpatterns = [
    path("register/", views.UserCreateView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="blog:index"), name="logout"),
    path("confirm/<str:token>/", views.email_verification, name="verification"),
    # Смена пароля
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="users/password_reset_form.html",
            email_template_name="users/password_reset_email.html",
            form_class=UserPasswordResetForm,
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            form_class=UserSetPasswordForm,
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    # Работа с профилем
    path("profile/<int:pk>/", views.UserDetailView.as_view(), name="profile"),
    path("profile_update/<int:pk>/", views.UserUpdateView.as_view(), name="profile_update"),
    # Модерация
    path("list_users/", views.ModerationUsersView.as_view(), name="moderation_user_list"),
    path("users/<int:pk>/block/", views.ModerationUsersView.as_view(), name="block_user"),
]
