from django.db import transaction
from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer
from apps.core.fields import AbsoluteImageField

from .models import Artwork, ArtworkImage, Exhibition, ExhibitionItem


class ArtworkImageSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()

    class Meta:
        model = ArtworkImage
        fields = ("id", "image", "caption", "order")


class ArtworkListSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()
    artist = UserMiniSerializer(read_only=True)
    batch_slug = serializers.CharField(source="batch.slug", read_only=True)

    class Meta:
        model = Artwork
        fields = ("id", "title", "image", "medium", "year", "price_bdt", "sale_status", "is_published",
                  "artist", "batch_slug", "created_at")


class ArtworkSerializer(ArtworkListSerializer):
    extra_images = ArtworkImageSerializer(many=True, read_only=True)
    batch_name = serializers.CharField(source="batch.name", read_only=True)
    live_auction_id = serializers.SerializerMethodField()

    class Meta(ArtworkListSerializer.Meta):
        fields = ArtworkListSerializer.Meta.fields + (
            "description", "width_cm", "height_cm", "extra_images", "batch_name", "live_auction_id", "updated_at",
        )
        read_only_fields = ("sale_status",)

    def get_live_auction_id(self, obj):
        a = obj.auctions.filter(is_cancelled=False, is_settled=False).order_by("-starts_at").first()
        return a.id if a and a.phase in ("live", "scheduled") else None


class ArtworkWriteSerializer(ArtworkSerializer):
    """Artists can toggle between not_for_sale and available; reserved/sold are set by orders."""

    image = AbsoluteImageField(required=False)
    # Explicit defaults: multipart forms would otherwise turn a missing boolean into False.
    is_published = serializers.BooleanField(default=True)
    for_sale = serializers.BooleanField(write_only=True, required=False)

    class Meta(ArtworkSerializer.Meta):
        fields = ArtworkSerializer.Meta.fields + ("for_sale",)

    def validate(self, attrs):
        if self.instance is None and not attrs.get("image"):
            raise serializers.ValidationError({"image": "A photo of the artwork is required."})
        for_sale = attrs.pop("for_sale", None)
        if for_sale is not None:
            current = getattr(self.instance, "sale_status", Artwork.SaleStatus.NOT_FOR_SALE)
            if current in (Artwork.SaleStatus.RESERVED, Artwork.SaleStatus.SOLD):
                raise serializers.ValidationError({"for_sale": "This artwork is reserved or sold."})
            price = attrs.get("price_bdt", getattr(self.instance, "price_bdt", None))
            if for_sale and not price:
                raise serializers.ValidationError({"price_bdt": "Set a price to put this artwork up for sale."})
            attrs["sale_status"] = Artwork.SaleStatus.AVAILABLE if for_sale else Artwork.SaleStatus.NOT_FOR_SALE
        return attrs


class ExhibitionSerializer(serializers.ModelSerializer):
    cover = AbsoluteImageField(required=False, allow_null=True)
    is_published = serializers.BooleanField(default=True)
    phase = serializers.CharField(read_only=True)
    created_by = UserMiniSerializer(read_only=True)
    batch_name = serializers.CharField(source="batch.name", read_only=True)
    batch_slug = serializers.CharField(source="batch.slug", read_only=True)
    artwork_count = serializers.SerializerMethodField()
    cover_fallback = serializers.SerializerMethodField()

    class Meta:
        model = Exhibition
        fields = ("id", "title", "description", "cover", "cover_fallback", "venue", "starts_at", "ends_at",
                  "is_published", "phase", "created_by", "batch_name", "batch_slug", "artwork_count")

    def get_artwork_count(self, obj):
        return obj.items.count()

    def get_cover_fallback(self, obj):
        if obj.cover:
            return None
        first = obj.items.select_related("artwork").first()
        return first.artwork.image.url if first and first.artwork.image else None

    def validate(self, attrs):
        s = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        e = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if s and e and e <= s:
            raise serializers.ValidationError({"ends_at": "End must be after start."})
        return attrs


class ExhibitionDetailSerializer(ExhibitionSerializer):
    artworks = serializers.SerializerMethodField()
    artwork_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta(ExhibitionSerializer.Meta):
        fields = ExhibitionSerializer.Meta.fields + ("artworks", "artwork_ids")

    def get_artworks(self, obj):
        items = obj.items.select_related("artwork__artist", "artwork__batch")
        request = self.context.get("request")
        me = request.user if request else None
        arts = [i.artwork for i in items if i.artwork.is_published or (me and i.artwork.artist_id == me.id)]
        return ArtworkListSerializer(arts, many=True, context=self.context).data

    def validate_artwork_ids(self, ids):
        batch = self.context["request"].user.batch
        valid = set(Artwork.objects.filter(batch=batch, id__in=ids).values_list("id", flat=True))
        bad = [i for i in ids if i not in valid]
        if bad:
            raise serializers.ValidationError(f"Artworks not in your group: {bad}")
        return list(dict.fromkeys(ids))

    @transaction.atomic
    def save(self, **kwargs):
        ids = self.validated_data.pop("artwork_ids", None)
        exhibition = super().save(**kwargs)
        if ids is not None:
            exhibition.items.all().delete()
            ExhibitionItem.objects.bulk_create(
                [ExhibitionItem(exhibition=exhibition, artwork_id=a, order=i) for i, a in enumerate(ids)]
            )
        return exhibition
