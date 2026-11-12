
from django.urls import path
from restaurant.views import home, signup, user_login, user_logout,staff_dashboard, customer_dashboard, make_reservation
from .views import add_food, ai_assistant, cancel_reservation, delete_food, delete_reservation, delete_user, edit_food, manage_food, manage_users
from .views import update_reservation_status, menu, customer_profile, admin_dashboard, manage_reservations, admin_update_reservation, edit_reservation


urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),

    path('staff/dashboard/', staff_dashboard, name='staff_dashboard'),
    path('customer/dashboard/', customer_dashboard, name='customer_dashboard'),

    path('reservation/', make_reservation, name='make_reservation'),
    path('reservation/cancel/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
    path('staff/reservation/<int:reservation_id>/update/',update_reservation_status,name='update_reservation_status'),
    path('menu/', menu, name='menu'),
    path('profile/', customer_profile, name='customer_profile'),

    path('admin-dashboard/',admin_dashboard,name='admin_dashboard'),
    path('admin-dashboard/reservations/',manage_reservations,name='manage_reservations'),
    path('admin-dashboard/reservations/<int:reservation_id>/update/',admin_update_reservation, name='admin_update_reservation'),
    path('admin-dashboard/reservations/<int:reservation_id>/edit/',edit_reservation, name='edit_reservation'),
    path('admin-dashboard/reservations/<int:reservation_id>/delete/',delete_reservation, name='delete_reservation'),
    path('admin-dashboard/food/', manage_food, name='manage_food'),
    path('admin-dashboard/food/add/', add_food, name='add_food'),
    path('admin-dashboard/food/<int:food_id>/edit/',edit_food, name='edit_food'),
    path('admin-dashboard/food/<int:food_id>/delete/',delete_food, name='delete_food'),
    path('admin-dashboard/users/', manage_users, name='manage_users'),
    path('admin-dashboard/users/<int:user_id>/delete/',delete_user,name='delete_user'),


    path('ai-assistant/',ai_assistant, name='ai_assistant'),
]