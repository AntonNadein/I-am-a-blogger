import stripe


class StripePaid:
    """ Класс для оплаты Stripe """

    def __init__(self, stripe_key: str, name: str, amount: int, pk: int):
        self.stripe_key = stripe_key
        self.name = name
        self.amount = amount
        self.pk = pk
        self.product = None
        self.price = None

    def get_stripe(self):
        """ Основной метод выполнения страйпа """
        stripe.api_key = self.stripe_key
        self.create_stripe_product()
        self.create_stripe_price()
        return self.create_stripe_session()

    def create_stripe_product(self):
        """Создание продукта в страйпе"""
        self.product = stripe.Product.create(name=self.name)

    def create_stripe_price(self):
        """Создание цены в страйпе"""
        self.price = stripe.Price.create(currency="rub", unit_amount=self.amount * 100, product=self.product.get("id"))

    def create_stripe_session(self):
        """Создание сессии в страйпе"""
        session = stripe.checkout.Session.create(
            success_url=f"http://127.0.0.1:8000/payment_confirmation/{self.pk}/",
            line_items=[{"price": self.price.get("id"), "quantity": 1}],
            mode="payment",
        )
        return session.get("id"), session.get("url")
