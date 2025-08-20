# ecommerce/urls.py

from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegistrationView, LoginView,
    CategoryViewSet, ProductViewSet, OrderViewSet,
    index, product_list, product_detail # Add the new views here
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    # API Endpoints
    path('api/register/', UserRegistrationView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    re_path(r'^api/(?P<version>v[12])/products/$', ProductViewSet.as_view({'get': 'list'}), name='products-list'),
    re_path(r'^api/(?P<version>v[12])/products/(?P<pk>\d+)/$', ProductViewSet.as_view({'get': 'retrieve'}), name='products-detail'),
    path('api/', include(router.urls)),

    # HTML Endpoints (for the front-end)
    path('', index, name='index'),
    path('products/', product_list, name='product-list-html'),
    path('products/<int:pk>/', product_detail, name='product-detail-html'),
]