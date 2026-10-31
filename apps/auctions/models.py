from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class Auction(models.Model):
    artwork = models.ForeignKey("gallery.Artwork", on_delete=models.CASCADE, related_name="auctions")
    batch = models.ForeignKey("batches.Batch", on_delete=models.CASCADE, related_name="auctions")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    starting_price = models.PositiveIntegerField()
    min_increment = models.PositiveIntegerField(default=100)
    reserve_price = models.PositiveIntegerField(
        null=True, blank=True, help_text="Hidden minimum; below this the artwork is not sold."
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_cancelled = models.BooleanField(default=False)
    # Filled once the auction has ended and been settled.
    is_settled = models.BooleanField(default=False)
    winning_bid = models.OneToOneField(
        "Bid", null=True, blank=True, on_delete=models.SET_NULL, related_name="won_auction"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-starts_at",)

    def __str__(self):
        return f"Auction: {self.artwork}"

    @property
    def phase(self):
        if self.is_cancelled:
            return "cancelled"
        now = timezone.now()
        if now < self.starts_at:
            return "scheduled"
        if now >= self.ends_at:
            return "ended"
        return "live"

    def highest_bid(self):
        return self.bids.order_by("-amount", "created_at").first()

    def minimum_next_bid(self):
        top = self.highest_bid()
        return top.amount + self.min_increment if top else self.starting_price

    @property
    def reserve_met(self):
        top = self.highest_bid()
        return bool(top) and (self.reserve_price is None or top.amount >= self.reserve_price)

    def place_bid(self, user, amount):
        with transaction.atomic():
            auction = Auction.objects.select_for_update().get(pk=self.pk)
            if auction.phase != "live":
                raise ValidationError("This auction is not live.")
            if user.pk == auction.artwork.artist_id:
                raise ValidationError("You cannot bid on your own artwork.")
            minimum = auction.minimum_next_bid()
            if amount < minimum:
                raise ValidationError(f"Bid must be at least ৳{minimum}.")
            bid = Bid.objects.create(auction=auction, bidder=user, amount=amount)
            # Anti-sniping: late bids extend the auction.
            window = timedelta(minutes=settings.AUCTION_EXTENSION_MINUTES)
            if auction.ends_at - timezone.now() < window:
                auction.ends_at = timezone.now() + window
                auction.save(update_fields=["ends_at"])
            self.ends_at = auction.ends_at
            return bid

    def settle(self):
        """Close an ended auction: record the winner and open an order for them."""
        from apps.market.models import Order

        if self.is_settled or self.phase != "ended":
            return
        with transaction.atomic():
            auction = Auction.objects.select_for_update().get(pk=self.pk)
            if auction.is_settled:
                return
            auction.is_settled = True
            if auction.reserve_met:
                top = auction.highest_bid()
                auction.winning_bid = top
                artwork = auction.artwork
                artwork.sale_status = artwork.SaleStatus.RESERVED
                artwork.save(update_fields=["sale_status"])
                Order.objects.create(
                    artwork=artwork,
                    buyer=top.bidder,
                    seller=artwork.artist,
                    amount_bdt=top.amount,
                    source=Order.Source.AUCTION,
                    status=Order.Status.ACCEPTED,
                    message=f"Won auction #{auction.pk}",
                )
            auction.save()
            self.is_settled, self.winning_bid = auction.is_settled, auction.winning_bid


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids")
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-amount", "created_at")

    def __str__(self):
        return f"৳{self.amount} by {self.bidder}"
