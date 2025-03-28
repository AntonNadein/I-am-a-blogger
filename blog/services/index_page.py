import calendar
from datetime import datetime

from django.db.models import Max, Count


class ServiceIndex:
    """ Сервис класс для главной страницы """

    def __init__(self):
        self.blog_objects = None
        self.queryset_page = None

    def get_max_view_count(self):
        """ Получаем максимальное значение view_count и фильтруем бд по данному объекту """

        max_view_count = self.blog_objects.aggregate(Max('view_count'))['view_count__max']
        max_object_queryset = self.blog_objects.filter(view_count=max_view_count).first()
        return max_object_queryset

    def get_max_view_count_today(self):
        """ Получаем максимальное значение view_count и фильтруем бд за сегодня """

        today = datetime.utcnow().date()
        blog_today = self.blog_objects.filter(created_at=today)
        max_view_count = blog_today.aggregate(Max('view_count'))['view_count__max']
        max_view_count_today = blog_today.filter(view_count=max_view_count).first()
        return max_view_count_today

    def get_max_like_month(self):
        """ Получаем максимальное значение like и фильтруем бд по данному объекту за месяц """

        date_month = datetime.utcnow().date().month
        blog_month = self.blog_objects.filter(created_at__month=date_month)
        max_like_month = blog_month.annotate(like_count=Count('like')).order_by('-like_count').first()
        return max_like_month

    def get_last_three_articles(self):
        """ Получаем последние три статьи """

        return self.blog_objects[0:3]

    def get_archives(self, is_index=True):
        """ Получаем архив для главой за последние 12 месяцев, для архивной полностью """

        archives = self.blog_objects.dates('created_at', 'month', order='DESC')
        if is_index:
            archives = archives[:12]

        return [
            {
                'year': archive.year,
                'month': archive.strftime('%B %Y'),
                'count': self.blog_objects.filter(created_at__year=archive.year,
                                                  created_at__month=archive.month).count()
            }
            for archive in archives
        ]

    def get_queryset_archive(self, page_link):
        """ QuerySet сортировок архива по месяцам"""

        if page_link is None:
            return self.queryset_page.filter(is_published=True)
        else:
            list_month_year = page_link.split(" ")
            number_month = list(calendar.month_name).index(list_month_year[0])
            return self.queryset_page.filter(created_at__year=list_month_year[1], created_at__month=number_month,
                                             is_published=True)
