from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.throttling import UserRateThrottle
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.shortcuts import render, get_object_or_404
from .models import Product

from .models import CustomUser, Category, Product, Order, OrderItem
from .serializers import (
    UserRegistrationSerializer,
    CategorySerializer,
    ProductV1Serializer,
    ProductV2Serializer,
    OrderSerializer
)

# User-related views
class UserRegistrationView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []      # No permission required

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user_id': user.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    authentication_classes = []  # No authentication required
    permission_classes = []      # No permission required

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user_id': user.id}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
# E-commerce views
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.request.version == 'v2':
            return ProductV2Serializer
        return ProductV1Serializer

class OrderViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                   mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        # Users can only see their own orders
        return self.queryset.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        # Here's the fix: convert quantity from string to integer
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return Response({'error': 'Quantity must be a valid number'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check for product existence and sufficient stock in a single query
            product = Product.objects.get(id=product_id, stock__gte=quantity)
            
            order = Order.objects.create(user=request.user)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price_at_purchase=product.price
            )
            
            # Decrement the stock
            product.stock -= quantity
            product.save()
            
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found or out of stock'}, status=status.HTTP_400_BAD_REQUEST)
        
        
# HTML Views
def index(request):
    return render(request, 'ecommerce/index.html')

def product_list(request):
    products = Product.objects.all()
    return render(request, 'ecommerce/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'ecommerce/product_detail.html', {'product': product})


        