from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from blog.forms import BlogCreationForm
from blog.models import Blog, Topic, Payment, PaidBlog
from blog.services.cache import CachedViewMixin
from blog.services.index_page import ServiceIndex
from blog.services.services_detail import ServiceDetail
from blog.services.services_create_update import ServiceForm


class ListIndex(ServiceIndex, CachedViewMixin, ListView):
    """Главная страница"""

    model = Blog
    context_object_name = "blog"
    ordering = "-created_at"
    paginator_class = Paginator
    paginate_by = 3
    template_name = "blog/index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        """ Контекст для главной станицы """

        context = super().get_context_data(**kwargs)
        self.blog_objects = self.get_queryset()

        # Находим максимальное значение view_count и фильтруем бд по данному объекту
        max_view_count = self.get_max_view_count()
        context["max_object_queryset"] = self.get_max_view_count()

        # максимальное значение like сегодня
        max_view_count_count_today = self.get_max_view_count_today()
        if max_view_count_count_today:
            context["max_like_today"] = max_view_count_count_today
        else:
            context["max_like_today"] = max_view_count

        # максимальное значение like за месяц
        context["max_like_month"] = self.get_max_like_month()

        # Последние 3 сообщения
        context["last_three_articles"] = self.get_last_three_articles()

        # Архив за 12 месяцев
        context['archives'] = self.get_archives()
        return context

    def get_queryset(self):
        """ QuerySet сортировок архива по месяцам"""

        self.queryset_page = self.get_cached_queryset()
        if self.queryset_page is not None:
            return self.queryset_page

        self.queryset_page = super().get_queryset()
        page_link = self.request.GET.get('month')
        self.cache_queryset(self.get_queryset_archive(page_link))
        return self.get_queryset_archive(page_link)


class ListArchive(ServiceIndex, ListView):
    """ Архив полностью и по месяцам """

    model = Blog
    context_object_name = "blog"
    ordering = "-created_at"
    paginator_class = Paginator
    paginate_by = 5
    template_name = "blog/archive.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        """ Контекст для архивной станицы """

        context = super().get_context_data(**kwargs)
        self.blog_objects = self.get_queryset()
        context['archives'] = self.get_archives(False)
        return context

    def get_queryset(self):
        """ QuerySet сортировок архива по месяцам"""

        self.queryset_page = super().get_queryset()
        page_link = self.request.GET.get('month')
        return self.get_queryset_archive(page_link)


class BlogListView(LoginRequiredMixin, ListView):
    """ Представление для моей страницы """
    model = Blog
    paginator_class = Paginator
    paginate_by = 5
    template_name = "blog/blog_list.html"

    def get_queryset(self):
        """ QuerySet для моей страницы """

        queryset = super().get_queryset()
        user = self.request.user
        if user:
            return queryset.filter(owner=user)
        else:
            return queryset.filter(is_published=True)


class BlogDetailView(LoginRequiredMixin, ServiceDetail, CachedViewMixin, DetailView):
    """ Полная информация о записи """
    model = Blog
    template_name = "blog/blog_detail.html"

    def get_object(self, queryset=None):
        """ Добавление просмотров (не ограничено можно накручивать) """

        self.object = super().get_object(queryset)
        self.object.view_count += 1
        self.object.save()
        return self.object

    def post(self, request, *args, **kwargs):
        """ Управление подпиской, оплатой и лайками """

        self.subscriber = self.request.user
        self.owner_blog = get_object_or_404(Blog, id=kwargs.get("pk")).owner
        # подписчики
        self.manage_subscriber(request)
        # лайки
        self.blog = get_object_or_404(Blog, id=kwargs.get("pk"))
        self.manage_like(request)
        # оплата
        if self.manage_payment(request):
            return HttpResponseRedirect(reverse_lazy("blog:payment_detail", kwargs={"pk": self.payment.pk}))

        return HttpResponseRedirect(reverse_lazy("blog:blog_detail", kwargs={"pk": kwargs.get("pk")}))

    def get_context_data(self, **kwargs):
        """Контекст для кнопки подписки"""
        context = super().get_context_data()
        self.blog_objects = kwargs.get("object")
        self.user = self.request.user
        context["subscriber"] = self.get_context_subscriber()
        context["like_user"] = self.get_context_like()
        context["like"] = self.blog_objects.like.count()
        context["payments"] = self.get_context_payments()
        return context

    def get_queryset(self):
        """Получает queryset, пытаясь использовать кэш."""

        queryset = self.get_cached_queryset()
        if queryset is not None:
            return queryset

        queryset = super().get_queryset()
        self.cache_queryset(queryset)
        return queryset


class BlogCreateView(LoginRequiredMixin, CreateView):
    """ Вьюшка создания записи """
    model = Blog
    form_class = BlogCreationForm
    success_url = reverse_lazy("blog:blog_list")

    def get_form_kwargs(self):
        """ Передаем объект request в форму """
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """ Добавление владельца для блога"""
        blog = form.save()
        user = self.request.user
        blog.owner = user
        blog.save()

        price = form.cleaned_data.get("price")
        if price:
            paid = PaidBlog.objects.create(paid_blog=blog, price=int(price))
            paid.save()

        return super().form_valid(form)


class BlogUpdateView(LoginRequiredMixin, ServiceForm, UpdateView):
    """ Вьюшка обновления своей записи """
    model = Blog
    template_name = "blog/blog_form.html"
    form_class = BlogCreationForm

    def get_success_url(self):
        """ Перенаправление после редактирования """
        return reverse("blog:blog_detail", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        """ Передаем объект request в форму """
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        """ POST обновления своей записи """
        product = self.get_object()
        if request.user != product.owner:
            return HttpResponseForbidden("У вас нет прав для редактирования продукта.")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """ Удаление изображения из хранилища и обновление цены """
        self.delete_image_from_media(form)
        self.blog = form.save()
        # обновление цены
        self.price = form.cleaned_data.get("price")
        self.is_paid = form.cleaned_data.get("is_paid")
        self.update_price()
        return super().form_valid(form)

    def get_initial(self):
        """ Добавление цены в форму, если цена существует """

        initial = super().get_initial()
        self.blog_instance = self.get_object()
        if self.initial_prise():
            initial['price'] = self.initial_prise()
        else:
            initial['price'] = ''
        # try:
        #     paid_blog_instance = blog_instance.payment
        #     initial['price'] = paid_blog_instance.price
        # except PaidBlog.DoesNotExist:
        #     # Если нет связанного PaidBlog, просто не добавляем цену
        #     initial['price'] = ''
        return initial


class BlogDeleteView(LoginRequiredMixin, DeleteView):
    """ Вьюшка удаления своей записи """
    model = Blog
    template_name = "blog/blog_confirm_delete.html"
    success_url = reverse_lazy("blog:blog_list")

    def post(self, request, *args, **kwargs):
        """ POST удаления своей записи """
        product = self.get_object()
        if request.user != product.owner:
            return HttpResponseForbidden("У вас нет прав для редактирования продукта.")
        return super().post(request, *args, **kwargs)


@method_decorator(cache_page(60 * 5), name="dispatch")
class TopicDetailView(DetailView):
    """ Информация о блогах по тематикам """
    model = Topic
    template_name = "blog/topic_detail.html"
    context_object_name = 'topic'

    def get_context_data(self, **kwargs):
        """ Добавление в контекст информации о содержании тематик блогов """

        context = super().get_context_data(**kwargs)
        title = self.kwargs.get('title')
        articles = Blog.objects.filter(topic__title=title, is_published=True)

        # Настройка пагинации
        paginator = Paginator(articles, 5)  # Показываем по 5 статей на странице
        page_number = self.request.GET.get('page')  # Получаем номер текущей страницы из GET запроса
        page_obj = paginator.get_page(page_number)  # Извлекаем объекты текущей страницы

        context['articles'] = page_obj
        context['page_obj'] = page_obj
        context['is_paginated'] = paginator.num_pages > 1  # Проверяем, есть ли страницы для пагинации
        context['paginator'] = paginator
        return context

    def get_object(self, queryset=None):
        """ Получение контекста тематики по заголовку """
        title = self.kwargs.get('title')
        return get_object_or_404(Topic, title=title)


class BlogSearchView(ListView):
    """ Класс поиска по названию и содержанию записи """

    model = Blog
    template_name = 'blog/search_results.html'
    context_object_name = 'blogs'

    def get_queryset(self):
        """ Ищет строки, которые содержат некоторую подстроку icontains-поиск не зависит от регистра"""

        query = self.request.GET.get('search')
        if query:
            return Blog.objects.filter(
                Q(title__icontains=query, is_published=True) | Q(blog_text__icontains=query, is_published=True))
        return Blog.objects.none()


@method_decorator(cache_page(60 * 15), name="dispatch")
class PaymentDetailView(LoginRequiredMixin, DetailView):
    """ Класс для оплаты контента """

    model = Payment
    template_name = "blog/payment.html"
    context_object_name = "pay"
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        """Контекст для кнопки подписки"""

        context = super().get_context_data()
        blog_objects = kwargs.get("object")
        context["buyer_name"] = blog_objects.buyers.username
        context["price"] = blog_objects.paid.all().first
        return context


def payment_confirmation(request, pk):
    """ Страница подтверждения оплаты """

    payment = get_object_or_404(Payment, pk=pk)
    payment.payment_date = datetime.utcnow().date()
    payment.status = "paid"
    payment.save()
    return render(request, "blog/payment_confirmation.html")
