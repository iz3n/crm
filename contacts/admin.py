from django.contrib import admin
from contacts.models import AppUser, Address, CustomerRelationship


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'street', 'street_number', 'city', 'country']
    list_filter = ['country', 'city']
    search_fields = ['street', 'city', 'country', 'city_code']


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'customer_id', 'gender', 'created']
    list_filter = ['gender', 'created', 'address__country']
    search_fields = ['first_name', 'last_name', 'customer_id', 'phone_number']
    readonly_fields = ['created', 'last_updated', 'customer_id']
    date_hierarchy = 'created'


@admin.register(CustomerRelationship)
class CustomerRelationshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'appuser', 'points', 'created', 'last_activity']
    list_filter = ['created', 'last_activity']
    search_fields = ['appuser__first_name', 'appuser__last_name', 'appuser__customer_id']
    readonly_fields = ['created']
    date_hierarchy = 'last_activity'
