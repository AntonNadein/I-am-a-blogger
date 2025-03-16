from django.core.management.base import BaseCommand

from blog.models import Blog, Topic
from users.models import ModelUser


class Command(BaseCommand):
    help = "Add test product to the database"

    def handle(self, *args, **kwargs):

        Blog.objects.all().delete()
        Topic.objects.all().delete()
        ModelUser.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Базы данных Blog и Topic удалены"))
