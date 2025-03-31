from django.contrib import messages
from django.http import HttpResponseForbidden

from blog.models import Payment
from blog.services.stripe import StripePaid


class ServiceDetail:
    """Сервисные функции связанных с детальным представлением блога"""

    def __init__(self):

        self.owner_blog = None
        self.subscriber = None
        self.blog = None
        self.payment = None
        self.user = None
        self.blog_objects = None

    def manage_subscriber(self, request):
        """Метод добавления и удаление подписок"""

        subscriber_list = self.owner_blog.subscriber
        if "subscription" in request.POST:
            if self.subscriber in subscriber_list.all():
                subscriber_list.remove(self.subscriber)
                message = "Подписка удалена"
            else:
                subscriber_list.add(self.subscriber)
                message = "Подписка добавлена"
            messages.success(request, message)

    def manage_like(self, request):
        """Метод добавления и удаление лайков"""

        likes_list = self.blog.like
        if "like" in request.POST:
            if self.subscriber in likes_list.all():
                likes_list.remove(self.subscriber)
            else:
                likes_list.add(self.subscriber)

    def manage_payment(self, request):
        """Метод добавления и удаление платежей"""

        if "payment" in request.POST:
            paid_blog = self.blog.payment
            self.payment = Payment.objects.create(buyers=self.subscriber)
            try:
                stripe_key = self.owner_blog.stripe_secret
                stripe_pay = StripePaid(stripe_key, paid_blog, self.blog.payment.price, self.payment.pk)
                stripe_id, stripe_url = stripe_pay.get_stripe()
            except ValueError:
                return HttpResponseForbidden(
                    "Пользователь не добавил данные о оплате, обратитесь к администрации сайта."
                )

            self.payment.link = stripe_url
            self.payment.session_id = stripe_id
            self.payment.save()
            paid_blog.payments.add(self.payment)
            return True
        return False

    def get_context_subscriber(self):
        """Метод получения подписок для контекста"""

        subscriber_list = self.blog_objects.owner.subscriber.all()
        if self.user in subscriber_list:
            return "Отписаться"
        return "Подписаться на автора"

    def get_context_like(self):
        """Метод получения лайков для контекста"""

        if self.user in self.blog_objects.like.all():
            return True
        return False

    def get_context_payments(self):
        """Метод получения платежей для контекста"""

        if self.blog_objects.is_paid:
            list_paid = []
            for i in self.blog_objects.payment.payments.filter(status="paid"):
                list_paid.append(i.buyers)
            return list_paid
