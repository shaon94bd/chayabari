from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer
from apps.gallery.models import Artwork
from apps.gallery.serializers import ArtworkListSerializer

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    artwork = ArtworkListSerializer(read_only=True)
    artwork_id = serializers.PrimaryKeyRelatedField(
        queryset=Artwork.objects.select_related("batch"), write_only=True, source="artwork"
    )
    buyer = UserMiniSerializer(read_only=True)
    seller = UserMiniSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = ("id", "artwork", "artwork_id", "buyer", "seller", "amount_bdt", "source", "status",
                  "status_label", "message", "contact_phone", "delivery_address", "created_at", "updated_at")
        read_only_fields = ("amount_bdt", "source", "status")

    def validate(self, attrs):
        from apps.auctions.models import Auction

        user = self.context["request"].user
        art = attrs["artwork"]
        if art.artist_id == user.id:
            raise serializers.ValidationError({"detail": "This is your own artwork."})
        if not art.is_published or art.sale_status != Artwork.SaleStatus.AVAILABLE or not art.price_bdt:
            raise serializers.ValidationError({"detail": "This artwork is not available for sale."})
        if not art.batch.is_active_subscription:
            raise serializers.ValidationError({"detail": "This artwork is not available for sale."})
        open_auction = Auction.objects.filter(artwork=art, is_cancelled=False, is_settled=False)
        if any(a.phase in ("live", "scheduled") for a in open_auction):
            raise serializers.ValidationError({"detail": "This artwork is being auctioned — place a bid instead."})
        if Order.objects.filter(artwork=art, buyer=user, status=Order.Status.PENDING).exists():
            raise serializers.ValidationError({"detail": "You already have a pending request for this artwork."})
        return attrs
