from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.images import shrink_image_field


class Artwork(models.Model):
    class SaleStatus(models.TextChoices):
        NOT_FOR_SALE = "not_for_sale", "Not for sale"
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"

    batch = models.ForeignKey("batches.Batch", on_delete=models.CASCADE, related_name="artworks")
    artist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="artworks")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    medium = models.CharField(max_length=120, blank=True, help_text="e.g. Oil on canvas")
    width_cm = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="artworks/")
    price_bdt = models.PositiveIntegerField(null=True, blank=True)
    sale_status = models.CharField(max_length=16, choices=SaleStatus.choices, default=SaleStatus.NOT_FOR_SALE)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        shrink_image_field(self.image)
        super().save(*args, **kwargs)


class ArtworkImage(models.Model):
    """Extra photos of an artwork (details, back side, in-situ)."""

    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE, related_name="extra_images")
    image = models.ImageField(upload_to="artworks/extra/")
    caption = models.CharField(max_length=160, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def save(self, *args, **kwargs):
        shrink_image_field(self.image)
        super().save(*args, **kwargs)


class Exhibition(models.Model):
    batch = models.ForeignKey("batches.Batch", on_delete=models.CASCADE, related_name="exhibitions")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="exhibitions/", blank=True)
    venue = models.CharField(max_length=200, blank=True, help_text="Leave empty for online-only")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    artworks = models.ManyToManyField(Artwork, through="ExhibitionItem", related_name="exhibitions", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-starts_at",)

    def __str__(self):
        return self.title

    @property
    def phase(self):
        now = timezone.now()
        if now < self.starts_at:
            return "upcoming"
        if now > self.ends_at:
            return "past"
        return "ongoing"

    def save(self, *args, **kwargs):
        shrink_image_field(self.cover)
        super().save(*args, **kwargs)


class ExhibitionItem(models.Model):
    exhibition = models.ForeignKey(Exhibition, on_delete=models.CASCADE, related_name="items")
    artwork = models.ForeignKey(Artwork, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        unique_together = ("exhibition", "artwork")
