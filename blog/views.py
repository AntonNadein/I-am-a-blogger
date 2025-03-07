from django.views.generic import ListView

from blog.models import Blog


class ListIndex(ListView):
    """Главная страница"""

    model = Blog
    context_object_name = "blog"
    template_name = "blog/index.html"
