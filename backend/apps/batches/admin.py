from django.contrib import admin, messages

from .models import Batch, Payment, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price_bdt", "duration_days", "max_members", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("plan", "status", "starts_at", "ends_at")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("name", "institution", "session", "owner", "member_count", "active", "created_at")
    search_fields = ("name", "institution", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SubscriptionInline]

    @admin.display(description="Members")
    def member_count(self, obj):
        return obj.members.count()

    @admin.display(boolean=True, description="Active")
    def active(self, obj):
        return obj.is_active_subscription


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "method", "amount_bdt", "sender_number", "batch", "status", "created_at")
    list_filter = ("status", "method")
    search_fields = ("transaction_id", "sender_number", "subscription__batch__name")
    actions = ("verify_payments", "reject_payments")

    @admin.display(description="Batch")
    def batch(self, obj):
        return obj.subscription.batch

    @admin.action(description="Verify selected payments (activates subscription)")
    def verify_payments(self, request, queryset):
        n = 0
        for p in queryset.select_related("subscription__plan", "subscription__batch"):
            if p.status != Payment.Status.VERIFIED:
                p.verify()
                n += 1
        self.message_user(request, f"{n} payment(s) verified.", messages.SUCCESS)

    @admin.action(description="Reject selected payments")
    def reject_payments(self, request, queryset):
        for p in queryset.exclude(status=Payment.Status.VERIFIED):
            p.reject("Rejected by admin")
        self.message_user(request, "Done.", messages.SUCCESS)
