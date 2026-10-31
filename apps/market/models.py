from django.conf import settings
from django.db import models


class Order(models.Model):
    """A purchase of an artwork. Money changes hands offline (cash / bKash);
    the app tracks the deal between buyer and artist."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending — waiting for artist"
        ACCEPTED = "accepted", "Accepted — arrange payment & delivery"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    class Source(models.TextChoices):
        DIRECT = "direct", "Direct purchase"
        AUCTION = "auction", "Auction"

    artwork = models.ForeignKey("gallery.Artwork", on_delete=models.CASCADE, related_name="orders")
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="purchases")
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sales")
    amount_bdt = models.PositiveIntegerField()
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.DIRECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Order #{self.pk}: {self.artwork} → {self.buyer}"
