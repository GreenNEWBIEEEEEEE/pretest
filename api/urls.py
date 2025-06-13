from django.contrib import admin
from django.urls import path
from api.views import import_order, list_product, create_coupon, create_product

urlpatterns = [
    path('import-order/', import_order, name='import-order'),
    path('list-product/', list_product),
    path('create-coupon/', create_coupon),
    path('create-product/', create_product)
]