

# Create your tests here.
from django.test import TestCase
from .models import FoodItem
from django.contrib.auth.models import Group
from django.urls import reverse


class FoodItemTest(TestCase):

    def setUp(self):
        self.food = FoodItem.objects.create(
            name="Chicken Burger",
            description="Delicious chicken burger",
            price=350,
            category="Burger"
        )

    def test_food_item_creation(self):
        self.assertEqual(self.food.name, "Chicken Burger")
        self.assertEqual(self.food.price, 350)
        self.assertEqual(self.food.category, "Burger")

    def test_food_item_default_availability(self):
        self.assertTrue(self.food.is_available)

    def test_food_item_exists_in_database(self):
        self.assertEqual(FoodItem.objects.count(), 1)

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Reservation


class ReservationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testcustomer',
            password='testpassword123'
        )

        self.reservation = Reservation.objects.create(
            customer=self.user,
            reservation_date=timezone.localdate() + timedelta(days=1),
            reservation_time='18:00',
            number_of_guests=4,
            special_request='Window seat'
        )

    def test_reservation_creation(self):
        self.assertEqual(self.reservation.customer, self.user)
        self.assertEqual(self.reservation.number_of_guests, 4)

    def test_reservation_default_status(self):
        self.assertEqual(self.reservation.status, 'pending')

    def test_reservation_special_request(self):
        self.assertEqual(
            self.reservation.special_request,
            'Window seat'
        )

    def test_reservation_exists_in_database(self):
        self.assertEqual(Reservation.objects.count(), 1)


from django.contrib.auth.models import User


class UserAuthenticationTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123'
        )

    def test_user_login(self):
        result = self.client.login(
            username='testuser',
            password='testpassword123'
        )
        self.assertTrue(result)

    def test_user_wrong_password(self):
        result = self.client.login(
            username='testuser',
            password='wrongpassword'
        )
        self.assertFalse(result)

    def test_user_logout(self):
        self.client.login(
            username='testuser',
            password='testpassword123'
        )

        self.client.logout()

        self.assertNotIn(
            '_auth_user_id',
            self.client.session
        )

class AdminPermissionTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='testadmin',
            password='adminpassword123',
            email='admin@test.com'
        )

        self.staff = User.objects.create_user(
            username='teststaff',
            password='staffpassword123'
        )

        staff_group, created = Group.objects.get_or_create(
            name='Staff'
        )
        self.staff.groups.add(staff_group)

    def test_admin_can_access_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('admin_dashboard')
        )

        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_access_admin_dashboard(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('admin_dashboard')
        )

        self.assertEqual(response.status_code, 302)

class ReservationPermissionTest(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            password='password123'
        )

        self.staff = User.objects.create_user(
            username='staff',
            password='password123'
        )

        self.admin = User.objects.create_superuser(
            username='admin',
            password='password123',
            email='admin@test.com'
        )

        customer_group, _ = Group.objects.get_or_create(
            name='Customer'
        )

        staff_group, _ = Group.objects.get_or_create(
            name='Staff'
        )

        self.customer.groups.add(customer_group)
        self.staff.groups.add(staff_group)

    def test_customer_can_access_reservation_page(self):
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse('make_reservation')
        )

        self.assertEqual(response.status_code, 200)

    def test_guest_is_redirected_to_login(self):
        response = self.client.get(
            reverse('make_reservation')
        )

        self.assertEqual(response.status_code, 302)

    def test_staff_cannot_access_reservation_page(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('make_reservation')
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_cannot_access_reservation_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('make_reservation')
        )

        self.assertEqual(response.status_code, 302)