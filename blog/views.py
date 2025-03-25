import calendar
import os
from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Max, Count, Q
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from blog.forms import BlogCreationForm
from blog.models import Blog, Topic, Payment, PaidBlog
from blog.servicies.stripe import StripePaid
from config.settings import MEDIA_ROOT


class ListIndex(ListView):
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
        blog_objects = self.get_queryset()

        # Находим максимальное значение view_count и фильтруем бд по данному объекту
        max_view_count = blog_objects.aggregate(Max('view_count'))['view_count__max']
        max_object_queryset = blog_objects.filter(view_count=max_view_count).first()
        context["max_object_queryset"] = max_object_queryset

        # Находим максимальное значение like и фильтруем бд по данному объекту
        today = datetime.utcnow().date()
        blog_today = blog_objects.filter(created_at=today)
        max_view_count = blog_today.aggregate(Max('view_count'))['view_count__max']
        max_view_count_today = blog_today.filter(view_count=max_view_count).first()
        if max_view_count_today:
            context["max_like_today"] = max_view_count_today
        else:
            context["max_like_today"] = max_object_queryset

        # Находим максимальное значение like и фильтруем бд по данному объекту за месяц
        date_month = datetime.utcnow().date().month
        blog_month = blog_objects.filter(created_at__month=date_month)
        max_like_month = blog_month.annotate(like_count=Count('like')).order_by('-like_count').first()
        context["max_like_month"] = max_like_month

        # Последние 3 сообщения
        context["last_three_articles"] = blog_objects[0:3]

        # Архив по месяцам
        archives = blog_objects.dates('created_at', 'month', order='DESC')[:12]
        context['archives'] = [
            {
                'year': archive.year,
                'month': archive.strftime('%B %Y'),
                'count': blog_objects.filter(created_at__year=archive.year, created_at__month=archive.month).count()
            }
            for archive in archives
        ]

        return context

    def get_queryset(self):
        """ QuerySet сортировок архива по месяцам"""
        queryset = super().get_queryset()
        page_link = self.request.GET.get('month')
        if page_link is None:
            return queryset.filter(is_published=True)
        else:
            list_month_year = page_link.split(" ")
            number_month = list(calendar.month_name).index(list_month_year[0])
            return queryset.filter(created_at__year=list_month_year[1], created_at__month=number_month,
                                   is_published=True)


class ListArchive(ListView):
    """ Архив полностью и по месяцам """

    model = Blog
    context_object_name = "blog"
    ordering = "-created_at"
    paginator_class = Paginator
    paginate_by = 5
    template_name = "blog/archive.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        blog_objects = self.get_queryset()

        archives = blog_objects.dates('created_at', 'month', order='DESC')
        context['archives'] = [
            {
                'year': archive.year,
                'month': archive.strftime('%B %Y'),
                'count': blog_objects.filter(created_at__year=archive.year, created_at__month=archive.month).count()
            }
            for archive in archives
        ]

        return context

    def get_queryset(self):
        """ QuerySet сортировок архива по месяцам"""
        queryset = super().get_queryset()
        page_link = self.request.GET.get('month')
        if page_link is None:
            return queryset.filter(is_published=True)
        else:
            list_month_year = page_link.split(" ")
            number_month = list(calendar.month_name).index(list_month_year[0])
            return queryset.filter(created_at__year=list_month_year[1], created_at__month=number_month,
                                   is_published=True)


class BlogListView(LoginRequiredMixin, ListView):
    """ Представление для моей страницы """
    model = Blog
    paginator_class = Paginator
    paginate_by = 5
    template_name = "blog/blog_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user:
            return queryset.filter(owner=user)
        else:
            return queryset.filter(is_published=True)


class BlogDetailView(LoginRequiredMixin, DetailView):
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
        """Включение и отключение подписки"""
        subscriber = self.request.user
        owner_blog = get_object_or_404(Blog, id=kwargs.get("pk")).owner
        subscriber_list = owner_blog.subscriber

        blog = get_object_or_404(Blog, id=kwargs.get("pk"))
        likes_list = blog.like

        if "subscription" in request.POST:
            if subscriber in subscriber_list.all():
                subscriber_list.remove(subscriber)
                message = "Подписка удалена"
            else:
                subscriber_list.add(subscriber)
                message = "Подписка добавлена"
            messages.success(request, message)

        elif "like" in request.POST:
            if subscriber in likes_list.all():
                likes_list.remove(subscriber)
            else:
                likes_list.add(subscriber)
        else:
            paid_blog = blog.payment
            payment = Payment.objects.create(buyers=subscriber)
            try:
                stripe_key = owner_blog.stripe_secret
                stripe_pay = StripePaid(stripe_key, paid_blog, blog.payment.price, payment.pk)
                stripe_id, stripe_url = stripe_pay.get_stripe()
            except ValueError:
                return HttpResponseForbidden(
                    "Пользователь не добавил данные о оплате, обратитесь к администрации сайта.")

            payment.link = stripe_url
            payment.session_id = stripe_id
            payment.save()
            paid_blog.payments.add(payment)
            return HttpResponseRedirect(reverse_lazy("blog:payment_detail", kwargs={"pk": payment.pk}))
        return HttpResponseRedirect(reverse_lazy("blog:blog_detail", kwargs={"pk": kwargs.get("pk")}))

    def get_context_data(self, **kwargs):
        """Контекст для кнопки подписки"""
        context = super().get_context_data()
        blog_objects = kwargs.get("object")
        subscriber_list = blog_objects.owner.subscriber.all()
        user = self.request.user
        if user in subscriber_list:
            context["subscriber"] = "Отписаться"
        else:
            context["subscriber"] = "Подписаться на автора"

        if user in blog_objects.like.all():
            context["like_user"] = True
        else:
            context["like_user"] = False
        context["like"] = blog_objects.like.count()
        if blog_objects.is_paid:
            list_paid = []
            for i in blog_objects.payment.payments.filter(status="paid"):
                list_paid.append(i.buyers)
            context["payments"] = list_paid
        return context


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


class BlogUpdateView(LoginRequiredMixin, UpdateView):
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
        """ Удаление изображения из хранилища """
        old_image = form.initial.get('image')
        if form.cleaned_data.get('image') is not None:
            if old_image != form.cleaned_data.get('image') and old_image.name != '':
                path_to_image = os.path.join(MEDIA_ROOT, str(old_image))
                if os.path.exists(path_to_image):
                    os.remove(path_to_image)
        blog = form.save()
        # замена цены
        price = form.cleaned_data.get("price")
        is_paid = form.cleaned_data.get("is_paid")
        if is_paid:
            if price is not None:
                try:
                    paid = blog.payment
                    paid.price = int(price)
                    paid.save()
                except Blog.payment.RelatedObjectDoesNotExist:
                    PaidBlog.objects.create(paid_blog=blog, price=price)

        return super().form_valid(form)

    def get_initial(self):
        """ Добавление цены в форму, если цена существует """
        initial = super().get_initial()
        blog_instance = self.get_object()

        try:
            paid_blog_instance = blog_instance.payment
            initial['price'] = paid_blog_instance.price
        except PaidBlog.DoesNotExist:
            # Если нет связанного PaidBlog, просто не добавляем цену
            initial['price'] = ''

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
