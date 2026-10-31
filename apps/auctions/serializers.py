from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer
from apps.gallery.models import Artwork
from apps.gallery.serializers import ArtworkListSerializer

from .models import Auction, Bid


class BidSerializer(serializers.ModelSerializer):
    bidder = UserMiniSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ("id", "bidder", "amount", "created_at")


class AuctionSerializer(serializers.ModelSerializer):
    artwork = ArtworkListSerializer(read_only=True)
    artwork_id = serializers.PrimaryKeyRelatedField(queryset=Artwork.objects.all(), write_only=True, source="artwork")
    phase = serializers.CharField(read_only=True)
    highest_bid = serializers.SerializerMethodField()
    bid_count = serializers.SerializerMethodField()
    minimum_next_bid = serializers.SerializerMethodField()
    reserve_met = serializers.BooleanField(read_only=True)
    has_reserve = serializers.SerializerMethodField()
    winner = serializers.SerializerMethodField()
    server_time = serializers.SerializerMethodField()

    class Meta:
        model = Auction
        fields = ("id", "artwork", "artwork_id", "starting_price", "min_increment", "reserve_price", "starts_at",
                  "ends_at", "phase", "highest_bid", "bid_count", "minimum_next_bid", "reserve_met", "has_reserve",
                  "is_settled", "winner", "server_time")
        extra_kwargs = {"reserve_price": {"write_only": True}}

    def get_highest_bid(self, obj):
        top = obj.highest_bid()
        return BidSerializer(top).data if top else None

    def get_bid_count(self, obj):
        return obj.bids.count()

    def get_minimum_next_bid(self, obj):
        return obj.minimum_next_bid()

    def get_has_reserve(self, obj):
        return obj.reserve_price is not None

    def get_winner(self, obj):
        return UserMiniSerializer(obj.winning_bid.bidder).data if obj.winning_bid_id else None

    def get_server_time(self, obj):
        return timezone.now()

    def validate(self, attrs):
        user = self.context["request"].user
        artwork = attrs["artwork"]
        if artwork.artist_id != user.id:
            raise serializers.ValidationError({"artwork_id": "You can only auction your own artwork."})
        if artwork.sale_status in (Artwork.SaleStatus.RESERVED, Artwork.SaleStatus.SOLD):
            raise serializers.ValidationError({"artwork_id": "This artwork is already reserved or sold."})
        if Auction.objects.filter(artwork=artwork, is_cancelled=False, is_settled=False, ends_at__gt=timezone.now()).exists():
            raise serializers.ValidationError({"artwork_id": "This artwork already has an open auction."})
        if attrs["ends_at"] <= attrs["starts_at"]:
            raise serializers.ValidationError({"ends_at": "End must be after start."})
        if attrs["ends_at"] <= timezone.now():
            raise serializers.ValidationError({"ends_at": "End must be in the future."})
        if attrs.get("reserve_price") is not None and attrs["reserve_price"] < attrs["starting_price"]:
            raise serializers.ValidationError({"reserve_price": "Reserve cannot be below the starting price."})
        if attrs.get("min_increment", 1) < 1:
            raise serializers.ValidationError({"min_increment": "Must be at least ৳1."})
        return attrs
