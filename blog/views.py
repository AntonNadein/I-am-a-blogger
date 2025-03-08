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
    # template_name = "blog/index.html"

    def get_template_names(self):
        # времянка для создания оформления главной страницы
        if self.request.path == '/index/2/':
            return ['blog/index2.html']
        return ['blog/index.html']


class BlogListView(ListView):
    model = Blog
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
        context['articles'] = Blog.objects.filter(topic__title=title)
        return context

    def get_object(self, queryset=None):
        """ Получение контекста тематики по заголовку """
        title = self.kwargs.get('title')
        return get_object_or_404(Topic, title=title)
