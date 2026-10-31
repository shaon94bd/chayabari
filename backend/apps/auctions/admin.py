from django.contrib import admin

from .models import Auction, Bid


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    readonly_fields = ("bidder", "amount", "created_at")


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ("artwork", "batch", "starting_price", "starts_at", "ends_at", "is_cancelled", "is_settled")
    list_filter = ("is_cancelled", "is_settled", "batch")
    inlines = [BidInline]
