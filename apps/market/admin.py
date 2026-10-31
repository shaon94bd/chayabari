from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "artwork", "buyer", "seller", "amount_bdt", "source", "status", "created_at")
    list_filter = ("status", "source")
    search_fields = ("artwork__title", "buyer__username", "seller__username")
