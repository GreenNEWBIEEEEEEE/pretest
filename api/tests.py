from rest_framework.test import APITestCase
from rest_framework import status
from .models import Product, Order
from decimal import Decimal
from django.urls import reverse

USER_TOKEN = 'omni_pretest_token'
class OrderTestCase(APITestCase):
    def setUp(self):
        self.product1 = Product.objects.create(name="筆記型電腦", price=Decimal("35000.00"))
        self.product2 = Product.objects.create(name="藍牙耳機", price=Decimal("2500.00"))
        self.import_order_url = reverse('import-order')

    def test_import_order_without_token_(self):
        response = self.client.post(self.import_order_url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_import_order_with_invalid_token(self):
        data = {
            "token": "this-is-a-invalid-token",
            "order_number": "Test-Should_Return_401",
            "products": [{"product_id": self.product1.product_id, "quantity": 1}]
        }
        response = self.client.post(self.import_order_url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_import_order_success(self):
        data = {
            "token": USER_TOKEN,
            "order_number": "Test_Should_Return_201",
            "products": [
                {"product_id": self.product1.product_id, "quantity": 1},
                {"product_id": self.product2.product_id, "quantity": 2}
            ]
        }
        response = self.client.post(self.import_order_url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(response.data['order']['order_number'], 'Test_Should_Return_201')

        self.assertTrue(Order.objects.filter(order_number='Test_Should_Return_201').exists())
        order = Order.objects.get(order_number='Test_Should_Return_201')
    
        self.assertEqual(order.total_price, 40000)
        self.assertEqual(order.discount_amount, 0)
        self.assertIsNone(order.coupon)