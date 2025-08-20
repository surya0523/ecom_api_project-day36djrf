from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import CustomUser, Category, Product, Order, OrderItem
from rest_framework.authtoken.models import Token

class EcommerceAPITests(APITestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testpassword')
        self.admin = CustomUser.objects.create_user(username='adminuser', password='adminpassword', is_staff=True)
        self.token = Token.objects.create(user=self.user)
        self.admin_token = Token.objects.create(user=self.admin)

        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Laptop',
            description='A powerful laptop',
            price=1500.00,
            category=self.category,
            stock=10
        )
        self.v1_url = reverse('products-list', kwargs={'version': 'v1'})
        self.v2_url = reverse('products-list', kwargs={'version': 'v2'})
        self.category_url = reverse('category-list')
        self.order_url = reverse('order-list')

    def test_product_list_v1(self):
        """v1 endpoint should return basic product data."""
        response = self.client.get(self.v1_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('name', response.data['results'][0])
        self.assertNotIn('description', response.data['results'][0])

    def test_product_list_v2(self):
        """v2 endpoint should return detailed product data."""
        response = self.client.get(self.v2_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn('name', response.data['results'][0])
        self.assertIn('description', response.data['results'][0])

    def test_user_cannot_create_category(self):
        """Authenticated users cannot create a category."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {'name': 'Books'}
        response = self.client.post(self.category_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_category(self):
        """Admin users can create a category."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        data = {'name': 'Books'}
        response = self.client.post(self.category_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_can_place_order(self):
        """Authenticated user can place an order."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(self.order_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

    def test_user_rate_throttle(self):
        """Test that UserRateThrottle limits order creation."""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        data = {'product_id': self.product.id, 'quantity': 1}
        # Send more requests than the throttle limit (100)
        for _ in range(101):
            response = self.client.post(self.order_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)