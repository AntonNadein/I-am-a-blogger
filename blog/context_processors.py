""" Функции добавления контекстного процессора во все шаблоны settings.TEMPLATES """

from .models import Topic


def topics(request):
    """Добавление контекста тем блогов в header"""
    topic = Topic.objects.all()
    return {"topic_list": topic, "topic_title": request.resolver_match.kwargs.get("title")}
