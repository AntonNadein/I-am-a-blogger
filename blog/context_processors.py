from .models import Topic


def topics(request):
    return {
        'topic_list': Topic.objects.all()
    }
