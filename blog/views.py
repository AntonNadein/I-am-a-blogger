from datetime import datetime

from django.core.paginator import Paginator
from django.db.models import Max
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from blog.forms import BlogCreationForm
from blog.models import Blog, Topic


class ListIndex(ListView):
    """Главная страница"""

    model = Blog
    context_object_name = "blog"
    ordering = "-created_at"
    paginator_class = Paginator
    paginate_by = 3
    # template_name = "blog/index.html"

    def get_template_names(self):
        # времянка для создания оформления главной страницы
        if self.request.path == '/index/2/':
            return ['blog/index2.html']
        return ['blog/index.html']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        blog_objects = self.get_queryset()

        # Находим максимальное значение view_count и фильтруем бд по данному объекту
        max_view_count = blog_objects.aggregate(Max('view_count'))['view_count__max']
        max_object_queryset = blog_objects.filter(view_count=max_view_count).first()
        context["max_object_queryset"] = max_object_queryset

        # Находим максимальное значение like и фильтруем бд по данному объекту
        today = datetime.utcnow().date()
        blog_today = blog_objects.filter(created_at=today)
        max_like = blog_today.aggregate(Max('like'))['like__max']
        max_like_today = blog_objects.filter(like=max_like).first()
        context["max_like_today"] = max_like_today

        # Находим максимальное значение like и фильтруем бд по данному объекту за месяц
        date_month = datetime.utcnow().date().month
        blog_month = blog_objects.filter(created_at__month=date_month)
        max_like = blog_month.aggregate(Max('like'))['like__max']
        max_like_month = blog_objects.filter(like=max_like).first()
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


class BlogListView(ListView):
    model = Blog
    paginator_class = Paginator
    paginate_by = 5
    template_name = "blog/blog_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(is_published=True)


class BlogDetailView(DetailView):
    model = Blog
    template_name = "blog/blog_detail.html"

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset)
        self.object.view_count += 1
        self.object.save()
        return self.object


class BlogCreateView(CreateView):
    model = Blog
    form_class = BlogCreationForm
    success_url = reverse_lazy("blog:blog_list")

    def form_valid(self, form):
        """ Добавление владельца для блога"""
        blog = form.save()
        user = self.request.user
        blog.owner = user
        blog.save()
        return super().form_valid(form)


class BlogUpdateView(UpdateView):
    model = Blog
    template_name = "blog/blog_form.html"
    form_class = BlogCreationForm

    def get_success_url(self):
        """ Перенаправление после редактирования """
        return reverse("blog:blog_detail", kwargs={"pk": self.object.pk})


class BlogDeleteView(DeleteView):
    model = Blog
    template_name = "blog/blog_confirm_delete.html"
    success_url = reverse_lazy("blog:blog_list")


class TopicDetailView(DetailView):
    """ Информация о блогах по тематикам """
    model = Topic
    template_name = "blog/topic_detail.html"
    context_object_name = 'topic'

    def get_context_data(self, **kwargs):
        """ Добавление в контекст информации о содержании тематик блогов """
        context = super().get_context_data(**kwargs)
        title = self.kwargs.get('title')
        articles = Blog.objects.filter(topic__title=title)

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
