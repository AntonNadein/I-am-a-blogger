import os

from blog.models import Blog, PaidBlog
from config.settings import MEDIA_ROOT


class ServiceForm:
    """Сервисные функции связанные с добавлением и обновлением блога"""

    def __init__(self):

        self.blog = None
        self.is_paid = None
        self.price = None
        self.blog_instance = None

    @staticmethod
    def delete_image_from_media(form):
        """Удаление изображения из хранилища"""

        old_image = form.initial.get("image")
        if form.cleaned_data.get("image") is not None:
            if old_image != form.cleaned_data.get("image") and old_image.name != "":
                path_to_image = os.path.join(MEDIA_ROOT, str(old_image))
                if os.path.exists(path_to_image):
                    os.remove(path_to_image)

    def update_price(self):
        """Обновление цены"""

        if self.is_paid:
            if self.price is not None:
                try:
                    paid = self.blog.payment
                    paid.price = int(self.price)
                    paid.save()
                except Blog.payment.RelatedObjectDoesNotExist:
                    PaidBlog.objects.create(paid_blog=self.blog, price=self.price)

    def initial_prise(self):
        """Добавление цены к форме обновления"""

        try:
            paid_blog_instance = self.blog_instance.payment
            return paid_blog_instance.price
        except PaidBlog.DoesNotExist:
            pass
