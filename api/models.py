from django.db import models
from django.utils import timezone
from decimal import Decimal
from uuid import uuid4

class BaseDiscountStrategy:
    def calculate(self, subtotal: Decimal, value: Decimal) -> Decimal:
        raise NotImplementedError("Use derived class to implement")

class FixedAmountStrategy(BaseDiscountStrategy):
    def calculate(self, subtotal: Decimal, value: Decimal) -> Decimal:
        return value

class PercentageStrategy(BaseDiscountStrategy):
    def calculate(self, origin: Decimal, value: Decimal) -> Decimal:
        discount_percentage = value / Decimal('100.0')
        return origin * discount_percentage

class Product(models.Model):
    product_id = models.CharField(primary_key=True, max_length=100, blank=True, unique=True, default=uuid4)
    name = models.CharField(max_length=100)
    created_time = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=10, decimal_places=3)

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("fixed", "fixed_amount"),
        ("percent", "percent_amount")
    ]
    code = models.CharField(primary_key=True, max_length=50)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='fixed')
    value = models.DecimalField(max_digits=10, decimal_places=2)
    expiration_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def get_strategy(self) -> BaseDiscountStrategy:
        if self.discount_type == 'fixed':
            return FixedAmountStrategy()
        elif self.discount_type == 'percent':
            return PercentageStrategy()
        return None

class Order(models.Model):
    order_number = models.CharField(primary_key=True, max_length=100)
    total_price = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    created_time = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, through="OrderItem", related_name="order")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')

    def _calculate_origin_total_price(self):
        return sum(item.price_at_purchase * item.quantity for item in self.orderItems.all())

    def calculate_total_price(self, coupon_code=None):
        origin_price = self._calculate_origin_total_price()

        self.coupon = None
        self.discount_amount = Decimal('0.0')

        if coupon_code:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True, expiration_date__gte=timezone.now())
            strategy = coupon.get_strategy()

            if strategy:
                self.discount_amount = strategy.calculate(origin_price, coupon.value)
                self.coupon = coupon
        
        self.total_price = origin_price - self.discount_amount

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orderItems")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=3)