from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from .models import Order, Product, OrderItem, Coupon
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from decimal import Decimal


ACCEPTED_TOKEN = ('omni_pretest_token')

def check_token(func):

    def wrapper(request):
        token = request.data.get('token')
        
        if not token or token != ACCEPTED_TOKEN:
            return Response(data={'error': 'Unauthorized or invalid token', }, status=status.HTTP_401_UNAUTHORIZED)

        return func(request)
    return wrapper

@api_view(['GET'])
def list_product(request):
    products = Product.objects.all()
    search_query = request.query_params.get('search', None)
    min_price = request.query_params.get('min_price', None)
    max_price = request.query_params.get('max_price', None)

    if search_query:
        products = products.filter(name__icontains=search_query)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    products_data = [
        {'id': p.product_id, 'name': p.name, 'price': str(p.price)} for p in products
    ]
    return Response(products_data)

@api_view(['POST'])
@check_token
def create_coupon(request):
    try:
        coupon = Coupon.objects.create(
            code=request.data['code'],
            discount_type=request.data['discount_type'],
            value=Decimal(request.data['value']),
            expiration_date=request.data['expiration_date']
        )
        return Response(
            {'message': 'Coupon created successfully!', 'code': coupon.code},
            status=status.HTTP_201_CREATED
        )
    except (KeyError, ValueError, ValidationError):
        return Response({'error': 'Invalid data provided'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@check_token
@transaction.atomic
def import_order(request):
    order_number = request.data.get('order_number')
    products = request.data.get('products')
    coupon_code = request.data.get('coupon_code')

    try:
        order_number = request.data.get('order_number')

        order = Order.objects.create(order_number=order_number)
        for product in products:
            quantity = product['quantity']
            product = Product.objects.get(product_id=product.get("product_id"))
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=int(quantity),
                price_at_purchase=product.price
            )
        
        order.calculate_total_price(coupon_code=coupon_code)
        order.save()

        resp_data = {
            'message': 'Order imported successfully!',
            'order': {
                'order_number': order.order_number,
                'total_price': order.total_price,
                'created_time': order.created_time
            }
        }
        
        return Response(data=resp_data, status=status.HTTP_201_CREATED)
    except IntegrityError:
        return Response({'error': f'Order with number {order_number} already exists, or a required field was missing or null.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

@api_view(['POST'])
def create_product(request):
    try:
        product = Product.objects.create(
            name=request.data['name'],
            price=Decimal(request.data['price'])
        )
        resp_data = {
            'id': product.product_id,
            'name': product.name,
            'price': product.price
        }
        return Response(resp_data, status=status.HTTP_201_CREATED)
    except (KeyError, ValueError, ValidationError):
        return Response({'error': 'Invalid data provided'}, status=status.HTTP_400_BAD_REQUEST)