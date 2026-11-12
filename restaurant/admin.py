
from django.contrib import admin
from .models import FoodItem, Reservation, CustomerProfile


# Foodora Admin Branding
admin.site.site_header = "Foodora Administration"
admin.site.site_title = "Foodora Admin"
admin.site.index_title = "Welcome to Foodora Management"


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available')
    ordering = ('name',)
    list_per_page = 20


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'reservation_date',
        'reservation_time',
        'number_of_guests',
        'status',
    )
    list_filter = ('status', 'reservation_date')
    search_fields = ('customer__username',)
    date_hierarchy = 'reservation_date'
    ordering = ('-reservation_date',)


admin.site.register(CustomerProfile)
