from django.contrib import admin

from .models import Artwork, ArtworkImage, Exhibition, ExhibitionItem


class ArtworkImageInline(admin.TabularInline):
    model = ArtworkImage
    extra = 0


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ("title", "artist", "batch", "price_bdt", "sale_status", "is_published", "created_at")
    list_filter = ("sale_status", "is_published", "batch")
    search_fields = ("title", "artist__username", "artist__display_name")
    inlines = [ArtworkImageInline]


class ExhibitionItemInline(admin.TabularInline):
    model = ExhibitionItem
    extra = 0
    raw_id_fields = ("artwork",)


@admin.register(Exhibition)
class ExhibitionAdmin(admin.ModelAdmin):
    list_display = ("title", "batch", "starts_at", "ends_at", "is_published")
    list_filter = ("is_published", "batch")
    inlines = [ExhibitionItemInline]
